#! /usr/bin/python3

"""Pay out dividends."""

import decimal
import struct

D = decimal.Decimal
import logging  # noqa: E402

from counterpartycore.lib import (  # noqa: E402
    config,
    database,
    exceptions,
    ledger,
    message_type,
    util,
)

logger = logging.getLogger(config.LOGGER_NAME)

FORMAT_1 = ">QQ"
LENGTH_1 = 8 + 8
FORMAT_2 = ">QQQ"
LENGTH_2 = 8 + 8 + 8
ID = 50


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "source_idx",
            "asset_idx",
        ],
    )

    cursor.execute("""CREATE TABLE IF NOT EXISTS dividends(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      asset TEXT,
                      dividend_asset TEXT,
                      quantity_per_unit INTEGER,
                      fee_paid INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)

    database.create_indexes(
        cursor,
        "dividends",
        [
            ["block_index"],
            ["source"],
            ["asset"],
        ],
    )


def validate(db, source, quantity_per_unit, asset, dividend_asset, block_index):
    cursor = db.cursor()
    problems = []

    if asset == config.BTC:
        problems.append(f"cannot pay dividends to holders of {config.BTC}")
    if asset == config.XCP:
        if (
            (not block_index >= 317500) or block_index >= 320000 or config.TESTNET or config.REGTEST
        ):  # Protocol change.
            problems.append(f"cannot pay dividends to holders of {config.XCP}")

    if quantity_per_unit <= 0:
        problems.append("non‐positive quantity per unit")

    # For SQLite3
    if quantity_per_unit > config.MAX_INT:
        problems.append("integer overflow")

    # Examine asset.
    try:
        divisible = ledger.is_divisible(db, asset)
    except exceptions.AssetError:
        problems.append(f"no such asset, {asset}.")
        return None, None, problems, 0

    # Only issuer can pay dividends.
    if block_index >= 320000 or config.TESTNET or config.REGTEST:  # Protocol change.
        issuer = ledger.get_asset_issuer(db, asset)

        if issuer != source:
            problems.append("only issuer can pay dividends")

    # Examine dividend asset.
    try:
        dividend_divisible = ledger.is_divisible(db, dividend_asset)
    except exceptions.AssetError:
        problems.append(f"no such dividend asset, {dividend_asset}.")
        return None, None, problems, 0

    # Calculate dividend quantities.
    exclude_empty = False
    if util.enabled("zero_quantity_value_adjustment_1"):
        exclude_empty = True
    holders = ledger.holders(db, asset, exclude_empty)

    outputs = []
    addresses = []
    dividend_total = 0
    for holder in holders:
        if block_index < 294500 and not (config.TESTNET or config.REGTEST):  # Protocol change.
            if holder["escrow"]:
                continue

        address = holder["address"]
        address_quantity = holder["address_quantity"]

        if block_index >= 296000 or config.TESTNET or config.REGTEST:  # Protocol change.
            if address == source:
                continue

        dividend_quantity = address_quantity * quantity_per_unit

        if divisible:
            dividend_quantity /= config.UNIT
        if not util.enabled("nondivisible_dividend_fix") and not dividend_divisible:
            dividend_quantity /= config.UNIT  # Pre-fix behaviour

        if dividend_asset == config.BTC and dividend_quantity < config.DEFAULT_MULTISIG_DUST_SIZE:
            continue  # A bit hackish.
        dividend_quantity = int(dividend_quantity)

        outputs.append(
            {
                "address": address,
                "address_quantity": address_quantity,
                "dividend_quantity": dividend_quantity,
            }
        )
        addresses.append(address)
        dividend_total += dividend_quantity

    if not dividend_total:
        problems.append("zero dividend")

    if dividend_asset != config.BTC:
        dividend_balances = ledger.get_balance(db, source, dividend_asset)
        if dividend_balances < dividend_total:
            problems.append(f"insufficient funds ({dividend_asset})")

    fee = 0
    if not problems and dividend_asset != config.BTC:
        holder_count = len(set(addresses))
        if block_index >= 330000 or config.TESTNET or config.REGTEST:  # Protocol change.
            fee = int(0.0002 * config.UNIT * holder_count)
        if fee:
            balance = ledger.get_balance(db, source, config.XCP)
            if balance < fee:
                problems.append(f"insufficient funds ({config.XCP})")

    if not problems and dividend_asset == config.XCP:
        total_cost = dividend_total + fee
        if dividend_balances < total_cost:
            problems.append(f"insufficient funds ({dividend_asset})")

    # For SQLite3
    if fee > config.MAX_INT or dividend_total > config.MAX_INT:
        problems.append("integer overflow")

    cursor.close()

    if len(problems):
        return None, None, problems, 0

    # preserve order with old queries
    # TODO: remove and update checkpoints
    if not config.TESTNET and block_index in [313590, 313594]:
        outputs.append(outputs.pop(-3))

    return dividend_total, outputs, problems, fee


def compose(
    db, source: str, quantity_per_unit: int, asset: str, dividend_asset: str, no_validate=False
):
    # resolve subassets
    asset = ledger.resolve_subasset_longname(db, asset)
    dividend_asset = ledger.resolve_subasset_longname(db, dividend_asset)

    dividend_total, outputs, problems, fee = validate(
        db, source, quantity_per_unit, asset, dividend_asset, util.CURRENT_BLOCK_INDEX
    )
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)
    logger.info(
        f"Total quantity to be distributed in dividends: {ledger.value_out(db, dividend_total, dividend_asset)} {dividend_asset}"
    )

    if dividend_asset == config.BTC:
        return (
            source,
            [(output["address"], output["dividend_quantity"]) for output in outputs],
            None,
        )

    asset_id = ledger.get_asset_id(db, asset, util.CURRENT_BLOCK_INDEX)
    dividend_asset_id = ledger.get_asset_id(db, dividend_asset, util.CURRENT_BLOCK_INDEX)
    data = message_type.pack(ID)
    data += struct.pack(FORMAT_2, quantity_per_unit, asset_id, dividend_asset_id)
    return (source, [], data)


def unpack(db, message, block_index, return_dict=False):
    try:
        if (block_index > 288150 or config.TESTNET or config.REGTEST) and len(message) == LENGTH_2:
            quantity_per_unit, asset_id, dividend_asset_id = struct.unpack(FORMAT_2, message)
            asset = ledger.get_asset_name(db, asset_id, block_index)
            dividend_asset = ledger.get_asset_name(db, dividend_asset_id, block_index)
            status = "valid"
        elif len(message) == LENGTH_1:
            quantity_per_unit, asset_id = struct.unpack(FORMAT_1, message)
            asset = ledger.get_asset_name(db, asset_id, block_index)
            dividend_asset = config.XCP
            status = "valid"
        else:
            raise exceptions.UnpackError
    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:  # noqa: F841
        dividend_asset, quantity_per_unit, asset = None, None, None
        status = "invalid: could not unpack"

    if return_dict:
        return {
            "asset": asset,
            "quantity_per_unit": quantity_per_unit,
            "dividend_asset": dividend_asset,
            "status": status,
        }
    return asset, quantity_per_unit, dividend_asset, status


def parse(db, tx, message):
    dividend_parse_cursor = db.cursor()

    fee = 0

    # Unpack message.
    asset, quantity_per_unit, dividend_asset, status = unpack(db, message, tx["block_index"])

    if dividend_asset == config.BTC:
        status = f"invalid: cannot pay {config.BTC} dividends within protocol"

    if status == "valid":
        # For SQLite3
        quantity_per_unit = min(quantity_per_unit, config.MAX_INT)

        dividend_total, outputs, problems, fee = validate(
            db,
            tx["source"],
            quantity_per_unit,
            asset,
            dividend_asset,
            block_index=tx["block_index"],
        )
        if problems:
            status = "invalid: " + "; ".join(problems)

    if status == "valid":
        # Debit.
        ledger.debit(
            db,
            tx["source"],
            dividend_asset,
            dividend_total,
            tx["tx_index"],
            action="dividend",
            event=tx["tx_hash"],
        )
        if tx["block_index"] >= 330000 or config.TESTNET or config.REGTEST:  # Protocol change.
            ledger.debit(
                db,
                tx["source"],
                config.XCP,
                fee,
                tx["tx_index"],
                action="dividend fee",
                event=tx["tx_hash"],
            )

        # Credit.
        for output in outputs:
            if not util.enabled("dont_credit_zero_dividend") or output["dividend_quantity"] > 0:
                ledger.credit(
                    db,
                    output["address"],
                    dividend_asset,
                    output["dividend_quantity"],
                    tx["tx_index"],
                    action="dividend",
                    event=tx["tx_hash"],
                )

    # Add parsed transaction to message-type–specific table.
    bindings = {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "asset": asset,
        "dividend_asset": dividend_asset,
        "quantity_per_unit": quantity_per_unit,
        "fee_paid": fee,
        "status": status,
    }

    if "integer overflow" not in status:
        ledger.insert_record(db, "dividends", bindings, "ASSET_DIVIDEND")

    logger.info(
        "Dividend of %(quantity_per_unit)s %(dividend_asset)s per unit of %(asset)s (%(tx_hash)s) [%(status)s]",
        bindings,
    )

    dividend_parse_cursor.close()
