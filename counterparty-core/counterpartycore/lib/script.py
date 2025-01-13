"""
None of the functions/objects in this module need be passed `db`.

Naming convention: a `pub` is either a pubkey or a pubkeyhash
"""

import binascii
import hashlib

import bitcoin as bitcoinlib
from bitcoin.bech32 import CBech32Data
from bitcoin.core.key import CPubKey
from bitcoinutils.keys import PublicKey
from bitcoinutils.setup import setup
from counterparty_rs import b58, utils

# TODO: Use `python-bitcointools` instead. (Get rid of `pycoin` dependency.)
from pycoin.ecdsa.secp256k1 import secp256k1_generator as generator_secp256k1
from pycoin.encoding.b58 import a2b_hashed_base58
from pycoin.encoding.bytes32 import from_bytes_32
from pycoin.encoding.exceptions import EncodingError
from pycoin.encoding.sec import public_pair_to_sec
from ripemd import ripemd160 as RIPEMD160  # nosec B413

from counterpartycore.lib import backend, config, exceptions, opcodes, util
from counterpartycore.lib.opcodes import *  # noqa: F403

B58_DIGITS = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class InputError(Exception):
    pass


class AddressError(Exception):
    pass


class MultiSigAddressError(AddressError):
    pass


class VersionByteError(AddressError):
    pass


class Base58Error(AddressError):
    pass


class Base58ChecksumError(Base58Error):
    pass


def validate(address, allow_p2sh=True):
    """Make sure the address is valid.

    May throw `AddressError`.
    """
    # Get array of pubkeyhashes to check.
    if is_multisig(address):
        pubkeyhashes = pubkeyhash_array(address)
    else:
        pubkeyhashes = [address]

    # Check validity by attempting to decode.
    for pubkeyhash in pubkeyhashes:
        try:
            if util.enabled("segwit_support"):
                if not is_bech32(pubkeyhash):
                    base58_check_decode(pubkeyhash, config.ADDRESSVERSION)
            else:
                base58_check_decode(pubkeyhash, config.ADDRESSVERSION)
        except VersionByteError as e:
            if not allow_p2sh:
                raise e
            base58_check_decode(pubkeyhash, config.P2SH_ADDRESSVERSION)
        except Base58Error as e:
            if not util.enabled("segwit_support") or not is_bech32(pubkeyhash):
                raise e


def base58_encode(binary):
    """Encode the address in base58."""
    # Convert big‐endian bytes to integer
    n = int("0x0" + util.hexlify(binary), 16)

    # Divide that integer into base58
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(B58_DIGITS[r])
    res = "".join(res[::-1])

    return res


def base58_check_encode_py(original, version):
    """Check if base58 encoding is valid."""
    b = binascii.unhexlify(bytes(original, "utf-8"))
    d = version + b

    binary = d + util.dhash(d)[:4]
    res = base58_encode(binary)

    # Encode leading zeros as base58 zeros
    czero = 0
    pad = 0
    for c in d:
        if c == czero:
            pad += 1
        else:
            break

    address = B58_DIGITS[0] * pad + res

    if original != util.hexlify(base58_check_decode(address, version)):
        raise AddressError("encoded address does not decode properly")

    return address


def base58_check_encode(original, version):
    return b58.b58_encode(version + binascii.unhexlify(original))


def base58_decode(s):
    # Convert the string to an integer
    n = 0
    for c in s:
        n *= 58
        if c not in B58_DIGITS:
            raise Base58Error(f"Not a valid Base58 character: ‘{c}’")
        digit = B58_DIGITS.index(c)
        n += digit

    # Convert the integer to bytes
    h = f"{n:x}"
    if len(h) % 2:
        h = "0" + h
    res = binascii.unhexlify(h.encode("utf8"))

    # Add padding back.
    pad = 0
    for c in s[:-1]:
        if c == B58_DIGITS[0]:
            pad += 1
        else:
            break
    k = b"\x00" * pad + res

    return k


def base58_check_decode_parts(s):
    """Decode from base58 and return parts."""

    k = base58_decode(s)

    addrbyte, data, chk0 = k[0:1], k[1:-4], k[-4:]

    return addrbyte, data, chk0


def base58_check_decode_py(s, version):
    """Decode from base58 and return data part."""

    addrbyte, data, chk0 = base58_check_decode_parts(s)

    if addrbyte != version:
        raise VersionByteError("incorrect version byte")

    chk1 = util.dhash(addrbyte + data)[:4]
    if chk0 != chk1:
        raise Base58ChecksumError(
            f"Checksum mismatch: 0x{util.hexlify(chk0)} ≠ 0x{util.hexlify(chk1)}"
        )

    return data


def base58_check_decode(s, version):
    try:
        decoded = bytes(b58.b58_decode(s))
    except ValueError:
        raise Base58Error("invalid base58 string")  # noqa: B904

    if decoded[0] != ord(version):
        raise VersionByteError("incorrect version byte")

    return decoded[1:]


def is_multisig(address):
    """Check if the address is multi‐signature."""
    array = address.split("_")
    return len(array) > 1


def is_p2sh(address):
    if is_multisig(address):
        return False

    try:
        base58_check_decode(address, config.P2SH_ADDRESSVERSION)
        return True
    except (VersionByteError, Base58Error):
        return False


def is_bech32(address):
    try:
        b32data = CBech32Data(address)  # noqa: F841
        return True
    except:  # noqa: E722
        return False


def is_fully_valid(pubkey_bin):
    """Check if the public key is valid."""
    cpubkey = CPubKey(pubkey_bin)
    return cpubkey.is_fullyvalid


def make_canonical(address):
    """Return canonical version of the address."""
    if is_multisig(address):
        signatures_required, pubkeyhashes, signatures_possible = extract_array(address)
        try:
            [base58_check_decode(pubkeyhash, config.ADDRESSVERSION) for pubkeyhash in pubkeyhashes]
        except Base58Error:
            raise MultiSigAddressError(  # noqa: B904
                "Multi‐signature address must use PubKeyHashes, not public keys."
            )
        return construct_array(signatures_required, pubkeyhashes, signatures_possible)
    else:
        return address


def test_array(signatures_required, pubs, signatures_possible):
    """Check if multi‐signature data is valid."""
    try:
        signatures_required, signatures_possible = (
            int(signatures_required),
            int(signatures_possible),
        )
    except (ValueError, TypeError):
        raise MultiSigAddressError("Signature values not integers.")  # noqa: B904
    if signatures_required < 1 or signatures_required > 3:
        raise MultiSigAddressError("Invalid signatures_required.")
    if signatures_possible < 2 or signatures_possible > 3:
        raise MultiSigAddressError("Invalid signatures_possible.")
    for pubkey in pubs:
        if "_" in pubkey:
            raise MultiSigAddressError("Invalid characters in pubkeys/pubkeyhashes.")
    if signatures_possible != len(pubs):
        raise InputError("Incorrect number of pubkeys/pubkeyhashes in multi‐signature address.")


def construct_array(signatures_required, pubs, signatures_possible):
    """Create a multi‐signature address."""
    test_array(signatures_required, pubs, signatures_possible)
    address = "_".join([str(signatures_required)] + sorted(pubs) + [str(signatures_possible)])
    return address


def extract_array(address):
    """Extract data from multi‐signature address."""
    assert is_multisig(address)
    array = address.split("_")
    signatures_required, pubs, signatures_possible = array[0], sorted(array[1:-1]), array[-1]
    test_array(signatures_required, pubs, signatures_possible)
    return int(signatures_required), pubs, int(signatures_possible)


def pubkeyhash_array(address):
    """Return PubKeyHashes from an address."""
    signatures_required, pubs, signatures_possible = extract_array(address)
    if not all([is_pubkeyhash(pub) for pub in pubs]):
        raise MultiSigAddressError(
            "Invalid PubKeyHashes. Multi‐signature address must use PubKeyHashes, not public keys."
        )
    pubkeyhashes = pubs
    return pubkeyhashes


def hash160(x):
    x = hashlib.sha256(x).digest()
    m = RIPEMD160.new()
    m.update(x)
    return m.digest()


def pubkey_to_pubkeyhash(pubkey):
    """Convert public key to PubKeyHash."""
    pubkeyhash = hash160(pubkey)
    pubkey = base58_check_encode(
        binascii.hexlify(pubkeyhash).decode("utf-8"), config.ADDRESSVERSION
    )
    return pubkey


def pubkey_to_p2whash(pubkey):
    """Convert public key to PayToWitness."""
    pubkeyhash = hash160(pubkey)
    pubkey = CBech32Data.from_bytes(0, pubkeyhash)
    return str(pubkey)


def pubkey_to_p2whash2(pubkey):
    if config.NETWORK_NAME.startswith("testnet"):
        setup("testnet")
    else:
        setup(config.NETWORK_NAME)
    address = PublicKey.from_hex(pubkey).get_segwit_address().to_string()
    return address


def bech32_to_scripthash(address):
    bech32 = CBech32Data(address)
    return bytes(bech32)


def get_asm(scriptpubkey):
    # TODO: When is an exception thrown here? Can this `try` block be tighter? Can it be replaced by a conditional?
    try:
        asm = []
        # TODO: This should be `for element in scriptpubkey`.
        for op in scriptpubkey:
            if type(op) == bitcoinlib.core.script.CScriptOp:  # noqa: E721
                # TODO: `op = element`
                asm.append(getattr(opcodes, str(op)))
            else:
                # TODO: `data = element` (?)
                asm.append(op)
    except bitcoinlib.core.script.CScriptTruncatedPushDataError:
        raise exceptions.PushDataDecodeError("invalid pushdata due to truncation")  # noqa: B904
    if not asm:
        raise exceptions.DecodeError("empty output")
    return asm


def script_to_asm(scriptpubkey):
    try:
        if isinstance(scriptpubkey, bitcoinlib.core.script.CScript):
            scriptpubkey = bytes(scriptpubkey)
        elif isinstance(scriptpubkey, str):
            scriptpubkey = binascii.unhexlify(scriptpubkey)
        asm = utils.script_to_asm(scriptpubkey)
        if asm[-1] == OP_CHECKMULTISIG:  # noqa: F405
            asm[-2] = int.from_bytes(asm[-2], "big")
            asm[0] = int.from_bytes(asm[0], "big")
        return asm
    except BaseException as e:  # noqa: F841
        raise exceptions.DecodeError("invalid script")  # noqa: B904


def script_to_address(scriptpubkey):
    if isinstance(scriptpubkey, str):
        scriptpubkey = binascii.unhexlify(scriptpubkey)
    try:
        script = bytes(scriptpubkey, "utf-8") if type(scriptpubkey) == str else bytes(scriptpubkey)  # noqa: E721
        return utils.script_to_address(script, config.NETWORK_NAME)
    except BaseException as e:  # noqa: F841
        raise exceptions.DecodeError("scriptpubkey decoding error")  # noqa: B904


def script_to_address2(scriptpubkey):
    if isinstance(scriptpubkey, str):
        scriptpubkey = binascii.unhexlify(scriptpubkey)
    try:
        script = bytes(scriptpubkey, "utf-8") if type(scriptpubkey) == str else bytes(scriptpubkey)  # noqa: E721
        return utils.script_to_address2(script, config.NETWORK_NAME)
    except BaseException as e:  # noqa: F841
        raise exceptions.DecodeError("scriptpubkey decoding error")  # noqa: B904


def get_checksig(asm):
    try:
        op_dup, op_hash160, pubkeyhash, op_equalverify, op_checksig = asm
    except ValueError:
        raise exceptions.DecodeError("invalid OP_CHECKSIG") from None

    if (op_dup, op_hash160, op_equalverify, op_checksig) == (
        OP_DUP,  # noqa: F405
        OP_HASH160,  # noqa: F405
        OP_EQUALVERIFY,  # noqa: F405
        OP_CHECKSIG,  # noqa: F405
    ) and type(pubkeyhash) == bytes:  # noqa: E721
        return pubkeyhash

    raise exceptions.DecodeError("invalid OP_CHECKSIG")


def get_checkmultisig(asm):
    # N‐of‐2
    if len(asm) == 5 and asm[3] == 2 and asm[4] == OP_CHECKMULTISIG:  # noqa: F405
        pubkeys, signatures_required = asm[1:3], asm[0]
        if all([type(pubkey) == bytes for pubkey in pubkeys]):  # noqa: E721
            return pubkeys, signatures_required
    # N‐of‐3
    if len(asm) == 6 and asm[4] == 3 and asm[5] == OP_CHECKMULTISIG:  # noqa: F405
        pubkeys, signatures_required = asm[1:4], asm[0]
        if all([type(pubkey) == bytes for pubkey in pubkeys]):  # noqa: E721
            return pubkeys, signatures_required
    raise exceptions.DecodeError("invalid OP_CHECKMULTISIG")


# TODO: Not used ?
def scriptpubkey_to_address(scriptpubkey):
    asm = script_to_asm(scriptpubkey)

    if asm[-1] == OP_CHECKSIG:  # noqa: F405
        try:
            checksig = get_checksig(asm)
        except exceptions.DecodeError:  # coinbase
            return None

        return base58_check_encode(
            binascii.hexlify(checksig).decode("utf-8"), config.ADDRESSVERSION
        )

    elif asm[-1] == OP_CHECKMULTISIG:  # noqa: F405
        pubkeys, signatures_required = get_checkmultisig(asm)
        pubkeyhashes = [pubkey_to_pubkeyhash(pubkey) for pubkey in pubkeys]
        return construct_array(signatures_required, pubkeyhashes, len(pubkeyhashes))

    elif len(asm) == 3 and asm[0] == OP_HASH160 and asm[2] == OP_EQUAL:  # noqa: F405
        return base58_check_encode(
            binascii.hexlify(asm[1]).decode("utf-8"), config.P2SH_ADDRESSVERSION
        )

    return None


def wif_to_tuple_of_prefix_secret_exponent_compressed(wif):
    """
    Return a tuple of (prefix, secret_exponent, is_compressed).
    """
    decoded = a2b_hashed_base58(wif)
    actual_prefix, private_key = decoded[:1], decoded[1:]
    compressed = len(private_key) > 32
    return actual_prefix, from_bytes_32(private_key[:32]), compressed


def wif_to_tuple_of_secret_exponent_compressed(wif, allowable_wif_prefixes=None):
    """Convert a WIF string to the corresponding secret exponent. Private key manipulation.
    Returns a tuple: the secret exponent, as a bignum integer, and a boolean indicating if the
    WIF corresponded to a compressed key or not.

    Not that it matters, since we can use the secret exponent to generate both the compressed
    and uncompressed Bitcoin address."""
    actual_prefix, secret_exponent, is_compressed = (
        wif_to_tuple_of_prefix_secret_exponent_compressed(wif)
    )
    if allowable_wif_prefixes and actual_prefix not in allowable_wif_prefixes:
        raise EncodingError(f"unexpected first byte of WIF {wif}")
    return secret_exponent, is_compressed


def public_pair_for_secret_exponent(generator, secret_exponent):
    return (generator * secret_exponent).pair()


class AltcoinSupportError(Exception):
    pass


def private_key_to_public_key(private_key_wif):
    """Convert private key to public key."""
    if config.TESTNET3:
        allowable_wif_prefixes = [config.PRIVATEKEY_VERSION_TESTNET]
    elif config.TESTNET4:
        allowable_wif_prefixes = [config.PRIVATEKEY_VERSION_TESTNET4]
    elif config.REGTEST:
        allowable_wif_prefixes = [config.PRIVATEKEY_VERSION_REGTEST]
    else:
        allowable_wif_prefixes = [config.PRIVATEKEY_VERSION_MAINNET]
    try:
        secret_exponent, compressed = wif_to_tuple_of_secret_exponent_compressed(
            private_key_wif, allowable_wif_prefixes=allowable_wif_prefixes
        )
    except EncodingError:
        raise AltcoinSupportError("pycoin: unsupported WIF prefix")  # noqa: B904
    public_pair = public_pair_for_secret_exponent(generator_secp256k1, secret_exponent)
    public_key = public_pair_to_sec(public_pair, compressed=compressed)
    public_key_hex = binascii.hexlify(public_key).decode("utf-8")
    return public_key_hex


def is_pubkeyhash(monosig_address):
    """Check if PubKeyHash is valid P2PKH address."""
    assert not is_multisig(monosig_address)
    try:
        base58_check_decode(monosig_address, config.ADDRESSVERSION)
        return True
    except (Base58Error, VersionByteError):
        return False


def make_pubkeyhash(address):
    """Create a new PubKeyHash."""
    if is_multisig(address):
        signatures_required, pubs, signatures_possible = extract_array(address)
        pubkeyhashes = []
        for pub in pubs:
            if is_pubkeyhash(pub):
                pubkeyhash = pub
            else:
                pubkeyhash = pubkey_to_pubkeyhash(binascii.unhexlify(bytes(pub, "utf-8")))
            pubkeyhashes.append(pubkeyhash)
        pubkeyhash_address = construct_array(signatures_required, pubkeyhashes, signatures_possible)
    else:
        if util.enabled("segwit_support") and is_bech32(address):
            pubkeyhash_address = address  # Some bech32 addresses are valid base58 data
        elif is_pubkeyhash(address):
            pubkeyhash_address = address
        elif is_p2sh(address):
            pubkeyhash_address = address
        else:
            pubkeyhash_address = pubkey_to_pubkeyhash(binascii.unhexlify(bytes(address, "utf-8")))
    return pubkeyhash_address


def extract_pubkeys(pub):
    """Assume pubkey if not pubkeyhash. (Check validity later.)"""
    pubkeys = []
    if is_multisig(pub):
        _, pubs, _ = extract_array(pub)
        for pub in pubs:
            if not is_pubkeyhash(pub):
                pubkeys.append(pub)
    elif is_p2sh(pub):
        pass
    elif util.enabled("segwit_support") and is_bech32(pub):
        pass
    else:
        if not is_pubkeyhash(pub):
            pubkeys.append(pub)
    return pubkeys


def ensure_script_pub_key_for_inputs(coins):
    txhash_set = set()
    for coin in coins:
        if "script_pub_key" not in coin:
            txhash_set.add(coin["txid"])

    if len(txhash_set) > 0:
        txhash_list_chunks = util.chunkify(list(txhash_set), config.MAX_RPC_BATCH_SIZE)
        txs = {}
        for txhash_list in txhash_list_chunks:
            txs = txs | backend.bitcoind.getrawtransaction_batch(
                txhash_list, verbose=True, return_dict=True
            )
        for coin in coins:
            if "script_pub_key" not in coin:
                # get the scriptPubKey
                txid = coin["txid"]
                if txid not in txs:
                    raise exceptions.ComposeError(f"Transaction {txid} not found")
                for vout in txs[txid]["vout"]:
                    if vout["n"] == coin["vout"]:
                        coin["script_pub_key"] = vout["scriptPubKey"]["hex"]

    return coins


def get_output_type(script_pub_key):
    asm = script_to_asm(script_pub_key)
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
    if is_multisig(address):
        asm = script_to_asm(script_pub_key)
        pubkeys = [binascii.hexlify(pubkey).decode("utf-8") for pubkey in asm[1:-2]]
        addresses = [
            PublicKey.from_hex(pubkey).get_address(compressed=True).to_string()
            for pubkey in pubkeys
        ]
        script_address = f"{asm[0]}_{'_'.join(addresses)}_{asm[-2]}"
    else:
        script_address = script_to_address2(script_pub_key)
    return address == script_address
