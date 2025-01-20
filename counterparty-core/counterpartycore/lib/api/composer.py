import binascii
import hashlib
import inspect
import logging
import string
import sys
import time
from collections import OrderedDict
from decimal import Decimal as D

from arc4 import ARC4
from bitcoinutils.keys import P2pkhAddress, P2shAddress, P2wpkhAddress, PublicKey
from bitcoinutils.script import Script, b_to_h
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput

from counterpartycore.lib import (
    backend,
    config,
    exceptions,
    ledger,
)
from counterpartycore.lib.parser import deserialize, utxosinfo
from counterpartycore.lib.utils import helpers, multisig, opcodes, script

MAX_INPUTS_SET = 100

logger = logging.getLogger(config.LOGGER_NAME)


def get_output_type(script_pub_key):
    asm = script.script_to_asm(script_pub_key)
    if asm[0] == opcodes.OP_RETURN:
        return "OP_RETURN"
    if len(asm) == 2 and asm[1] == opcodes.OP_CHECKSIG:
        return "P2PK"
    if (
        len(asm) == 5
        and asm[0] == opcodes.OP_DUP
        and asm[3] == opcodes.OP_EQUALVERIFY
        and asm[4] == opcodes.OP_CHECKSIG
    ):
        return "P2PKH"
    if len(asm) >= 4 and asm[-1] == opcodes.OP_CHECKMULTISIG and asm[-2] == len(asm) - 3:
        return "P2MS"
    if len(asm) == 3 and asm[0] == opcodes.OP_HASH160 and asm[2] == opcodes.OP_EQUAL:
        return "P2SH"
    if len(asm) == 2 and asm[0] == b"":
        if len(asm[1]) == 32:
            return "P2WSH"
        return "P2WPKH"
    if len(asm) == 2 and asm[0] == b"\x01":
        return "P2TR"
    return "UNKNOWN"


def is_segwit_output(script_pub_key):
    return get_output_type(script_pub_key) in ("P2WPKH", "P2WSH", "P2TR")


def is_address_script(address, script_pub_key):
    if multisig.is_multisig(address):
        asm = script.script_to_asm(script_pub_key)
        pubkeys = [binascii.hexlify(pubkey).decode("utf-8") for pubkey in asm[1:-2]]
        addresses = [
            PublicKey.from_hex(pubkey).get_address(compressed=True).to_string()
            for pubkey in pubkeys
        ]
        script_address = f"{asm[0]}_{'_'.join(addresses)}_{asm[-2]}"
    else:
        script_address = script.script_to_address2(script_pub_key)
    return address == script_address


################
#   Outputs    #
################


def address_to_script_pub_key(address, unspent_list, construct_params):
    helpers.setup_bitcoinutils()
    if multisig.is_multisig(address):
        signatures_required, addresses, signatures_possible = multisig.extract_array(address)
        pubkeys = [search_pubkey(addr, unspent_list, construct_params) for addr in addresses]
        if None in pubkeys:
            raise exceptions.ComposeError(
                f"Pubkeys not found for {address}, please provide them with the `pubkeys` parameter"
            )
        multisig_script = Script(
            [signatures_required] + pubkeys + [signatures_possible] + ["OP_CHECKMULTISIG"]
        )
        return multisig_script
    try:
        return P2wpkhAddress(address).to_script_pub_key()
    except ValueError:
        pass
    try:
        return P2pkhAddress(address).to_script_pub_key()
    except ValueError:
        pass
    try:
        return P2shAddress(address).to_script_pub_key()
    except ValueError as e:
        raise exceptions.ComposeError(f"Invalid address: {address}") from e


def create_tx_output(value, address_or_script, unspent_list, construct_params):
    try:
        # if hex string we assume it is a script
        if all(c in string.hexdigits for c in address_or_script):
            has_segwit = is_segwit_output(address_or_script)
            # check if it is a valid script
            output_script = Script.from_raw(address_or_script, has_segwit=has_segwit)
        else:
            output_script = address_to_script_pub_key(
                address_or_script, unspent_list, construct_params
            )
    except Exception as e:
        raise exceptions.ComposeError(
            f"Invalid script or address for output: {address_or_script} (error: {e})"
        ) from e

    return TxOutput(value, output_script)


def regular_dust_size(construct_params):
    if construct_params.get("regular_dust_size") is not None:
        return construct_params["regular_dust_size"]
    return config.DEFAULT_REGULAR_DUST_SIZE


def multisig_dust_size(construct_params):
    if construct_params.get("multisig_dust_size") is not None:
        return construct_params["multisig_dust_size"]
    return config.DEFAULT_MULTISIG_DUST_SIZE


def dust_size(address, construct_params):
    if multisig.is_multisig(address):
        return multisig_dust_size(construct_params)
    return regular_dust_size(construct_params)


def perpare_non_data_outputs(destinations, unspent_list, construct_params):
    outputs = []
    for address, value in destinations:
        output_value = value or dust_size(address, construct_params)
        outputs.append(create_tx_output(output_value, address, unspent_list, construct_params))
    return outputs


def determine_encoding(data, construct_params):
    desired_encoding = construct_params.get("encoding", "auto")
    if desired_encoding == "auto":
        if len(data) + len(config.PREFIX) <= config.OP_RETURN_MAX_SIZE:
            encoding = "opreturn"
        else:
            encoding = "multisig"
    else:
        encoding = desired_encoding
    if encoding not in ("multisig", "opreturn"):
        raise exceptions.ComposeError(f"Not supported encoding: {encoding}")
    return encoding


def encrypt_data(data, arc4_key):
    key = binascii.unhexlify(arc4_key)
    return ARC4(key).encrypt(data)


def prepare_opreturn_output(data, arc4_key):
    if len(data) + len(config.PREFIX) > config.OP_RETURN_MAX_SIZE:
        raise exceptions.ComposeError("One `OP_RETURN` output per transaction")
    opreturn_data = config.PREFIX + data
    opreturn_data = encrypt_data(opreturn_data, arc4_key)
    return [TxOutput(0, Script(["OP_RETURN", b_to_h(opreturn_data)]))]


def is_valid_pubkey(pubkey):
    try:
        PublicKey.from_hex(pubkey).get_address(compressed=True).to_string()
        return True
    except Exception:
        return False


def search_pubkey(source, unspent_list, construct_params):
    # search in provided pubkeys
    if construct_params is not None:
        pubkeys = construct_params.get("pubkeys")
        if pubkeys is not None:
            pubkeys = pubkeys.split(",")
        else:
            pubkeys = []
        if len(pubkeys) > 0:
            for pubkey in pubkeys:
                if PublicKey.from_hex(pubkey).get_address(compressed=True).to_string() == source:
                    return pubkey
    # then search with Bitcoin Core or Electrs
    tx_hashes = [utxo["txid"] for utxo in unspent_list]
    return backend.search_pubkey(source, tx_hashes)


def make_valid_pubkey(pubkey_start):
    """Take a too short data pubkey and make it look like a real pubkey.

    Take an obfuscated chunk of data that is two bytes too short to be a pubkey and
    add a sign byte to its beginning and a nonce byte to its end. Choose these
    bytes so that the resulting sequence of bytes is a fully valid pubkey (i.e. on
    the ECDSA curve). Find the correct bytes by guessing randomly until the check
    passes. (In parsing, these two bytes are ignored.)
    """
    assert isinstance(pubkey_start, bytes)  # noqa: E721
    assert len(pubkey_start) == 31  # One sign byte and one nonce byte required (for 33 bytes).

    random_bytes = hashlib.sha256(
        pubkey_start
    ).digest()  # Deterministically generated, for unit tests.
    sign = (random_bytes[0] & 0b1) + 2  # 0x02 or 0x03
    nonce = initial_nonce = random_bytes[1]

    pubkey = b""
    while not is_valid_pubkey(binascii.hexlify(pubkey).decode("utf-8")):
        # Increment nonce.
        nonce += 1
        assert nonce != initial_nonce

        # Construct a possibly fully valid public key.
        pubkey = bytes([sign]) + pubkey_start + bytes([nonce % 256])

    assert len(pubkey) == 33
    return pubkey


def data_to_pubkey_pairs(data, arc4_key):
    # Two pubkeys, minus length byte, minus prefix, minus two nonces,
    # minus two sign bytes.
    chunk_size = (33 * 2) - 1 - len(config.PREFIX) - 2 - 2
    data_array = helpers.chunkify(data, chunk_size)
    pubkey_pairs = []
    for data_part in data_array:
        # Get data (fake) public key.
        data_chunk = config.PREFIX + data_part
        pad_length = (33 * 2) - 1 - 2 - 2 - len(data_chunk)
        assert pad_length >= 0
        output_data = bytes([len(data_chunk)]) + data_chunk + (pad_length * b"\x00")  # noqa: PLW2901
        output_data = encrypt_data(output_data, arc4_key)
        data_pubkey_1 = make_valid_pubkey(output_data[:31])
        data_pubkey_2 = make_valid_pubkey(output_data[31:])
        pubkey_pairs.append((b_to_h(data_pubkey_1), b_to_h(data_pubkey_2)))
    return pubkey_pairs


def prepare_multisig_output(source, data, arc4_key, unspent_list, construct_params):
    # determine multisig pubkey
    multisig_pubkey = construct_params.get("multisig_pubkey")
    if multisig_pubkey is None:
        multisig_pubkey = search_pubkey(source, unspent_list, construct_params)
    if multisig_pubkey is None:
        raise exceptions.ComposeError(
            f"Pubkey not found for {source}, please provide it with the `multisig_pubkey` parameter"
        )
    elif not is_valid_pubkey(multisig_pubkey):
        raise exceptions.ComposeError(f"Invalid multisig pubkey: {multisig_pubkey}")
    # generate pubkey pairs from data
    pubkey_pairs = data_to_pubkey_pairs(data, arc4_key)
    outputs = []
    for pubkey_pair in pubkey_pairs:
        output_script = Script(
            [1, pubkey_pair[0], pubkey_pair[1], multisig_pubkey, 3, "OP_CHECKMULTISIG"]
        )
        outputs.append(TxOutput(multisig_dust_size(construct_params), output_script))
    return outputs


def prepare_data_outputs(source, data, unspent_list, construct_params):
    encoding = determine_encoding(data, construct_params)
    arc4_key = unspent_list[0]["txid"]
    if encoding == "multisig":
        return prepare_multisig_output(source, data, arc4_key, unspent_list, construct_params)
    if encoding == "opreturn":
        return prepare_opreturn_output(data, arc4_key)
    raise exceptions.ComposeError(f"Not supported encoding: {encoding}")


def prepare_more_outputs(more_outputs, unspent_list, construct_params):
    output_list = [output.split(":") for output in more_outputs.split(",")]
    outputs = []
    for output in output_list:
        if len(output) != 2:
            raise exceptions.ComposeError(f"Invalid output format: {':'.join(output)}")
        value, address_or_script = output
        # check value
        try:
            value = int(value)
        except ValueError as e:
            raise exceptions.ComposeError(f"Invalid value for output: {':'.join(output)}") from e
        # create output
        tx_output = create_tx_output(value, address_or_script, unspent_list, construct_params)
        outputs.append(tx_output)
    return outputs


def prepare_outputs(source, destinations, data, unspent_list, construct_params):
    # prepare non-data outputs
    outputs = perpare_non_data_outputs(destinations, unspent_list, construct_params)
    # prepare data outputs
    if data:
        outputs += prepare_data_outputs(source, data, unspent_list, construct_params)
    # Add more outputs if needed
    more_outputs = construct_params.get("more_outputs")
    if more_outputs:
        outputs += prepare_more_outputs(more_outputs, unspent_list, construct_params)
    return outputs


################
#   Inputs     #
################


class UTXOLocks(metaclass=helpers.SingletonMeta):
    def __init__(self):
        self.init()

    def init(self):
        self.locks = OrderedDict()
        self.locks = OrderedDict()
        self.set_limits(config.UTXO_LOCKS_MAX_AGE, config.UTXO_LOCKS_MAX_ADDRESSES)

    def set_limits(self, max_age, max_size):
        self.max_age = max_age
        self.max_size = max_size

    def lock(self, utxo):
        self.locks[utxo] = time.time()
        if len(self.locks) > self.max_size:
            self.locks.popitem(last=False)

    def locked(self, utxo):
        if utxo not in self.locks:
            return False
        if time.time() - self.locks[utxo] > self.max_age:
            del self.locks[utxo]
            return False
        return True

    def filter_unspent_list(self, unspent_list):
        return [utxo for utxo in unspent_list if not self.locked(f"{utxo['txid']}:{utxo['vout']}")]

    def lock_inputs(self, inputs):
        for tx_input in inputs:
            self.lock(f"{tx_input.txid}:{tx_input.txout_index}")


def complete_unspent_list(unspent_list):
    # gather tx hashes with missing data
    txhash_set = set()
    for utxo in unspent_list:
        if "script_pub_key" not in utxo or "value" not in utxo:
            txhash_set.add(utxo["txid"])

    # get missing data from Bitcoin Core
    if len(txhash_set) > 0:
        txhash_list_chunks = helpers.chunkify(list(txhash_set), config.MAX_RPC_BATCH_SIZE)
        txs = {}
        for txhash_list in txhash_list_chunks:
            txs = txs | backend.bitcoind.getrawtransaction_batch(
                txhash_list, verbose=True, return_dict=True
            )

    # complete unspent list with missing data
    completed_unspent_list = []
    for utxo in unspent_list:
        if "script_pub_key" not in utxo or "value" not in utxo:
            txid = utxo["txid"]
            if txid not in txs:
                raise exceptions.ComposeError(
                    f"invalid UTXOs: {txid}:{utxo['vout']} (transaction not found)"
                )
            for vout in txs[txid]["vout"]:
                if vout["n"] == utxo["vout"]:
                    if "script_pub_key" not in utxo:
                        utxo["script_pub_key"] = vout["scriptPubKey"]["hex"]
                    if "value" not in utxo:
                        utxo["value"] = int(vout["value"] * config.UNIT)
                        utxo["amount"] = vout["value"]
        utxo["is_segwit"] = is_segwit_output(utxo["script_pub_key"])
        completed_unspent_list.append(utxo)

    return completed_unspent_list


def prepare_inputs_set(inputs_set):
    unspent_list = []
    utxos_list = inputs_set.split(",")
    if len(utxos_list) > MAX_INPUTS_SET:
        raise exceptions.ComposeError(
            f"too many UTXOs in inputs_set (max. {MAX_INPUTS_SET}): {len(utxos_list)}"
        )
    for utxo in utxos_list:
        utxo_parts = utxo.split(":")

        if len(utxo_parts) == 2:
            txid, vout = utxo.split(":")
            value, script_pub_key = None, None
        elif len(utxo_parts) == 3:
            txid, vout, value = utxo.split(":")
            script_pub_key = None
        elif len(utxo_parts) == 4:
            txid, vout, value, script_pub_key = utxo.split(":")
        else:
            raise exceptions.ComposeError(f"invalid UTXOs: {utxo} (invalid format)")

        if not utxosinfo.is_utxo_format(f"{txid}:{vout}"):
            raise exceptions.ComposeError(f"invalid UTXOs: {utxo} (invalid format)")

        unspent = {
            "txid": txid,
            "vout": int(vout),
        }

        if value is not None:
            try:
                unspent["value"] = int(value)
            except ValueError as e:
                raise exceptions.ComposeError(f"invalid UTXOs: {utxo} (invalid value)") from e

        if script_pub_key is not None:
            try:
                script.script_to_asm(script_pub_key)
            except Exception as e:
                raise exceptions.ComposeError(
                    f"invalid UTXOs: {utxo} (invalid script_pub_key)"
                ) from e
            unspent["script_pub_key"] = script_pub_key

        unspent_list.append(unspent)

    return unspent_list


def utxo_to_address(db, utxo):
    # first try with the database
    sql = "SELECT utxo_address FROM balances WHERE utxo = ? LIMIT 1"
    balance = db.execute(sql, (utxo,)).fetchone()
    if balance:
        return balance["utxo_address"]
    # then try with Bitcoin Core
    txid, vout = utxo.split(":")
    try:
        tx = backend.bitcoind.getrawtransaction(txid, verbose=True)
        vout = int(vout)
        address = tx["vout"][vout]["scriptPubKey"]["address"]
        return address
    except Exception as e:
        raise exceptions.ComposeError(
            f"invalid UTXOs: {utxo} (not found in the database or Bitcoin Core)"
        ) from e


def ensure_utxo_is_first(utxo, unspent_list):
    txid, vout = utxo.split(":")
    vout = int(vout)
    new_unspent_list = []
    for unspent in unspent_list:
        if unspent["txid"] == txid and unspent["vout"] == vout:
            new_unspent_list.insert(0, unspent)
        else:
            new_unspent_list.append(unspent)

    first_utxo = new_unspent_list[0]
    if first_utxo["txid"] != txid or first_utxo["vout"] != vout:
        try:
            value = backend.bitcoind.get_utxo_value(txid, vout)
        except Exception as e:
            raise exceptions.ComposeError(f"invalid UTXOs: {utxo} (value not found)") from e
        new_unspent_list.insert(
            0,
            {
                "txid": txid,
                "vout": vout,
                "value": value,
            },
        )
    return new_unspent_list


def filter_utxos_with_balances(db, source, unspent_list, construct_params):
    use_utxos_with_balances = construct_params.get("use_utxos_with_balances", False)
    if use_utxos_with_balances:
        return unspent_list

    exclude_utxos_with_balances = construct_params.get("exclude_utxos_with_balances", False)
    new_unspent_list = []
    with_balance_utxos = []
    for utxo in unspent_list:
        str_input = f"{utxo['txid']}:{utxo['vout']}"
        if str_input == source:
            new_unspent_list.append(utxo)
            continue
        utxo_balances = ledger.balances.get_utxo_balances(db, str_input)
        with_balances = len(utxo_balances) > 0 and any(
            balance["quantity"] > 0 for balance in utxo_balances
        )
        if exclude_utxos_with_balances and with_balances:
            continue
        if with_balances:
            with_balance_utxos.append(str_input)
            continue
        new_unspent_list.append(utxo)
    if len(with_balance_utxos) > 0:
        raise exceptions.ComposeError(
            f"invalid UTXOs: {', '.join(with_balance_utxos)} (use `use_utxos_with_balances=True` to include them or `exclude_utxos_with_balances=True` to exclude them silently)"
        )
    return new_unspent_list


def prepare_unspent_list(db, source, construct_params):
    inputs_set = construct_params.get("inputs_set")

    if inputs_set is None:
        # get unspent list from Bitcoin Core or Electrs
        allow_unconfirmed_inputs = construct_params.get("allow_unconfirmed_inputs", False)
        if utxosinfo.is_utxo_format(source):
            source_address = utxo_to_address(db, source)
        else:
            source_address = source
        unspent_list = backend.list_unspent(source_address, allow_unconfirmed_inputs)
        # exclude silentely utxos with balances
        unspent_list = filter_utxos_with_balances(
            db, source, unspent_list, construct_params | {"exclude_utxos_with_balances": True}
        )
    else:
        # prepare unspent list provided by the user
        unspent_list = prepare_inputs_set(inputs_set)

    # exclude utxos if explicitly requested
    exclude_utxos = construct_params.get("exclude_utxos")
    if exclude_utxos is not None:
        exclude_utxos_list = exclude_utxos.split(",")
        unspent_list = [
            utxo
            for utxo in unspent_list
            if f"{utxo['txid']}:{utxo['vout']}" not in exclude_utxos_list
        ]

    # include only tx_hash if explicitly requested
    unspent_tx_hash = construct_params.get("unspent_tx_hash")  # legacy
    if unspent_tx_hash is not None:
        unspent_list = [utxo for utxo in unspent_list if utxo["txid"] == unspent_tx_hash]

    # excluded locked utxos
    if not construct_params.get("disable_utxo_locks", False):
        unspent_list = UTXOLocks().filter_unspent_list(unspent_list)

    # exclude utxos with balances if needed
    unspent_list = filter_utxos_with_balances(db, source, unspent_list, construct_params)

    if len(unspent_list) == 0:
        raise exceptions.ComposeError(
            f"No UTXOs found for {source}, provide UTXOs with the `inputs_set` parameter"
        )

    # complete unspent list with missing data (value or script_pub_key)
    # so we can sort it by value
    unspent_list = complete_unspent_list(unspent_list)

    # sort unspent list by value
    unspent_list = sorted(unspent_list, key=lambda x: x["value"], reverse=True)

    # if source is an utxo, ensure it is first in the unspent list
    if utxosinfo.is_utxo_format(source):
        unspent_list = ensure_utxo_is_first(source, unspent_list)
        # complete unspent list again with missing data
        unspent_list = complete_unspent_list(unspent_list)

    return unspent_list


def utxos_to_txins(utxos: list):
    inputs = []
    for utxo in utxos:
        tx_input = TxInput(utxo["txid"], utxo["vout"])
        inputs.append(tx_input)
    return inputs


###################
#   Composition   #
##################

DUMMY_DER_SIG = "3045" + "00" * 70
DUMMY_REEDEM_SCRIPT = DUMMY_DER_SIG
DUMMY_PUBKEY = "03" + 32 * "00"
DUMMY_SCHNORR_SIG = "00" * 65
OP_0 = "00"
OP_PUSHBYTES_72 = "48"
OP_PUSHBYTES_33 = "21"


# dummies script_sig from https://learnmeabitcoin.com/technical/script/
def get_dummy_script_sig(script_pub_key):
    output_type = get_output_type(script_pub_key)
    script_sig = None
    if output_type == "P2PK":
        script_sig = OP_PUSHBYTES_72 + DUMMY_DER_SIG
    elif output_type == "P2PKH":
        script_sig = OP_PUSHBYTES_72 + DUMMY_DER_SIG + OP_PUSHBYTES_33 + DUMMY_PUBKEY
    elif output_type == "P2MS":
        asm = script.script_to_asm(script_pub_key)
        required_signatures = asm[0]
        script_sig = OP_0 + (required_signatures * DUMMY_DER_SIG)
    elif output_type == "P2SH":
        script_sig = OP_0 + OP_PUSHBYTES_72 + DUMMY_DER_SIG + OP_PUSHBYTES_72 + DUMMY_REEDEM_SCRIPT
    if script_sig is not None:
        return Script.from_raw(script_sig)
    return None


def get_dummy_witness(script_pub_key):
    output_type = get_output_type(script_pub_key)
    witness = None
    if output_type == "P2WPKH":
        witness = [DUMMY_DER_SIG, DUMMY_PUBKEY]
    elif output_type == "P2WSH":
        witness = [
            OP_PUSHBYTES_72 + DUMMY_DER_SIG + OP_PUSHBYTES_33 + DUMMY_PUBKEY,  # P2PKH unlock script
            script_pub_key,
        ]
    elif output_type == "P2TR":
        witness = [DUMMY_SCHNORR_SIG]
    if witness is not None:
        return TxWitnessInput(witness)
    return None


def generate_dummy_signed_tx(tx, selected_utxos):
    dummy_signed_tx = Transaction.copy(tx)
    for i, utxo in enumerate(selected_utxos):
        dummy_script_sig = get_dummy_script_sig(utxo["script_pub_key"])
        if dummy_script_sig is not None:
            dummy_signed_tx.inputs[i].script_sig = dummy_script_sig
        dummy_witness = get_dummy_witness(utxo["script_pub_key"])
        if dummy_witness is not None:
            dummy_signed_tx.witnesses.append(dummy_witness)
    return dummy_signed_tx


def get_output_sigops_count(script_pub_key, is_redeem_script=False, is_segwit=False):
    output_type = get_output_type(script_pub_key)
    multiplicator = 1 if is_segwit else 4
    count = 0
    if output_type in ["P2PK", "P2PKH"]:
        count = 1
    elif output_type == "P2MS":
        if is_redeem_script:
            asm = script.script_to_asm(script_pub_key)
            pubkeys_count = int(asm[-2])
            if pubkeys_count > 16:
                count = 20
            else:
                count = pubkeys_count
        else:
            count = 20
    elif output_type in ["P2WPKH", "P2WSH", "P2TR"] and is_redeem_script:
        return 1
    return count * multiplicator


def get_input_sigops_count(script_sig, script_pub_key):
    prevout_type = get_output_type(script_pub_key)
    if prevout_type == "P2SH":
        asm = script.script_to_asm(script_sig)
        redeem_script = binascii.hexlify(asm[-1]).decode("utf-8")
        return get_output_sigops_count(redeem_script, is_redeem_script=True)
    if prevout_type == "P2WPKH":
        return 1
    if prevout_type == "P2WSH":
        return get_output_sigops_count(script_pub_key, is_segwit=True)
    return 0


# source: https://bitcoin.stackexchange.com/questions/67760/how-are-sigops-calculated
def get_tx_sigops_count(tx, selected_utxos):
    sigops_count = 0
    for i, utxo in enumerate(selected_utxos):
        script_pub_key = utxo["script_pub_key"]
        script_sig = tx.inputs[i].script_sig.to_hex()
        sigops_count += get_input_sigops_count(script_sig, script_pub_key)
    for output in tx.outputs:
        sigops_count += get_output_sigops_count(output.script_pubkey.to_hex())
    return sigops_count


# source: https://mempool.space/docs/faq#what-is-adjusted-vsize
def get_size_info(tx, selected_utxos, signed=False):
    if signed:
        signed_tx = tx
    else:
        signed_tx = generate_dummy_signed_tx(tx, selected_utxos)
    sigops_count = get_tx_sigops_count(signed_tx, selected_utxos)
    virtual_size = signed_tx.get_vsize()
    adjusted_vsize = max(sigops_count * 5, virtual_size)
    return adjusted_vsize, virtual_size, sigops_count


def prepare_fee_parameters(construct_params):
    exact_fee = construct_params.get("exact_fee")
    sat_per_vbyte = construct_params.get("sat_per_vbyte")
    confirmation_target = construct_params.get("confirmation_target")
    max_fee = construct_params.get("max_fee")
    if exact_fee is not None:
        sat_per_vbyte, confirmation_target, max_fee = None, None, None
    elif sat_per_vbyte is None:
        if confirmation_target is not None:
            sat_per_vbyte = backend.bitcoind.satoshis_per_vbyte(confirmation_target)
        else:
            sat_per_vbyte = backend.bitcoind.satoshis_per_vbyte()
    return exact_fee, sat_per_vbyte, max_fee


def prepare_inputs_and_change(db, source, outputs, unspent_list, construct_params):
    # prepare fee parameters
    exact_fee, sat_per_vbyte, max_fee = prepare_fee_parameters(construct_params)

    change_address = construct_params.get("change_address")
    if change_address is None:
        if utxosinfo.is_utxo_format(source):
            change_address = utxo_to_address(db, source)
        else:
            change_address = source

    outputs_total = sum(output.amount for output in outputs)

    change_outputs = []
    btc_in = 0
    needed_fee = 0
    size_info = (0, 0, 0)
    # try with one input and increase until the change is enough for the fee
    use_all_inputs_set = construct_params.get("use_all_inputs_set", False)
    input_count = len(unspent_list) if use_all_inputs_set else 1
    while True:
        if input_count > len(unspent_list):
            total_needed = outputs_total + (exact_fee or needed_fee)
            raise exceptions.ComposeError(
                f"Insufficient funds for the target amount: {btc_in} < {total_needed}"
            )

        selected_utxos = unspent_list[:input_count]
        inputs = utxos_to_txins(selected_utxos)
        btc_in = sum(utxo["value"] for utxo in selected_utxos)
        change_amount = int(btc_in - outputs_total)

        # if change is negative, try with more inputs
        if change_amount < 0:
            input_count += 1
            continue
        # if change is not enough for exact_fee, try with more inputs
        if exact_fee is not None and change_amount < exact_fee:
            input_count += 1
            continue

        # if change is enough for exact_fee, add change output and break
        if exact_fee is not None:
            change_amount = int(change_amount - exact_fee)
            if change_amount > dust_size(change_address, construct_params):
                change_outputs.append(
                    create_tx_output(change_amount, change_address, unspent_list, construct_params)
                )
            break

        # else calculate needed fee
        has_segwit = any(utxo["is_segwit"] for utxo in selected_utxos)

        tx = Transaction(
            inputs,
            outputs
            + [create_tx_output(change_amount, change_address, unspent_list, construct_params)],
            has_segwit=has_segwit,
        )

        size_info = get_size_info(tx, selected_utxos)
        adjusted_vsize = size_info[0]
        needed_fee = sat_per_vbyte * adjusted_vsize
        if max_fee is not None:
            needed_fee = min(needed_fee, max_fee)
        needed_fee = int(needed_fee)
        # if change is enough for needed fee, add change output and break
        if change_amount > needed_fee:
            change_amount = int(change_amount - needed_fee)
            if change_amount > dust_size(change_address, construct_params):
                change_outputs.append(
                    create_tx_output(change_amount, change_address, unspent_list, construct_params)
                )
            break
        # else try with more inputs
        input_count += 1

    return selected_utxos, btc_in, change_outputs


def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def compose_data(db, name, params, accept_missing_params=False, skip_validation=False):
    try:
        compose_method = sys.modules[f"counterpartycore.lib.messages.{name}"].compose
    except KeyError as e:
        raise exceptions.ComposeError(f"message {name} not found") from e
    compose_params = inspect.getfullargspec(compose_method)[0]
    missing_params = [p for p in compose_params if p not in params and p != "db"]
    if accept_missing_params:  # for API v1 backward compatibility
        for param in missing_params:
            params[param] = None
    else:
        if len(missing_params) > 0:
            default_values = get_default_args(compose_method)
            for param in missing_params:
                if param in default_values:
                    params[param] = default_values[param]
                else:
                    raise exceptions.ComposeError(
                        f"missing parameters: {', '.join(missing_params)}"
                    )
    params["skip_validation"] = skip_validation
    return compose_method(db, **params)


def construct(db, tx_info, construct_params):
    source, destinations, data = tx_info

    # prepare unspent list
    unspent_list = prepare_unspent_list(db, source, construct_params)

    # prepare outputs
    outputs = prepare_outputs(source, destinations, data, unspent_list, construct_params)

    # prepare inputs and change
    selected_utxos, btc_in, change_outputs = prepare_inputs_and_change(
        db, source, outputs, unspent_list, construct_params
    )
    inputs = utxos_to_txins(selected_utxos)

    if not construct_params.get("disable_utxo_locks", False):
        UTXOLocks().lock_inputs(inputs)

    # construct transaction
    btc_out = sum(output.amount for output in outputs)
    btc_change = sum(change_output.amount for change_output in change_outputs)
    lock_scripts = [utxo["script_pub_key"] for utxo in selected_utxos]
    tx = Transaction(inputs, outputs + change_outputs)
    unsigned_tx_hex = tx.serialize()
    adjusted_vsize, virtual_size, sigops_count = get_size_info(tx, selected_utxos)

    return {
        "rawtransaction": unsigned_tx_hex,
        "btc_in": btc_in,
        "btc_out": btc_out,
        "btc_change": btc_change,
        "btc_fee": btc_in - btc_out - btc_change,
        "data": config.PREFIX + data if data else None,
        "lock_scripts": lock_scripts,
        "signed_tx_estimated_size": {
            "vsize": virtual_size,
            "adjusted_vsize": adjusted_vsize,
            "sigops_count": sigops_count,
        },
    }


def check_transaction_sanity(tx_info, composed_tx, construct_params):
    tx_hex = composed_tx["rawtransaction"]
    source, destinations, data = tx_info
    decoded_tx = deserialize.deserialize_tx(tx_hex, parse_vouts=True)

    # check if source address matches the first input address
    first_utxo_txid = decoded_tx["vin"][0]["hash"]
    first_utxo = f"{first_utxo_txid}:{decoded_tx['vin'][0]['n']}"

    if utxosinfo.is_utxo_format(source):
        source_is_ok = first_utxo == source
    else:
        source_is_ok = is_address_script(source, composed_tx["lock_scripts"][0])

    if not source_is_ok:
        raise exceptions.ComposeError(
            "Sanity check error: source address does not match the first input address"
        )

    # check if destination addresses and values match the outputs
    for i, destination in enumerate(destinations):
        address, value = destination
        out = decoded_tx["vout"][i]

        if not is_address_script(address, out["script_pub_key"]):
            raise exceptions.ComposeError(
                "Sanity check error: destination address does not match the output address"
            )

        value_is_ok = True
        if value is not None:
            if value != out["value"]:
                value_is_ok = False
        elif out["value"] not in [
            regular_dust_size(construct_params),
            multisig_dust_size(construct_params),
        ]:
            value_is_ok = False

        if not value_is_ok:
            raise exceptions.ComposeError(
                "Sanity check error: destination value does not match the output value"
            )

    # check if data matches the output data
    if data:
        if isinstance(decoded_tx["parsed_vouts"], Exception):
            raise exceptions.ComposeError(
                f"Sanity check error: cannot parse the output data from the transaction ({decoded_tx['parsed_vouts']})"
            )
        _, _, _, tx_data, _ = decoded_tx["parsed_vouts"]
        if tx_data != data:
            raise exceptions.ComposeError("Sanity check error: data does not match the output data")


CONSTRUCT_PARAMS = {
    # general parameters
    "encoding": (str, "auto", "The encoding method to use"),
    "validate": (bool, True, "Validate the transaction"),
    # fee parameters
    "sat_per_vbyte": (float, None, "The fee per vbyte in satoshis"),
    "confirmation_target": (
        int,
        config.ESTIMATE_FEE_CONF_TARGET,
        "The number of blocks to target for confirmation",
    ),
    "exact_fee": (int, None, "The exact fee to use in satoshis"),
    "max_fee": (int, None, "The maximum fee to use in satoshis"),
    # inputs parameters
    "inputs_set": (
        str,
        None,
        "A comma-separated list of UTXOs (`<txid>:<vout>`) to use as inputs for the transaction being created. To speed up the composition you can also use the following format for utxos: `<txid>:<vout>:<value>:<script_pub_key>`.",
    ),
    "allow_unconfirmed_inputs": (
        bool,
        False,
        "Set to true to allow this transaction to utilize unconfirmed UTXOs as inputs",
    ),
    "exclude_utxos": (
        str,
        None,
        "A comma-separated list of UTXO txids to exclude when selecting UTXOs to use as inputs for the transaction being created",
    ),
    "use_utxos_with_balances": (bool, False, "Use UTXO with balances"),
    "exclude_utxos_with_balances": (
        bool,
        False,
        "Exclude silently UTXO with balances instead of raising an exception. Important: the `exclude_utxos_with_balances` will not exclude unconfirmed `attach` and `utxomove`. You need to explicitly exclude them with the `exclude_utxos` parameter",
    ),
    "disable_utxo_locks": (
        bool,
        False,
        "By default, UTXOs utilized when creating a transaction are 'locked' for a few seconds, to prevent a case where rapidly generating create_ calls reuse UTXOs due to their spent status not being updated in bitcoind yet. Specify true for this parameter to disable this behavior, and not temporarily lock UTXOs",
    ),
    "use_all_inputs_set": (bool, False, "Use all UTXOs provide with `inputs_set` parameter"),
    # outputs parameters
    "mutlisig_pubkey": (
        str,
        None,
        "The reedem public key to use for multisig encoding, by default it is searched for the source address",
    ),
    "change_address": (str, None, "The address to send the change to"),
    "more_outputs": (
        str,
        None,
        "Additional outputs to include in the transaction in the format `<value>:<address>` or `<value>:<script>`",
    ),
    "pubkeys": (
        str,
        None,
        "Pubkeys needed in case one or more destinations are multisig addresses",
    ),
    # result parameters
    "verbose": (
        bool,
        False,
        "Include additional information in the result including data and psbt",
    ),
    "return_only_data": (bool, False, "Return only the data part of the transaction"),
    # deprecated parameters
    "fee_per_kb": (int, None, "Deprecated, use `sat_per_vbyte` instead"),
    "fee_provided": (int, None, "Deprecated, use `max_fee` instead"),
    "unspent_tx_hash": (str, None, "Deprecated, use `inputs_set` instead"),
    "dust_return_pubkey": (str, None, "Deprecated, use `mutlisig_pubkey` instead"),
    "return_psbt": (bool, False, "Deprecated, use `verbose` instead"),
    "regular_dust_size": (int, None, "Deprecated, automatically calculated"),
    "multisig_dust_size": (int, None, "Deprecated, automatically calculated"),
    "extended_tx_info": (bool, False, "Deprecated (API v1 only), use API v2 instead"),
    "old_style_api": (bool, False, "Deprecated (API v1 only), use API v2 instead"),
    "p2sh_pretx_txid": (str, None, "Ignored, P2SH disabled"),
    "segwit": (bool, False, "Ignored, Segwit automatically detected"),
}
DEPRECATED_CONSTRUCT_PARAMS = [
    "fee_per_kb",
    "fee_provided",
    "dust_return_pubkey",
    "return_psbt",
    "regular_dust_size",
    "multisig_dust_size",
    "extended_tx_info",
    "old_style_api",
    "p2sh_pretx_txid",
    "segwit",
    "unspent_tx_hash",
]


def fee_per_kb_to_sat_per_vbyte(fee_per_kb):
    if fee_per_kb is None or fee_per_kb == 0:
        return 0
    print("Fee per kb", fee_per_kb)
    print("Fee per vbyte", float(D(fee_per_kb) / D(1024)))
    return float(D(fee_per_kb) / D(1024))


def prepare_construct_params(construct_params):
    cleaned_construct_params = construct_params.copy()
    # copy deprecated parameters to new ones
    for deprecated_param, new_param, copyer in [
        ("fee_per_kb", "sat_per_vbyte", fee_per_kb_to_sat_per_vbyte),
        ("fee_provided", "max_fee", lambda x: x),
        ("dust_return_pubkey", "mutlisig_pubkey", lambda x: x),
        ("return_psbt", "verbose", lambda x: x),
    ]:
        if deprecated_param in construct_params:
            if (
                construct_params.get(new_param) is None or not construct_params.get(new_param)
            ) and construct_params.get(deprecated_param) is not None:
                cleaned_construct_params[new_param] = copyer(construct_params[deprecated_param])
            cleaned_construct_params.pop(deprecated_param)
    # add warnings for deprecated parameters
    warnings = []
    for field in DEPRECATED_CONSTRUCT_PARAMS:
        if field in construct_params and construct_params[field] not in [None, False]:
            warnings.append(f"The `{field}` parameter is {CONSTRUCT_PARAMS[field][2].lower()}")

    return cleaned_construct_params, warnings


def compose_transaction(db, name, params, construct_parameters):
    helpers.setup_bitcoinutils()

    construct_params, warnings = prepare_construct_params(construct_parameters)

    # prepare data
    skip_validation = not construct_params.get("validate", True)
    tx_info = compose_data(db, name, params, skip_validation=skip_validation)

    if construct_params.get("return_only_data", False):
        data = tx_info[2]
        return {
            "data": config.PREFIX + data if data else None,
        }

    # construct transaction
    result = construct(db, tx_info, construct_params)

    # sanity check
    try:
        check_transaction_sanity(tx_info, result, construct_params)
    except Exception as e:
        raise exceptions.ComposeError(str(e)) from e

    # return result
    if construct_params.get("verbose", False):
        result = result | {
            "psbt": backend.bitcoind.convert_to_psbt(result["rawtransaction"]),
            "params": params,
            "name": name.split(".")[-1],
        }
    else:
        result = {
            "rawtransaction": result["rawtransaction"],
        }

    if len(warnings) > 0:
        result["warnings"] = warnings

    return result
