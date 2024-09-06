#! /usr/bin/python3

"""Destroy a quantity of an asset."""

import logging
import struct

from counterpartycore.lib import config, database, ledger, message_type, script, util
from counterpartycore.lib.exceptions import *  # noqa: F403
from counterpartycore.lib.script import AddressError

logger = logging.getLogger(config.LOGGER_NAME)

FORMAT = ">QQ"
LENGTH = 8 + 8
MAX_TAG_LENGTH = 34
ID = 110


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "status_idx",
            "address_idx",
        ],
    )

    create_destructions_sql = """
        CREATE TABLE IF NOT EXISTS destructions(
            tx_index INTEGER,
            tx_hash TEXT,
            block_index INTEGER,
            source TEXT,
            asset INTEGER,
            quantity INTEGER,
            tag TEXT,
            status TEXT
        )
    """
    cursor.execute(create_destructions_sql)

    if database.has_fk_on(cursor, "destructions", "transactions.tx_index") or database.field_is_pk(
        cursor, "destructions", "tx_index"
    ):
        database.copy_old_table(cursor, "destructions", create_destructions_sql)

    database.create_indexes(
        cursor,
        "destructions",
        [
            ["status"],
            ["source"],
        ],
    )


def pack(db, asset, quantity, tag):
    data = message_type.pack(ID)
    if isinstance(tag, str):
        tag = bytes(tag.encode("utf8"))[0:MAX_TAG_LENGTH]
    elif isinstance(tag, bytes):
        tag = tag[0:MAX_TAG_LENGTH]
    else:
        tag = b""

    data += struct.pack(FORMAT, ledger.get_asset_id(db, asset, util.CURRENT_BLOCK_INDEX), quantity)
    data += tag
    return data


def unpack(db, message, return_dict=False):
    try:
        asset_id, quantity = struct.unpack(FORMAT, message[0:16])
        tag = message[16:]
        asset = ledger.get_asset_name(db, asset_id, util.CURRENT_BLOCK_INDEX)

    except struct.error:
        raise UnpackError("could not unpack")  # noqa: B904, F405

    except AssetIDError:  # noqa: F405
        raise UnpackError("asset id invalid")  # noqa: B904, F405

    if return_dict:
        return {"asset": asset, "quantity": quantity, "tag": tag}
    return asset, quantity, tag


def validate(db, source, destination, asset, quantity):
    try:
        ledger.get_asset_id(db, asset, util.CURRENT_BLOCK_INDEX)
    except AssetError:  # noqa: F405
        raise ValidateError("asset invalid")  # noqa: B904, F405

    try:
        script.validate(source)
    except AddressError:
        raise ValidateError("source address invalid")  # noqa: B904, F405

    if destination:
        raise ValidateError("destination exists")  # noqa: F405

    if asset == config.BTC:
        raise ValidateError(f"cannot destroy {config.BTC}")  # noqa: F405

    if type(quantity) != int:  # noqa: E721
        raise ValidateError("quantity not integer")  # noqa: F405

    if quantity > config.MAX_INT:
        raise ValidateError("integer overflow, quantity too large")  # noqa: F405

    if quantity < 0:
        raise ValidateError("quantity negative")  # noqa: F405

    if ledger.get_balance(db, source, asset) < quantity:
        raise BalanceError("balance insufficient")  # noqa: F405


def compose(db, source: str, asset: str, quantity: int, tag: str, no_validate=False):
    # resolve subassets
    asset = ledger.resolve_subasset_longname(db, asset)

    if not no_validate:
        validate(db, source, None, asset, quantity)
    data = pack(db, asset, quantity, tag)

    return (source, [], data)


def parse(db, tx, message):
    status = "valid"

    asset, quantity, tag = None, None, None

    try:
        asset, quantity, tag = unpack(db, message)
        validate(db, tx["source"], tx["destination"], asset, quantity)
        ledger.debit(db, tx["source"], asset, quantity, tx["tx_index"], "destroy", tx["tx_hash"])

    except UnpackError as e:  # noqa: F405
        status = "invalid: " + "".join(e.args)

    except (ValidateError, BalanceError) as e:  # noqa: F405
        status = "invalid: " + "".join(e.args)

    bindings = {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "asset": asset,
        "quantity": quantity,
        "tag": tag,
        "status": status,
    }
    if "integer overflow" not in status:
        ledger.insert_record(db, "destructions", bindings, "ASSET_DESTRUCTION")

    logger.info(
        "Destroy of %(quantity)s %(asset)s by %(source)s (%(tx_hash)s) [%(status)s]", bindings
    )


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
