#! /usr/bin/python3

import binascii
import logging
import struct

from counterpartycore.lib import (  # noqa: F401
    config,
    database,
    exceptions,
    ledger,
    log,
    message_type,
    util,
)

logger = logging.getLogger(config.LOGGER_NAME)

FORMAT = ">32s32s"
LENGTH = 32 + 32
ID = 11


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "source_idx",
            "destination_idx",
        ],
    )

    cursor.execute("""CREATE TABLE IF NOT EXISTS btcpays(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      btc_amount INTEGER,
                      order_match_id TEXT,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)

    database.create_indexes(
        cursor,
        "btcpays",
        [
            ["block_index"],
            ["source"],
            ["destination"],
        ],
    )


def validate(db, source, order_match_id, block_index):
    problems = []
    order_match = None
    order_matches = ledger.get_order_match(db, id=order_match_id)
    if len(order_matches) == 0:
        problems.append(f"no such order match {order_match_id}")
        return None, None, None, None, order_match, problems
    elif len(order_matches) > 1:
        assert False  # noqa: B011
    else:
        order_match = order_matches[0]

        if order_match["status"] == "expired":
            problems.append("order match expired")
        elif order_match["status"] == "completed":
            problems.append("order match completed")
        elif order_match["status"].startswith("invalid"):
            problems.append("order match invalid")
        elif order_match["status"] != "pending":
            raise exceptions.OrderError("unrecognised order match status")

    # Figure out to which address the BTC are being paid.
    # Check that source address is correct.
    if order_match["backward_asset"] == config.BTC:
        if source != order_match["tx1_address"] and not (
            block_index >= 313900 or config.TESTNET or config.REGTEST
        ):  # Protocol change.
            problems.append("incorrect source address")
        destination = order_match["tx0_address"]
        btc_quantity = order_match["backward_quantity"]
        escrowed_asset = order_match["forward_asset"]
        escrowed_quantity = order_match["forward_quantity"]
    elif order_match["forward_asset"] == config.BTC:
        if source != order_match["tx0_address"] and not (
            block_index >= 313900 or config.TESTNET or config.REGTEST
        ):  # Protocol change.
            problems.append("incorrect source address")
        destination = order_match["tx1_address"]
        btc_quantity = order_match["forward_quantity"]
        escrowed_asset = order_match["backward_asset"]
        escrowed_quantity = order_match["backward_quantity"]
    else:
        assert False  # noqa: B011

    return destination, btc_quantity, escrowed_asset, escrowed_quantity, order_match, problems


def compose(db, source: str, order_match_id: str, no_validate=False):
    tx0_hash, tx1_hash = util.parse_id(order_match_id)

    destination, btc_quantity, escrowed_asset, escrowed_quantity, order_match, problems = validate(
        db, source, order_match_id, util.CURRENT_BLOCK_INDEX
    )
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    if not no_validate:
        # Warn if down to the wire.
        time_left = order_match["match_expire_index"] - util.CURRENT_BLOCK_INDEX
        if time_left < 4:
            logger.warning(
                f"Only {time_left} blocks until that order match expires. The payment might not make into the blockchain in time."
            )
        if 10 - time_left < 4:
            logger.warning(f"Order match has only {10 - time_left} confirmation(s).")

    tx0_hash_bytes, tx1_hash_bytes = (
        binascii.unhexlify(bytes(tx0_hash, "utf-8")),
        binascii.unhexlify(bytes(tx1_hash, "utf-8")),
    )
    data = message_type.pack(ID)
    data += struct.pack(FORMAT, tx0_hash_bytes, tx1_hash_bytes)
    return (source, [(destination, btc_quantity)], data)


def unpack(message, return_dict=False):
    try:
        if len(message) != LENGTH:
            raise exceptions.UnpackError
        tx0_hash_bytes, tx1_hash_bytes = struct.unpack(FORMAT, message)
        tx0_hash, tx1_hash = (
            binascii.hexlify(tx0_hash_bytes).decode("utf-8"),
            binascii.hexlify(tx1_hash_bytes).decode("utf-8"),
        )
        order_match_id = util.make_id(tx0_hash, tx1_hash)
        status = "valid"
    except (exceptions.UnpackError, struct.error) as e:  # noqa: F841
        tx0_hash, tx1_hash, order_match_id = None, None, None
        status = "invalid: could not unpack"

    if return_dict:
        return {
            "tx0_hash": tx0_hash,
            "tx1_hash": tx1_hash,
            "order_match_id": order_match_id,
            "status": status,
        }
    return tx0_hash, tx1_hash, order_match_id, status


def parse(db, tx, message):
    cursor = db.cursor()

    # Unpack message.
    tx0_hash, tx1_hash, order_match_id, status = unpack(message)

    if status == "valid":
        destination, btc_quantity, escrowed_asset, escrowed_quantity, order_match, problems = (
            validate(db, tx["source"], order_match_id, tx["block_index"])
        )
        if problems:
            order_match = None  # noqa: F841
            status = "invalid: " + "; ".join(problems)

    if status == "valid":
        # BTC must be paid all at once.
        if tx["btc_amount"] >= btc_quantity:
            # Credit source address for the currency that he bought with the bitcoins.
            ledger.credit(
                db,
                tx["source"],
                escrowed_asset,
                escrowed_quantity,
                tx["tx_index"],
                action="btcpay",
                event=tx["tx_hash"],
            )
            status = "valid"

            # Update order match.
            ledger.update_order_match_status(db, order_match_id, "completed")

            # Update give and get order status as filled if order_match is completed
            if util.enabled("btc_order_filled"):
                order_matches = ledger.get_pending_order_matches(db, tx0_hash, tx1_hash)
                if len(order_matches) == 0:
                    # mark both btc get and give orders as filled when order_match is completed and give or get remaining = 0
                    ledger.mark_order_as_filled(db, tx0_hash, tx1_hash)
                else:
                    # always mark btc get order as filled when order_match is completed and give or get remaining = 0
                    ledger.mark_order_as_filled(db, tx0_hash, tx1_hash, source=tx["destination"])

    # Add parsed transaction to message-type–specific table.
    bindings = {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "destination": tx["destination"],
        "btc_amount": tx["btc_amount"],
        "order_match_id": order_match_id,
        "status": status,
    }
    if "integer overflow" not in status:
        ledger.insert_record(db, "btcpays", bindings, "BTC_PAY")
    logger.info("BTC Pay for order match %(order_match_id)s (%(tx_hash)s) [%(status)s]", bindings)

    cursor.close()
