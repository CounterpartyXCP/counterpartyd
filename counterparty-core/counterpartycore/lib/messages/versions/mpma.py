#! /usr/bin/python3

import binascii  # noqa: F401
import json  # noqa: F401
import logging
import math  # noqa: F401
import struct
from functools import reduce
from itertools import groupby

from bitcoin.core import key  # noqa: F401
from bitstring import ReadError

from counterpartycore.lib import config, exceptions, ledger, message_type, util

from .mpma_util.internals import _decode_mpma_send_decode, _encode_mpma_send

logger = logging.getLogger(config.LOGGER_NAME)

ID = 3  # 0x03 is this specific message type


## expected functions for message version
def unpack(message, block_index):
    try:
        unpacked = _decode_mpma_send_decode(message, block_index)
    except struct.error as e:  # noqa: F841
        raise exceptions.UnpackError("could not unpack")  # noqa: B904
    except (exceptions.AssetNameError, exceptions.AssetIDError) as e:  # noqa: F841
        raise exceptions.UnpackError("invalid asset in mpma send")  # noqa: B904
    except ReadError as e:  # noqa: F841
        raise exceptions.UnpackError("truncated data")  # noqa: B904

    return unpacked


def validate(db, source, asset_dest_quant_list, block_index):
    problems = []

    if len(asset_dest_quant_list) == 0:
        problems.append("send list cannot be empty")

    if len(asset_dest_quant_list) == 1:
        problems.append("send list cannot have only one element")

    if len(asset_dest_quant_list) > 0:
        # Need to manually unpack the tuple to avoid errors on scenarios where no memo is specified
        grpd = groupby([(t[0], t[1]) for t in asset_dest_quant_list])
        lengrps = [len(list(grpr)) for (group, grpr) in grpd]
        cardinality = max(lengrps)
        if cardinality > 1:
            problems.append("cannot specify more than once a destination per asset")

    cursor = db.cursor()
    for t in asset_dest_quant_list:
        # Need to manually unpack the tuple to avoid errors on scenarios where no memo is specified
        asset = t[0]
        destination = t[1]
        quantity = t[2]

        send_memo = None
        if len(t) > 3:
            send_memo = t[3]

        if asset == config.BTC:
            problems.append(f"cannot send {config.BTC} to {destination}")

        if not isinstance(quantity, int):
            problems.append(f"quantities must be an int (in satoshis) for {asset} to {destination}")

        if quantity < 0:
            problems.append(f"negative quantity for {asset} to {destination}")

        if quantity == 0:
            problems.append(f"zero quantity for {asset} to {destination}")

        # For SQLite3
        if quantity > config.MAX_INT:
            problems.append(f"integer overflow for {asset} to {destination}")

        # destination is always required
        if not destination:
            problems.append(f"destination is required for {asset}")

        if util.enabled("options_require_memo"):
            results = ledger.get_addresses(db, address=destination) if destination else None
            if results:
                result = results[0]
                if (
                    result
                    and result["options"] & config.ADDRESS_OPTION_REQUIRE_MEMO
                    and (send_memo is None)
                ):
                    problems.append(f"destination {destination} requires memo")

    cursor.close()

    return problems


def compose(
    db, source: str, asset_dest_quant_list: list, memo: str, memo_is_hex: bool, no_validate=False
):
    cursor = db.cursor()

    out_balances = util.accumulate([(t[0], t[2]) for t in asset_dest_quant_list])
    if not no_validate:
        for asset, quantity in out_balances:
            if util.enabled("mpma_subasset_support"):
                # resolve subassets
                asset = ledger.resolve_subasset_longname(db, asset)  # noqa: PLW2901

            if not isinstance(quantity, int):
                raise exceptions.ComposeError(
                    f"quantities must be an int (in satoshis) for {asset}"
                )

            balance = ledger.get_balance(db, source, asset)
            if balance < quantity:
                raise exceptions.ComposeError(f"insufficient funds for {asset}")

    block_index = util.CURRENT_BLOCK_INDEX

    cursor.close()

    problems = validate(db, source, asset_dest_quant_list, block_index)
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    data = message_type.pack(ID)
    data += _encode_mpma_send(
        db, asset_dest_quant_list, block_index, memo=memo, memo_is_hex=memo_is_hex
    )

    return (source, [], data)


def parse(db, tx, message):
    try:
        unpacked = unpack(message, tx["block_index"])
        status = "valid"
    except struct.error as e:  # noqa: F841
        status = "invalid: truncated message"
    except (exceptions.AssetNameError, exceptions.AssetIDError) as e:  # noqa: F841
        status = "invalid: invalid asset name/id"
    except Exception as e:
        status = f"invalid: couldn't unpack; {e}"

    cursor = db.cursor()

    plain_sends = []
    all_debits = []
    all_credits = []
    if status == "valid":
        for asset_id in unpacked:
            try:
                asset = ledger.get_asset_name(db, asset_id, tx["block_index"])  # noqa: F841
            except exceptions.AssetNameError as e:  # noqa: F841
                status = f"invalid: asset {asset_id} invalid at block index {tx['block_index']}"
                break

            balance = ledger.get_balance(db, tx["source"], asset_id)
            if not balance:
                status = f"invalid: insufficient funds for asset {asset_id}, address {tx['source']} has no balance"
                break

            credits = unpacked[asset_id]

            total_sent = reduce(lambda p, t: p + t[1], credits, 0)

            if balance < total_sent:
                status = f"invalid: insufficient funds for asset {asset_id}, needs {total_sent}"
                break

            if status == "valid":
                plain_sends += map(lambda t: util.py34_tuple_append(asset_id, t), credits)
                all_credits += map(
                    lambda t: {"asset": asset_id, "destination": t[0], "quantity": t[1]}, credits
                )
                all_debits.append({"asset": asset_id, "quantity": total_sent})

    if status == "valid":
        problems = validate(db, tx["source"], plain_sends, tx["block_index"])

        if problems:
            status = "invalid:" + "; ".join(problems)

    if status == "valid":
        for op in all_credits:
            ledger.credit(
                db,
                op["destination"],
                op["asset"],
                op["quantity"],
                tx["tx_index"],
                action="mpma send",
                event=tx["tx_hash"],
            )

        for op in all_debits:
            ledger.debit(
                db,
                tx["source"],
                op["asset"],
                op["quantity"],
                tx["tx_index"],
                action="mpma send",
                event=tx["tx_hash"],
            )

        # Enumeration of the plain sends needs to be deterministic, so we sort them by asset and then by address
        plain_sends = sorted(plain_sends, key=lambda x: "".join([x[0], x[1]]))
        for i, op in enumerate(plain_sends):
            if len(op) > 3:
                memo_bytes = op[3]
            else:
                memo_bytes = None

            bindings = {
                "tx_index": tx["tx_index"],
                "tx_hash": tx["tx_hash"],
                "block_index": tx["block_index"],
                "source": tx["source"],
                "asset": op[0],
                "destination": op[1],
                "quantity": op[2],
                "status": status,
                "memo": memo_bytes,
                "msg_index": i,
            }

            ledger.insert_record(db, "sends", bindings, "MPMA_SEND")

            logger.info(
                "Send (MPMA) %(asset)s from %(source)s to %(destination)s (%(tx_hash)s) [%(status)s]",
                bindings,
            )

    if status != "valid":
        logger.info(
            "Invalid MPMA Send (%(tx_hash)s) [%(status)s]",
            {"tx_hash": tx["tx_hash"], "status": status},
        )

    cursor.close()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
