#! /usr/bin/python3

"""Create and parse 'send'-type messages."""

import logging
import struct

from ... import config, exceptions, ledger, message_type, util
from .. import dispense

logger = logging.getLogger(config.LOGGER_NAME)

FORMAT = ">QQ"
LENGTH = 8 + 8
ID = 0


def unpack(db, message, block_index):
    # Only used for `unpack` API call at the moment.
    try:
        asset_id, quantity = struct.unpack(FORMAT, message)
        asset = ledger.get_asset_name(db, asset_id, block_index)

    except struct.error:
        raise exceptions.UnpackError("could not unpack")  # noqa: B904

    except exceptions.AssetNameError:
        raise exceptions.UnpackError("asset id invalid")  # noqa: B904

    unpacked = {"asset": asset, "quantity": quantity}
    return unpacked


def validate(db, source, destination, asset, quantity, block_index):
    problems = []

    if asset == config.BTC:
        problems.append("cannot send bitcoins")  # Only for parsing.

    if not isinstance(quantity, int):
        problems.append("quantity must be in satoshis")
        return problems

    if quantity < 0:
        problems.append("negative quantity")

    # For SQLite3
    if quantity > config.MAX_INT:
        problems.append("integer overflow")

    if util.enabled("send_destination_required"):  # Protocol change.
        if not destination:
            problems.append("destination is required")

    if util.enabled("options_require_memo"):
        # Check destination address options

        cursor = db.cursor()
        results = ledger.get_addresses(db, address=destination)
        if results:
            result = results[0]
            if result and util.active_options(
                result["options"], config.ADDRESS_OPTION_REQUIRE_MEMO
            ):
                problems.append("destination requires memo")
        cursor.close()

    return problems


def compose_send_btc(db, source: str, destination: str, quantity: int, no_validate=False):
    if not util.enabled("enable_dispense_tx"):
        return (source, [(destination, quantity)], None)
    # try to compose a dispense instead
    try:
        return dispense.compose(db, source, destination, quantity, no_validate)
    except (exceptions.NoDispenserError, exceptions.ComposeError):
        # simple BTC send
        return (source, [(destination, quantity)], None)


def compose(db, source: str, destination: str, asset: str, quantity: int, no_validate=False):
    cursor = db.cursor()

    # Just send BTC?
    if asset == config.BTC:
        return compose_send_btc(db, source, destination, quantity, no_validate)

    # resolve subassets
    asset = ledger.resolve_subasset_longname(db, asset)

    # quantity must be in int satoshi (not float, string, etc)
    if not isinstance(quantity, int):
        raise exceptions.ComposeError("quantity must be an int (in satoshi)")

    if not no_validate:
        # Only for outgoing (incoming will overburn).
        balance = ledger.get_balance(db, source, asset)
        if balance < quantity:
            raise exceptions.ComposeError("insufficient funds")

    block_index = util.CURRENT_BLOCK_INDEX

    problems = validate(db, source, destination, asset, quantity, block_index)
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    asset_id = ledger.get_asset_id(db, asset, block_index)
    data = message_type.pack(ID)
    data += struct.pack(FORMAT, asset_id, quantity)

    cursor.close()
    return (source, [(destination, None)], data)


def parse(db, tx, message):
    cursor = db.cursor()

    # Unpack message.
    try:
        if len(message) != LENGTH:
            raise exceptions.UnpackError
        asset_id, quantity = struct.unpack(FORMAT, message)
        asset = ledger.get_asset_name(db, asset_id, tx["block_index"])
        status = "valid"
    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:  # noqa: F841
        asset, quantity = None, None
        status = "invalid: could not unpack"

    if status == "valid":
        # Oversend
        # doesn't make sense (0 and no balance should be the same) but let's not break the protocol
        try:
            balance = ledger.get_balance(db, tx["source"], asset, raise_error_if_no_balance=True)
            if balance < quantity:
                quantity = min(balance, quantity)
        except exceptions.BalanceError:
            status = "invalid: insufficient funds"

    # For SQLite3
    if quantity:
        quantity = min(quantity, config.MAX_INT)

    if status == "valid":
        problems = validate(db, tx["source"], tx["destination"], asset, quantity, tx["block_index"])
        if problems:
            status = "invalid: " + "; ".join(problems)

    if status == "valid":
        ledger.debit(
            db, tx["source"], asset, quantity, tx["tx_index"], action="send", event=tx["tx_hash"]
        )
        ledger.credit(
            db,
            tx["destination"],
            asset,
            quantity,
            tx["tx_index"],
            action="send",
            event=tx["tx_hash"],
        )

    # Add parsed transaction to message-type–specific table.
    bindings = {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "destination": tx["destination"],
        "asset": asset,
        "quantity": quantity,
        "status": status,
    }
    if "integer overflow" not in status and "quantity must be in satoshis" not in status:
        ledger.insert_record(db, "sends", bindings, "SEND")

    logger.info(
        "Send %(asset)s from %(source)s to %(destination)s (%(tx_hash)s) [%(status)s]", bindings
    )

    cursor.close()
