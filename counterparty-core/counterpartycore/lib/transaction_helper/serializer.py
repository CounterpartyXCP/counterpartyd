"""
Construct and serialize the Bitcoin transactions that are Counterparty transactions.

This module contains no consensus‐critical code.
"""

import binascii
import decimal
import hashlib
import logging

import bitcoin as bitcoinlib
from bitcoin.bech32 import CBech32Data

from counterpartycore.lib import arc4, backend, config, exceptions, script, util  # noqa: F401
from counterpartycore.lib.transaction_helper import p2sh_encoding

logger = logging.getLogger(config.LOGGER_NAME)

# Constants
OP_RETURN = b"\x6a"
OP_PUSHDATA1 = b"\x4c"
OP_DUP = b"\x76"
OP_HASH160 = b"\xa9"
OP_EQUALVERIFY = b"\x88"
OP_CHECKSIG = b"\xac"
OP_0 = b"\x00"
OP_1 = b"\x51"
OP_2 = b"\x52"
OP_3 = b"\x53"
OP_CHECKMULTISIG = b"\xae"
OP_EQUAL = b"\x87"

D = decimal.Decimal
UTXO_LOCKS = None
UTXO_LOCKS_PER_ADDRESS_MAXSIZE = 5000  # set higher than the max number of UTXOs we should expect to
# manage in an aging cache for any one source address, at any one period


def var_int(i):
    if i < 0xFD:
        return (i).to_bytes(1, byteorder="little")
    elif i <= 0xFFFF:
        return b"\xfd" + (i).to_bytes(2, byteorder="little")
    elif i <= 0xFFFFFFFF:
        return b"\xfe" + (i).to_bytes(4, byteorder="little")
    else:
        return b"\xff" + (i).to_bytes(8, byteorder="little")


def op_push(i):
    if i < 0x4C:
        return (i).to_bytes(1, byteorder="little")  # Push i bytes.
    elif i <= 0xFF:
        return b"\x4c" + (i).to_bytes(1, byteorder="little")  # OP_PUSHDATA1
    elif i <= 0xFFFF:
        return b"\x4d" + (i).to_bytes(2, byteorder="little")  # OP_PUSHDATA2
    else:
        return b"\x4e" + (i).to_bytes(4, byteorder="little")  # OP_PUSHDATA4


def get_script(address):
    if script.is_multisig(address):
        return get_multisig_script(address)
    elif script.is_bech32(address):
        return get_p2w_script(address)
    else:
        try:
            return get_monosig_script(address)
        except script.VersionByteError as e:  # noqa: F841
            return get_p2sh_script(address)


def get_multisig_script(address):
    # Unpack multi‐sig address.
    signatures_required, pubkeys, signatures_possible = script.extract_array(address)

    # Required signatures.
    if signatures_required == 1:
        op_required = OP_1
    elif signatures_required == 2:
        op_required = OP_2
    elif signatures_required == 3:
        op_required = OP_3
    else:
        raise script.InputError("Required signatures must be 1, 2 or 3.")

    # Required signatures.
    # Note 1-of-1 addresses are not supported (they don't go through extract_array anyway).
    if signatures_possible == 2:
        op_total = OP_2
    elif signatures_possible == 3:
        op_total = OP_3
    else:
        raise script.InputError("Total possible signatures must be 2 or 3.")

    # Construct script.
    tx_script = op_required  # Required signatures
    for public_key in pubkeys:
        public_key = binascii.unhexlify(public_key)  # noqa: PLW2901
        tx_script += op_push(len(public_key))  # Push bytes of public key
        tx_script += public_key  # Data chunk (fake) public key
    tx_script += op_total  # Total signatures
    tx_script += OP_CHECKMULTISIG  # OP_CHECKMULTISIG

    return (tx_script, None)


def get_monosig_script(address):
    # Construct script.
    pubkeyhash = script.base58_check_decode(address, config.ADDRESSVERSION)
    tx_script = OP_DUP  # OP_DUP
    tx_script += OP_HASH160  # OP_HASH160
    tx_script += op_push(20)  # Push 0x14 bytes
    tx_script += pubkeyhash  # pubKeyHash
    tx_script += OP_EQUALVERIFY  # OP_EQUALVERIFY
    tx_script += OP_CHECKSIG  # OP_CHECKSIG

    return (tx_script, None)


def get_p2sh_script(address):
    # Construct script.
    scripthash = script.base58_check_decode(address, config.P2SH_ADDRESSVERSION)
    tx_script = OP_HASH160
    tx_script += op_push(len(scripthash))
    tx_script += scripthash
    tx_script += OP_EQUAL

    return (tx_script, None)


def get_p2w_script(address):
    # Construct script.
    scripthash = bytes(CBech32Data(address))

    if len(scripthash) == 20:
        # P2WPKH encoding

        tx_script = OP_0
        tx_script += b"\x14"
        tx_script += scripthash

        witness_script = OP_HASH160
        witness_script += op_push(len(scripthash))
        witness_script += scripthash
        witness_script += OP_EQUAL

        return (tx_script, witness_script)
    elif len(scripthash) == 32:
        # P2WSH encoding
        raise Exception("P2WSH encoding not yet supported")


def make_fully_valid(pubkey_start):
    """Take a too short data pubkey and make it look like a real pubkey.

    Take an obfuscated chunk of data that is two bytes too short to be a pubkey and
    add a sign byte to its beginning and a nonce byte to its end. Choose these
    bytes so that the resulting sequence of bytes is a fully valid pubkey (i.e. on
    the ECDSA curve). Find the correct bytes by guessing randomly until the check
    passes. (In parsing, these two bytes are ignored.)
    """
    assert type(pubkey_start) == bytes  # noqa: E721
    assert len(pubkey_start) == 31  # One sign byte and one nonce byte required (for 33 bytes).

    random_bytes = hashlib.sha256(
        pubkey_start
    ).digest()  # Deterministically generated, for unit tests.
    sign = (random_bytes[0] & 0b1) + 2  # 0x02 or 0x03
    nonce = initial_nonce = random_bytes[1]

    pubkey = b""
    while not script.is_fully_valid(pubkey):
        # Increment nonce.
        nonce += 1
        assert nonce != initial_nonce

        # Construct a possibly fully valid public key.
        pubkey = bytes([sign]) + pubkey_start + bytes([nonce % 256])

    assert len(pubkey) == 33
    return pubkey


def serialise(
    encoding,
    inputs,
    destination_outputs,
    block_index,
    data_output=None,
    change_output=None,
    dust_return_pubkey=None,
):
    s = (1).to_bytes(4, byteorder="little")  # Version

    use_segwit = False
    for i in range(len(inputs)):
        txin = inputs[i]
        spk = txin["script_pub_key"]
        if spk[0:2] == "00":  # Witness version 0
            datalen = binascii.unhexlify(spk[2:4])[0]
            if datalen == 20 or datalen == 32:
                # 20 is for P2WPKH and 32 is for P2WSH
                if not (use_segwit):
                    s = (2).to_bytes(4, byteorder="little")  # Rewrite version
                    use_segwit = True

                txin["is_segwit"] = True

    if use_segwit:
        s += b"\x00"  # marker
        s += b"\x01"  # flag

    # Number of inputs.
    s += var_int(int(len(inputs)))

    witness_txins = []  # noqa: F841
    witness_data = {}  # noqa: F841

    # List of Inputs.
    for i in range(len(inputs)):
        txin = inputs[i]
        s += binascii.unhexlify(bytes(txin["txid"], "utf-8"))[::-1]  # TxOutHash
        s += txin["vout"].to_bytes(4, byteorder="little")  # TxOutIndex

        tx_script = binascii.unhexlify(bytes(txin["script_pub_key"], "utf-8"))
        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script  # Script
        s += b"\xff" * 4  # Sequence

    # Number of outputs.
    n = 0
    n += len(destination_outputs)
    if data_output:
        data_array, value = data_output
        for data_chunk in data_array:  # noqa: B007
            n += 1
    else:
        data_array = []
    if change_output:
        n += 1
    s += var_int(n)

    # Destination output.
    for destination, value in destination_outputs:
        s += value.to_bytes(8, byteorder="little")  # Value

        tx_script, witness_script = get_script(destination)
        # if use_segwit and destination in witness_data: # Not deleteing, We will need this for P2WSH
        #    witness_data[destination].append(witness_script)
        #    tx_script = witness_script

        # if witness_script:
        #    tx_script = witness_script

        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script

    # Data output.
    for data_chunk in data_array:
        data_array, value = data_output
        s += value.to_bytes(8, byteorder="little")  # Value

        data_chunk = util.prefix(block_index) + data_chunk  # noqa: PLW2901

        # Initialise encryption key (once per output).
        assert isinstance(inputs[0]["txid"], str)
        key = arc4.init_arc4(
            binascii.unhexlify(inputs[0]["txid"])
        )  # Arbitrary, easy‐to‐find, unique key.

        if encoding == "multisig":
            assert dust_return_pubkey
            # Get data (fake) public key.
            pad_length = (33 * 2) - 1 - 2 - 2 - len(data_chunk)
            assert pad_length >= 0
            data_chunk = bytes([len(data_chunk)]) + data_chunk + (pad_length * b"\x00")  # noqa: PLW2901
            data_chunk = key.encrypt(data_chunk)  # noqa: PLW2901
            data_pubkey_1 = make_fully_valid(data_chunk[:31])
            data_pubkey_2 = make_fully_valid(data_chunk[31:])

            # Construct script.
            tx_script = OP_1  # OP_1
            tx_script += op_push(33)  # Push bytes of data chunk (fake) public key    (1/2)
            tx_script += data_pubkey_1  # (Fake) public key                  (1/2)
            tx_script += op_push(33)  # Push bytes of data chunk (fake) public key    (2/2)
            tx_script += data_pubkey_2  # (Fake) public key                  (2/2)
            tx_script += op_push(len(dust_return_pubkey))  # Push bytes of source public key
            tx_script += dust_return_pubkey  # Source public key
            tx_script += OP_3  # OP_3
            tx_script += OP_CHECKMULTISIG  # OP_CHECKMULTISIG
        elif encoding == "opreturn":
            data_chunk = key.encrypt(data_chunk)  # noqa: PLW2901
            tx_script = OP_RETURN  # OP_RETURN
            tx_script += op_push(len(data_chunk))  # Push bytes of data chunk (NOTE: OP_SMALLDATA?)
            tx_script += data_chunk  # Data
        elif encoding == "pubkeyhash":
            pad_length = 20 - 1 - len(data_chunk)
            assert pad_length >= 0
            data_chunk = bytes([len(data_chunk)]) + data_chunk + (pad_length * b"\x00")  # noqa: PLW2901
            data_chunk = key.encrypt(data_chunk)  # noqa: PLW2901
            # Construct script.
            tx_script = OP_DUP  # OP_DUP
            tx_script += OP_HASH160  # OP_HASH160
            tx_script += op_push(20)  # Push 0x14 bytes
            tx_script += data_chunk  # (Fake) pubKeyHash
            tx_script += OP_EQUALVERIFY  # OP_EQUALVERIFY
            tx_script += OP_CHECKSIG  # OP_CHECKSIG
        else:
            raise exceptions.TransactionError("Unknown encoding‐scheme.")

        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script

    # Change output.
    if change_output:
        change_address, change_value = change_output
        s += change_value.to_bytes(8, byteorder="little")  # Value

        tx_script, witness_script = get_script(change_address)
        # print("Change address!", change_address, "\n", witness_data, "\n", tx_script, "\n", witness_script)
        # if witness_script: #use_segwit and change_address in witness_data:
        #    if not(change_address in witness_data):
        #        witness_data[change_address] = []
        #    witness_data[change_address].append(witness_script)
        #    tx_script = witness_script
        #    use_segwit = True

        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script

    if use_segwit:
        for i in range(len(inputs)):
            txin = inputs[i]
            if txin["is_segwit"]:
                s += b"\x02"
                s += b"\x00\x00"
            else:
                s += b"\x00"

    s += (0).to_bytes(4, byteorder="little")  # LockTime
    return s


def serialise_p2sh_pretx(
    inputs,
    source,
    source_value,
    data_output,
    block_index,
    change_output=None,
    pubkey=None,
    multisig_pubkeys=None,
    multisig_pubkeys_required=None,
):
    assert data_output  # we don't do this unless there's data

    data_array, data_value = data_output

    s = (1).to_bytes(4, byteorder="little")  # Version

    # Number of inputs.
    s += var_int(int(len(inputs)))

    # List of Inputs.
    for i in range(len(inputs)):
        txin = inputs[i]
        s += binascii.unhexlify(bytes(txin["txid"], "utf-8"))[::-1]  # TxOutHash
        s += txin["vout"].to_bytes(4, byteorder="little")  # TxOutIndex

        tx_script = binascii.unhexlify(bytes(txin["script_pub_key"], "utf-8"))
        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script  # Script
        s += b"\xff" * 4  # Sequence

    # Number of outputs.
    n = len(data_array)
    if change_output:
        n += 1

    # encode number of outputs
    s += var_int(n)

    # P2SH for data encodeded inputs
    for n, data_chunk in enumerate(data_array):
        data_chunk = util.prefix(block_index) + data_chunk  # prefix the data_chunk  # noqa: PLW2901

        # get the scripts
        script_sig, redeem_script, output_script = p2sh_encoding.make_p2sh_encoding_redeemscript(
            data_chunk, n, pubkey, multisig_pubkeys, multisig_pubkeys_required
        )

        # if data_value is an array, then every output fee is specified in it
        if type(data_value) == list:  # noqa: E721
            s += data_value[n].to_bytes(8, byteorder="little")  # Value
        else:
            s += data_value.to_bytes(8, byteorder="little")  # Value
        s += var_int(int(len(output_script)))  # Script length
        s += output_script  # Script

    # Change output.
    if change_output:
        change_address, change_value = change_output
        tx_script, witness_script = get_script(change_address)

        s += change_value.to_bytes(8, byteorder="little")  # Value
        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script  # Script

    s += (0).to_bytes(4, byteorder="little")  # LockTime

    return s


def serialise_p2sh_datatx(
    txid,
    source,
    source_input,
    destination_outputs,
    data_output,
    block_index,
    pubkey=None,
    multisig_pubkeys=None,
    multisig_pubkeys_required=None,
):
    assert data_output  # we don't do this unless there's data

    txhash = bitcoinlib.core.lx(bitcoinlib.core.b2x(txid))  # reverse txId
    data_array, value = data_output

    # version
    s = (1).to_bytes(4, byteorder="little")

    # number of inputs is the length of data_array (+1 if a source_input exists)
    number_of_inputs = len(data_array)
    if source_input is not None:
        number_of_inputs += 1
    s += var_int(number_of_inputs)

    # Handle a source input here for a P2SH source
    if source_input is not None:
        s += binascii.unhexlify(bytes(source_input["txid"], "utf-8"))[::-1]  # TxOutHash
        s += source_input["vout"].to_bytes(4, byteorder="little")  # TxOutIndex

        # since pubkey is not returned from indexd, add it from bitcoind
        source_inputs = script.ensure_script_pub_key_for_inputs([source_input])
        source_input = source_inputs[0]
        tx_script = binascii.unhexlify(bytes(source_input["script_pub_key"], "utf-8"))
        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script  # Script
        s += b"\xff" * 4  # Sequence

    # list of inputs
    for n, data_chunk in enumerate(data_array):
        data_chunk = util.prefix(block_index) + data_chunk  # prefix the data_chunk  # noqa: PLW2901

        # get the scripts
        script_sig, redeem_script, output_script = p2sh_encoding.make_p2sh_encoding_redeemscript(
            data_chunk, n, pubkey, multisig_pubkeys, multisig_pubkeys_required
        )
        # substituteScript = script_sig + output_script

        s += txhash  # TxOutHash
        s += (n).to_bytes(4, byteorder="little")  # TxOutIndex (assumes 0-based)

        # s += var_int(len(substituteScript))                      # Script length
        # s += substituteScript                                    # Script

        s += var_int(len(script_sig))  # + len(output_script))                      # Script length
        s += script_sig  # Script
        # s += output_script                                    # Script

        s += b"\xff" * 4  # Sequence

    # number of outputs, always 1 for the opreturn
    n = 1
    n += len(destination_outputs)

    # encode output length
    s += var_int(n)

    # destination outputs
    for destination, value in destination_outputs:
        tx_script, witness_script = get_script(destination)

        s += value.to_bytes(8, byteorder="little")  # Value
        s += var_int(int(len(tx_script)))  # Script length
        s += tx_script  # Script

    # opreturn to signal P2SH encoding
    key = arc4.init_arc4(txid)
    data_chunk = util.prefix(block_index) + b"P2SH"
    data_chunk = key.encrypt(data_chunk)
    tx_script = OP_RETURN  # OP_RETURN
    tx_script += op_push(len(data_chunk))  # Push bytes of data chunk
    tx_script += data_chunk  # Data

    # add opreturn
    s += (0).to_bytes(8, byteorder="little")  # Value
    s += var_int(int(len(tx_script)))  # Script length
    s += tx_script  # Script

    s += (0).to_bytes(4, byteorder="little")  # LockTime

    return s
