import binascii
import logging
import struct

from counterpartycore.lib import arc4, backend, config, ledger, message_type, script, util
from counterpartycore.lib.exceptions import BTCOnlyError, DecodeError
from counterpartycore.lib.messages import dispenser
from counterpartycore.lib.opcodes import *  # noqa: F403
from counterpartycore.lib.transaction_helper import p2sh_encoding
from counterpartycore.lib.util import inverse_hash

logger = logging.getLogger(config.LOGGER_NAME)


def arc4_decrypt(cyphertext, decoded_tx):
    """Un-obfuscate. Initialise key once per attempt."""
    if isinstance(decoded_tx["vin"][0]["hash"], str):
        vin_hash = binascii.unhexlify(inverse_hash(decoded_tx["vin"][0]["hash"]))
    else:
        vin_hash = decoded_tx["vin"][0]["hash"]
    key = arc4.init_arc4(vin_hash[::-1])
    return key.decrypt(cyphertext)


def get_opreturn(asm):
    if len(asm) == 2 and asm[0] == OP_RETURN:  # noqa: F405
        pubkeyhash = asm[1]
        if type(pubkeyhash) == bytes:  # noqa: E721
            return pubkeyhash
    raise DecodeError("invalid OP_RETURN")


def decode_opreturn(asm, decoded_tx, block_index):
    chunk = get_opreturn(asm)
    chunk = arc4_decrypt(chunk, decoded_tx)
    if chunk[: len(util.prefix(block_index))] == util.prefix(block_index):  # Data
        destination, data = None, chunk[len(util.prefix(block_index)) :]
    else:
        raise DecodeError("unrecognised OP_RETURN output")

    return destination, data


def decode_checksig(asm, decoded_tx, block_index):
    pubkeyhash = script.get_checksig(asm)
    chunk = arc4_decrypt(pubkeyhash, decoded_tx)  # TODO: This is slow!
    if chunk[1 : len(util.prefix(block_index)) + 1] == util.prefix(block_index):  # Data
        # Padding byte in each output (instead of just in the last one) so that encoding methods may be mixed. Also, it’s just not very much data.
        chunk_length = chunk[0]
        chunk = chunk[1 : chunk_length + 1]
        destination, data = None, chunk[len(util.prefix(block_index)) :]
    else:  # Destination
        pubkeyhash = binascii.hexlify(pubkeyhash).decode("utf-8")
        destination, data = script.base58_check_encode(pubkeyhash, config.ADDRESSVERSION), None
    return destination, data


def decode_scripthash(asm):
    destination = script.base58_check_encode(
        binascii.hexlify(asm[1]).decode("utf-8"), config.P2SH_ADDRESSVERSION
    )

    return destination, None


def decode_checkmultisig(asm, decoded_tx, block_index):
    pubkeys, signatures_required = script.get_checkmultisig(asm)
    chunk = b""
    for pubkey in pubkeys[:-1]:  # (No data in last pubkey.)
        chunk += pubkey[1:-1]  # Skip sign byte and nonce byte.
    chunk = arc4_decrypt(chunk, decoded_tx)
    if chunk[1 : len(util.prefix(block_index)) + 1] == util.prefix(block_index):  # Data
        # Padding byte in each output (instead of just in the last one) so that encoding methods may be mixed. Also, it’s just not very much data.
        chunk_length = chunk[0]
        chunk = chunk[1 : chunk_length + 1]
        destination, data = None, chunk[len(util.prefix(block_index)) :]
    else:  # Destination
        pubkeyhashes = [script.pubkey_to_pubkeyhash(pubkey) for pubkey in pubkeys]
        destination, data = (
            script.construct_array(signatures_required, pubkeyhashes, len(pubkeyhashes)),
            None,
        )

    return destination, data


def get_pubkeyhash(scriptpubkey, block_index):
    asm = script.script_to_asm(scriptpubkey)
    if util.enabled("multisig_addresses", block_index=block_index):
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

            elif (asm[0] == OP_HASH160) and util.enabled("p2sh_dispensers_support"):  # noqa: F405
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
    if util.enabled("correct_segwit_txids") and is_witness_v0_keyhash(scriptpubkey):
        address = script.script_to_address(scriptpubkey)
        return address
    else:
        pubkeyhash, address_version = get_pubkeyhash(scriptpubkey, block_index)
        if not pubkeyhash:
            return False
        pubkeyhash = binascii.hexlify(pubkeyhash).decode("utf-8")
        address = script.base58_check_encode(pubkeyhash, address_version)
        # Test decoding of address.
        if address != config.UNSPENDABLE and binascii.unhexlify(
            bytes(pubkeyhash, "utf-8")
        ) != script.base58_check_decode(address, address_version):
            return False
        return address


def get_vin_info(vin):
    if "value" in vin:
        return vin["value"], vin["script_pub_key"], vin["is_segwit"]

    # Note: We don't know what block the `vin` is in, and the block might have been from a while ago, so this call may not hit the cache.
    vin_ctx = backend.bitcoind.get_decoded_transaction(vin["hash"])

    is_segwit = len(vin_ctx["vtxinwit"]) > 0
    vout = vin_ctx["vout"][vin["n"]]

    return vout["value"], vout["script_pub_key"], is_segwit


def get_transaction_sources(decoded_tx, block_index):
    sources = []
    outputs_value = 0

    for vin in decoded_tx["vin"][:]:  # Loop through inputs.
        vout_value, script_pubkey, _is_segwit = get_vin_info(vin)

        outputs_value += vout_value

        asm = script.script_to_asm(script_pubkey)

        if asm[-1] == OP_CHECKSIG:  # noqa: F405
            new_source, new_data = decode_checksig(asm, decoded_tx, block_index)
            if new_data or not new_source:
                raise DecodeError("data in source")
        elif asm[-1] == OP_CHECKMULTISIG:  # noqa: F405
            new_source, new_data = decode_checkmultisig(asm, decoded_tx, block_index)
            if new_data or not new_source:
                raise DecodeError("data in source")
        elif asm[0] == OP_HASH160 and asm[-1] == OP_EQUAL and len(asm) == 3:  # noqa: F405
            new_source, new_data = decode_scripthash(asm)
            if new_data or not new_source:
                raise DecodeError("data in source")
        elif util.enabled("segwit_support") and asm[0] == b"":
            # Segwit output
            new_source = script.script_to_address(script_pubkey)
            new_data = None
        else:
            raise DecodeError("unrecognised source type")

        # old; append to sources, results in invalid addresses
        # new; first found source is source, the rest can be anything (to fund the TX for example)
        if not (util.enabled("first_input_is_source") and len(sources)):
            # Collect unique sources.
            if new_source not in sources:
                sources.append(new_source)

    return "-".join(sources), outputs_value


def get_transaction_source_from_p2sh(decoded_tx, p2sh_is_segwit, block_index):
    p2sh_encoding_source = None
    data = b""
    outputs_value = 0

    for vin in decoded_tx["vin"]:
        vout_value, _script_pubkey, is_segwit = get_vin_info(vin)

        if util.enabled("prevout_segwit_fix"):
            prevout_is_segwit = is_segwit
        else:
            prevout_is_segwit = p2sh_is_segwit

        outputs_value += vout_value

        # Ignore transactions with invalid script.
        asm = script.script_to_asm(vin["script_sig"])

        new_source, new_destination, new_data = p2sh_encoding.decode_p2sh_input(
            asm, block_index, p2sh_is_segwit=prevout_is_segwit
        )
        # this could be a p2sh source address with no encoded data
        if new_data is None:
            continue

        if new_source is not None:
            if p2sh_encoding_source is not None and new_source != p2sh_encoding_source:
                # this p2sh data input has a bad source address
                raise DecodeError("inconsistent p2sh inputs")

            p2sh_encoding_source = new_source

        assert not new_destination

        data += new_data

    return p2sh_encoding_source, data, outputs_value


def get_dispensers_outputs(db, potential_dispensers):
    outputs = []
    for destination, btc_amount in potential_dispensers:
        if destination is None or btc_amount is None:
            continue
        if dispenser.is_dispensable(db, destination, btc_amount):
            outputs.append((destination, btc_amount))
    return outputs


def get_dispensers_tx_info(sources, dispensers_outputs, tx_data=None):
    source, destination, btc_amount, fee, data, outs = b"", None, None, None, tx_data, []

    dispenser_source = sources.split("-")[0]
    out_index = 0
    for out in dispensers_outputs:
        if out[0] is None or out[1] is None:
            continue
        if out[0] != dispenser_source:
            source = dispenser_source
            destination = out[0]
            btc_amount = out[1]
            fee = 0
            if data is None:
                data = struct.pack(config.SHORT_TXTYPE_FORMAT, dispenser.DISPENSE_ID)
                data += b"\x00"
                if util.enabled("new_tx_format"):
                    data = b"\x00\x02" + data

            if util.enabled("multiple_dispenses"):
                outs.append({"destination": out[0], "btc_amount": out[1], "out_index": out_index})
            else:
                break  # Prevent inspection of further dispenses (only first one is valid)

        out_index = out_index + 1

    return source, destination, btc_amount, fee, data, outs


def parse_transaction_vouts(decoded_tx, block_index):
    # Get destinations and data outputs.
    destinations, btc_amount, fee, data, potential_dispensers = [], 0, 0, b"", []

    for vout in decoded_tx["vout"]:
        potential_dispensers.append((None, None))
        # Fee is the input values minus output values.
        output_value = vout["value"]
        fee -= output_value

        script_pub_key = vout["script_pub_key"]

        # Ignore transactions with invalid script.
        asm = script.script_to_asm(script_pub_key)
        if asm[0] == OP_RETURN:  # noqa: F405
            new_destination, new_data = decode_opreturn(asm, decoded_tx, block_index)
        elif asm[-1] == OP_CHECKSIG:  # noqa: F405
            new_destination, new_data = decode_checksig(asm, decoded_tx, block_index)
            potential_dispensers[-1] = (new_destination, output_value)
        elif asm[-1] == OP_CHECKMULTISIG:  # noqa: F405
            try:
                new_destination, new_data = decode_checkmultisig(asm, decoded_tx, block_index)
                potential_dispensers[-1] = (new_destination, output_value)
            except script.MultiSigAddressError:
                raise DecodeError("invalid OP_CHECKMULTISIG")  # noqa: B904
        elif (
            util.enabled("p2sh_addresses")
            and asm[0] == OP_HASH160  # noqa: F405
            and asm[-1] == OP_EQUAL  # noqa: F405
            and len(asm) == 3
        ):
            new_destination, new_data = decode_scripthash(asm)
            if util.enabled("p2sh_dispensers_support"):
                potential_dispensers[-1] = (new_destination, output_value)
        elif util.enabled("segwit_support") and asm[0] == b"":
            # Segwit Vout, second param is redeemScript
            # redeemScript = asm[1]
            new_destination = script.script_to_address(script_pub_key)
            new_data = None
            if util.enabled("correct_segwit_txids"):
                potential_dispensers[-1] = (new_destination, output_value)
        else:
            raise DecodeError("unrecognised output type")
        assert not (new_destination and new_data)
        assert (
            new_destination != None or new_data != None  # noqa: E711
        )  # `decode_*()` should never return `None, None`.

        if util.enabled("null_data_check"):
            if new_data == []:
                raise DecodeError("new destination is `None`")

        # All destinations come before all data.
        if (
            not data
            and not new_data
            and destinations
            != [
                config.UNSPENDABLE,
            ]
        ):
            destinations.append(new_destination)
            btc_amount += output_value
        else:
            if new_destination:  # Change.
                break
            else:  # Data.
                data += new_data

    return destinations, btc_amount, fee, data, potential_dispensers


def get_tx_info_new(db, decoded_tx, block_index, p2sh_is_segwit=False, composing=False):
    """Get multisig transaction info.
    The destinations, if they exists, always comes before the data output; the
    change, if it exists, always comes after.
    """
    # Ignore coinbase transactions.
    if decoded_tx["coinbase"]:
        raise DecodeError("coinbase transaction")

    # Get destinations and data outputs.
    if "parsed_vouts" in decoded_tx:
        if isinstance(decoded_tx["parsed_vouts"], Exception):
            raise DecodeError(str(decoded_tx["parsed_vouts"]))
        elif decoded_tx["parsed_vouts"] == "DecodeError":
            raise DecodeError("unrecognised output type")
        destinations, btc_amount, fee, data, potential_dispensers = decoded_tx["parsed_vouts"]
    else:
        logger.trace("parsed_vouts not in decoded_tx")
        destinations, btc_amount, fee, data, potential_dispensers = parse_transaction_vouts(
            decoded_tx, block_index
        )

    if util.enabled("new_tx_format") and data:
        flags = data[0]  # noqa F841
        data = data[1:]

    # source can be determined by parsing the p2sh_data transaction
    #   or from the first spent output
    sources = []
    fee_added = False
    # P2SH encoding signalling
    p2sh_encoding_source = None
    if util.enabled("p2sh_encoding") and data == b"P2SH":
        p2sh_encoding_source, data, outputs_value = get_transaction_source_from_p2sh(
            decoded_tx, p2sh_is_segwit, block_index
        )
        fee += outputs_value
        fee_added = True

    # Only look for source if data were found or destination is `UNSPENDABLE`,
    # for speed.
    dispensers_outputs = []
    if not data and destinations != [
        config.UNSPENDABLE,
    ]:
        if util.enabled("disable_vanilla_btc_dispense", block_index):
            raise BTCOnlyError("no data and not unspendable")

        if util.enabled("dispensers", block_index) and not composing:
            dispensers_outputs = get_dispensers_outputs(db, potential_dispensers)
            if len(dispensers_outputs) == 0:
                raise BTCOnlyError("no data and not unspendable")
        else:
            raise BTCOnlyError("no data and not unspendable")

    # Collect all (unique) source addresses.
    #   if we haven't found them yet
    if p2sh_encoding_source is None:
        sources, outputs_value = get_transaction_sources(decoded_tx, block_index)
        if not fee_added:
            fee += outputs_value
    else:  # use the source from the p2sh data source
        sources = p2sh_encoding_source

    if not data and destinations != [
        config.UNSPENDABLE,
    ]:
        assert util.enabled(
            "dispensers", block_index
        )  # else an exception would have been raised above
        assert len(dispensers_outputs) > 0  # else an exception would have been raised above
        return get_dispensers_tx_info(sources, dispensers_outputs)

    destinations = "-".join(destinations)

    try:
        message_type_ids = [
            message_type_id for message_type_id, _ in message_type.unpack(data, block_index)
        ]
    except struct.error:  # Deterministically raised.
        message_type_ids = [None]

    if dispenser.DISPENSE_ID in message_type_ids and util.enabled(
        "enable_dispense_tx", block_index=block_index
    ):
        # if there is a dispense prefix we assume all potential_dispensers are dispensers
        # that's mean we don't need to call get_dispensers_outputs()
        # and so we avoid a db query (dispenser.is_dispensable()).
        # If one of them is not a dispenser `dispenser.dispense()` will silently skip it
        return get_dispensers_tx_info(sources, potential_dispensers, data)

    return sources, destinations, btc_amount, round(fee), data, []


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
        elif len(asm) == 5 and (
            block_index >= 293000 or config.TESTNET or config.REGTEST
        ):  # Protocol change.
            # Be strict.
            pubkeyhash, address_version = get_pubkeyhash(script_pub_key, block_index)
            if not pubkeyhash:
                continue

            data_pubkey = arc4_decrypt(pubkeyhash, decoded_tx)
            if data_pubkey[1:9] == util.prefix(block_index) or pubkeyhash_encoding:
                pubkeyhash_encoding = True
                data_chunk_length = data_pubkey[0]  # No ord() necessary.
                data_chunk = data_pubkey[1 : data_chunk_length + 1]
                if data_chunk[-8:] == util.prefix(block_index):
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
    elif data[: len(util.prefix(block_index))] == util.prefix(block_index):
        data = data[len(util.prefix(block_index)) :]
    else:
        raise DecodeError("no prefix")

    # Only look for source if data were found or destination is UNSPENDABLE, for speed.
    if not data and destination != config.UNSPENDABLE:
        raise BTCOnlyError("no data and not unspendable")

    # Collect all possible source addresses; ignore coinbase transactions and anything but the simplest Pay‐to‐PubkeyHash inputs.
    source_list = []
    for vin in decoded_tx["vin"][:]:  # Loop through input transactions.
        # Get the full transaction data for this input transaction.
        vout_value, script_pubkey, _is_segwit = get_vin_info(vin)
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


def _get_tx_info(db, decoded_tx, block_index, p2sh_is_segwit=False):
    """Get the transaction info. Calls one of two subfunctions depending on signature type."""
    if not block_index:
        block_index = util.CURRENT_BLOCK_INDEX

    if util.enabled("p2sh_addresses", block_index=block_index):  # Protocol change.
        return get_tx_info_new(
            db,
            decoded_tx,
            block_index,
            p2sh_is_segwit=p2sh_is_segwit,
        )
    elif util.enabled("multisig_addresses", block_index=block_index):  # Protocol change.
        return get_tx_info_new(
            db,
            decoded_tx,
            block_index,
        )
    else:
        return get_tx_info_legacy(decoded_tx, block_index)


def get_utxos_info(db, decoded_tx):
    """
    Get the UTXO move info.
    Returns a list of UTXOs. Last UTXO is the destination, previous UTXOs are the sources.
    """
    sources = []
    # we check that each vin does not contain assets..
    for vin in decoded_tx["vin"]:
        if isinstance(vin["hash"], str):
            vin_hash = vin["hash"]
        else:
            vin_hash = inverse_hash(binascii.hexlify(vin["hash"]).decode("utf-8"))
        utxo = vin_hash + ":" + str(vin["n"])
        utxo_balances = ledger.get_utxo_balances(db, utxo)
        if len(utxo_balances) > 0:
            sources.append(utxo)
    destination = None
    # the destination is the first non-OP_RETURN vout
    for n, vout in enumerate(decoded_tx["vout"]):
        asm = script.script_to_asm(vout["script_pub_key"])
        if asm[0] == OP_RETURN:  # noqa: F405
            continue
        destination = decoded_tx["tx_hash"] + ":" + str(n)
        return sources + [destination]
    return []


def get_tx_info(db, decoded_tx, block_index):
    """Get the transaction info. Returns normalized None data for DecodeError and BTCOnlyError."""
    if util.enabled("utxo_support", block_index=block_index):
        utxos_info = get_utxos_info(db, decoded_tx)
    else:
        utxos_info = []
    try:
        source, destination, btc_amount, fee, data, dispensers_outs = _get_tx_info(
            db, decoded_tx, block_index
        )
        return source, destination, btc_amount, fee, data, dispensers_outs, utxos_info
    except DecodeError as e:  # noqa: F841
        return b"", None, None, None, None, None, utxos_info
    except BTCOnlyError as e:  # noqa: F841
        return b"", None, None, None, None, None, utxos_info
