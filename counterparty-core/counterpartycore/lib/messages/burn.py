#! /usr/bin/python3
import decimal
import logging

D = decimal.Decimal
from fractions import Fraction  # noqa: E402

from counterpartycore.lib import config, database, exceptions, ledger, util  # noqa: E402

logger = logging.getLogger(config.LOGGER_NAME)

f"""Burn {config.BTC} to earn {config.XCP} during a special period of time."""

ID = 60


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

    cursor.execute("""CREATE TABLE IF NOT EXISTS burns(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      burned INTEGER,
                      earned INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)

    database.create_indexes(
        cursor,
        "burns",
        [
            ["status"],
            ["source"],
        ],
    )


def validate(db, source, destination, quantity, block_index, overburn=False):
    problems = []

    # Check destination address.
    if destination != config.UNSPENDABLE:
        problems.append("wrong destination address")

    if not isinstance(quantity, int):
        problems.append("quantity must be in satoshis")
        return problems

    if quantity < 0:
        problems.append("negative quantity")

    # Try to make sure that the burned funds won't go to waste.
    if block_index < config.BURN_START - 1:
        problems.append("too early")
    elif block_index > config.BURN_END:
        problems.append("too late")

    return problems


def compose(db, source: str, quantity: int, overburn: bool = False, no_validate=False):
    cursor = db.cursor()
    destination = config.UNSPENDABLE
    problems = validate(
        db, source, destination, quantity, util.CURRENT_BLOCK_INDEX, overburn=overburn
    )
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    # Check that a maximum of 1 BTC total is burned per address.
    burns = ledger.get_burns(db, source)
    already_burned = sum([burn["burned"] for burn in burns])

    if quantity > (1 * config.UNIT - already_burned) and not overburn:
        raise exceptions.ComposeError(f"1 {config.BTC} may be burned per address")

    cursor.close()
    return (source, [(destination, quantity)], None)


def parse(db, tx, mainnet_burns, message=None):
    burn_parse_cursor = db.cursor()

    if config.TESTNET or config.REGTEST:
        problems = []
        status = "valid"

        if status == "valid":
            problems = validate(
                db,
                tx["source"],
                tx["destination"],
                tx["btc_amount"],
                tx["block_index"],
                overburn=False,
            )
            if problems:
                status = "invalid: " + "; ".join(problems)

            if tx["btc_amount"] != None:  # noqa: E711
                sent = tx["btc_amount"]
            else:
                sent = 0

        if status == "valid":
            # Calculate quantity of XCP earned. (Maximum 1 BTC in total, ever.)
            burns = ledger.get_burns(db, tx["source"])
            already_burned = sum([burn["burned"] for burn in burns])
            one = 1 * config.UNIT
            max_burn = one - already_burned
            if sent > max_burn:
                burned = max_burn  # Exceeded maximum burn; earn what you can.
            else:
                burned = sent

            total_time = config.BURN_END - config.BURN_START
            partial_time = config.BURN_END - tx["block_index"]
            multiplier = 1000 + (500 * Fraction(partial_time, total_time))
            earned = round(burned * multiplier)

            # Credit source address with earned XCP.
            ledger.credit(
                db,
                tx["source"],
                config.XCP,
                earned,
                tx["tx_index"],
                action="burn",
                event=tx["tx_hash"],
            )
        else:
            burned = 0
            earned = 0

        tx_index = tx["tx_index"]
        tx_hash = tx["tx_hash"]
        block_index = tx["block_index"]
        source = tx["source"]

    else:
        # Mainnet burns are hard‐coded.

        try:
            line = mainnet_burns[tx["tx_hash"]]
        except KeyError:
            return

        ledger.credit(
            db,
            line["source"],
            config.XCP,
            int(line["earned"]),
            tx["tx_index"],
            action="burn",
            event=line["tx_hash"],
        )

        tx_index = int(tx["tx_index"])
        tx_hash = line["tx_hash"]
        block_index = int(line["block_index"])
        source = line["source"]
        burned = int(line["burned"])
        earned = int(line["earned"])
        status = "valid"

    # Add parsed transaction to message-type–specific table.
    # TODO: store sent in table
    bindings = {
        "tx_index": tx_index,
        "tx_hash": tx_hash,
        "block_index": block_index,
        "source": source,
        "burned": burned,
        "earned": earned,
        "status": status,
    }
    if "integer overflow" not in status:
        ledger.insert_record(db, "burns", bindings, "BURN")

    logger.info(
        "%(source)s burned %(burned)s BTC for %(earned)s XCP (%(tx_hash)s) [%(status)s]", bindings
    )

    burn_parse_cursor.close()


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
