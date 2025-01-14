import binascii
import logging

from counterpartycore.lib import backend, config, util
from counterpartycore.lib.exceptions import BTCOnlyError, DecodeError
from counterpartycore.lib.parser import protocol
from counterpartycore.lib.utils import base58, script
from counterpartycore.lib.utils.opcodes import *  # noqa: F403

logger = logging.getLogger(config.LOGGER_NAME)


def get_pubkeyhash(scriptpubkey, block_index):
    asm = script.script_to_asm(scriptpubkey)
    if protocol.enabled("multisig_addresses", block_index=block_index):
        if len(asm) > 0:
            if asm[0] == OP_DUP:  # noqa: F405
                if (
                    len(asm) != 5
                    or asm[1] != OP_HASH160  # noqa: F405
                    or asm[3] != OP_EQUALVERIFY  # noqa: F405
                    or asm[4] != OP_CHECKSIG  # noqa: F405
                ):
                    return None, None
                else:
                    return asm[2], config.ADDRESSVERSION

            elif (asm[0] == OP_HASH160) and protocol.enabled("p2sh_dispensers_support"):  # noqa: F405
                if len(asm) != 3 or asm[-1] != "OP_EQUAL":
                    return None, None
                else:
                    return asm[1], config.P2SH_ADDRESSVERSION
        return None, None
    else:
        if (
            len(asm) != 5
            or asm[0] != OP_DUP  # noqa: F405
            or asm[1] != OP_HASH160  # noqa: F405
            or asm[3] != OP_EQUALVERIFY  # noqa: F405
            or asm[4] != OP_CHECKSIG  # noqa: F405
        ):
            return None, None
        return asm[2], config.ADDRESSVERSION


def is_witness_v0_keyhash(scriptpubkey):
    """Returns true if this is a scriptpubkey for V0 P2WPKH."""
    return len(scriptpubkey) == 22 and scriptpubkey[0:2] == b"\x00\x14"


def get_address(scriptpubkey, block_index):
    if isinstance(scriptpubkey, str):
        scriptpubkey = binascii.unhexlify(scriptpubkey)
    if protocol.enabled("correct_segwit_txids") and is_witness_v0_keyhash(scriptpubkey):
        address = script.script_to_address(scriptpubkey)
        return address
    else:
        pubkeyhash, address_version = get_pubkeyhash(scriptpubkey, block_index)
        if not pubkeyhash:
            return False
        pubkeyhash = binascii.hexlify(pubkeyhash).decode("utf-8")
        address = base58.base58_check_encode(pubkeyhash, address_version)
        # Test decoding of address.
        if address != config.UNSPENDABLE and binascii.unhexlify(
            bytes(pubkeyhash, "utf-8")
        ) != base58.base58_check_decode(address, address_version):
            return False
        return address


def get_tx_info_legacy(decoded_tx, block_index):
    """Get singlesig transaction info.
    The destination, if it exists, always comes before the data output; the
    change, if it exists, always comes after.
    """

    if decoded_tx["coinbase"]:
        raise DecodeError("coinbase transaction")

    # Fee is the input values minus output values.
    fee = 0

    # Get destination output and data output.
    destination, btc_amount, data = None, None, b""
    pubkeyhash_encoding = False
    for vout in decoded_tx["vout"]:
        fee -= vout["value"]

        script_pub_key = vout["script_pub_key"]

        # Sum data chunks to get data. (Can mix OP_RETURN and multi-sig.)
        asm = script.script_to_asm(script_pub_key)
        if len(asm) == 2 and asm[0] == OP_RETURN:  # OP_RETURN  # noqa: F405
            if type(asm[1]) != bytes:  # noqa: E721
                continue
            data_chunk = asm[1]
            data += data_chunk
        elif (
            len(asm) == 5 and asm[0] == 1 and asm[3] == 2 and asm[4] == OP_CHECKMULTISIG  # noqa: F405
        ):  # Multi-sig
            if type(asm[2]) != bytes:  # noqa: E721
                continue
            data_pubkey = asm[2]
            data_chunk_length = data_pubkey[0]  # No ord() necessary.
            data_chunk = data_pubkey[1 : data_chunk_length + 1]
            data += data_chunk
        elif len(asm) == 5 and protocol.after_block_or_test_network(
            block_index, 293000
        ):  # Protocol change.
            # Be strict.
            pubkeyhash, address_version = get_pubkeyhash(script_pub_key, block_index)
            if not pubkeyhash:
                continue

            data_pubkey = util.arc4_decrypt(pubkeyhash, decoded_tx)
            if data_pubkey[1:9] == config.PREFIX or pubkeyhash_encoding:
                pubkeyhash_encoding = True
                data_chunk_length = data_pubkey[0]  # No ord() necessary.
                data_chunk = data_pubkey[1 : data_chunk_length + 1]
                if data_chunk[-8:] == config.PREFIX:
                    data += data_chunk[:-8]
                    break
                else:
                    data += data_chunk

        # Destination is the first output before the data.
        if not destination and not btc_amount and not data:
            address = get_address(script_pub_key, block_index)
            if address:
                destination = address
                btc_amount = vout["value"]

    # Check for, and strip away, prefix (except for burns).
    if destination == config.UNSPENDABLE:
        pass
    elif data[: len(config.PREFIX)] == config.PREFIX:
        data = data[len(config.PREFIX) :]
    else:
        raise DecodeError("no prefix")

    # Only look for source if data were found or destination is UNSPENDABLE, for speed.
    if not data and destination != config.UNSPENDABLE:
        raise BTCOnlyError("no data and not unspendable")

    # Collect all possible source addresses; ignore coinbase transactions and anything but the simplest Pay‐to‐PubkeyHash inputs.
    source_list = []
    for vin in decoded_tx["vin"][:]:  # Loop through input transactions.
        # Get the full transaction data for this input transaction.
        vout_value, script_pubkey, _is_segwit = backend.bitcoind.get_vin_info(vin)
        fee += vout_value

        address = get_address(script_pubkey, block_index)
        if not address:
            raise DecodeError("invalid scriptpubkey")
        else:
            source_list.append(address)

    # Require that all possible source addresses be the same.
    if all(x == source_list[0] for x in source_list):
        source = source_list[0]
    else:
        source = None

    return source, destination, btc_amount, fee, data, []
