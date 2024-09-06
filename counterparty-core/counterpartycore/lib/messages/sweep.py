#! /usr/bin/python3

import logging
import struct

from counterpartycore.lib import (
    address,
    config,
    database,
    exceptions,
    ledger,
    message_type,
    util,
)
from counterpartycore.lib.exceptions import *  # noqa: F403

logger = logging.getLogger(config.LOGGER_NAME)

FORMAT = ">21sB"
LENGTH = 22
MAX_MEMO_LENGTH = 34  # Could be higher, but we will keep it consistent with enhanced send
ID = 4
ANTISPAM_FEE_DECIMAL = 0.5
ANTISPAM_FEE = ANTISPAM_FEE_DECIMAL * config.UNIT

FLAG_BALANCES = 1
FLAG_OWNERSHIP = 2
FLAG_BINARY_MEMO = 4

FLAGS_ALL = FLAG_BINARY_MEMO | FLAG_BALANCES | FLAG_OWNERSHIP


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "source_idx",
            "destination_idx",
            "memo_idx",
        ],
    )

    cursor.execute("""CREATE TABLE IF NOT EXISTS sweeps(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      flags INTEGER,
                      status TEXT,
                      memo BLOB,
                      fee_paid INTEGER,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)

    database.create_indexes(
        cursor,
        "sweeps",
        [
            ["block_index"],
            ["source"],
            ["destination"],
            ["memo"],
        ],
    )


def validate(db, source, destination, flags, memo, block_index):
    problems = []

    if source == destination:
        problems.append("destination cannot be the same as source")

    cursor = db.cursor()

    result = ledger.get_balance(db, source, "XCP")

    antispamfee = util.get_value_by_block_index("sweep_antispam_fee", block_index) * config.UNIT
    total_fee = ANTISPAM_FEE

    if antispamfee > 0:
        balances_count = ledger.get_balances_count(db, source)[0]["cnt"]
        issuances_count = ledger.get_issuances_count(db, source)

        total_fee = int(balances_count * antispamfee * 2 + issuances_count * antispamfee * 4)

        if result < total_fee:
            problems.append(
                f"insufficient XCP balance for sweep. Need {total_fee} XCP for antispam fee"
            )
    else:
        if result < ANTISPAM_FEE:
            problems.append(
                f"insufficient XCP balance for sweep. Need {ANTISPAM_FEE_DECIMAL} XCP for antispam fee"
            )

    cursor.close()

    if flags > FLAGS_ALL:
        problems.append(f"invalid flags {flags}")
    elif not (flags & (FLAG_BALANCES | FLAG_OWNERSHIP)):
        problems.append("must specify which kind of transfer in flags")

    if memo and len(memo) > MAX_MEMO_LENGTH:
        problems.append("memo too long")

    return problems, total_fee


def compose(db, source: str, destination: str, flags: int, memo: str, no_validate=False):
    if memo is None:
        memo = b""
    elif flags & FLAG_BINARY_MEMO:
        memo = bytes.fromhex(memo)
    else:
        memo = memo.encode("utf-8")
        memo = struct.pack(f">{len(memo)}s", memo)

    block_index = util.CURRENT_BLOCK_INDEX
    problems, total_fee = validate(db, source, destination, flags, memo, block_index)
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    short_address_bytes = address.pack(destination)

    data = message_type.pack(ID)
    data += struct.pack(FORMAT, short_address_bytes, flags)
    data += memo

    return (source, [], data)


def unpack(message):
    try:
        memo_bytes_length = len(message) - LENGTH
        if memo_bytes_length < 0:
            raise exceptions.UnpackError("invalid message length")
        if memo_bytes_length > MAX_MEMO_LENGTH:
            raise exceptions.UnpackError("memo too long")

        struct_format = FORMAT + f"{memo_bytes_length}s"
        short_address_bytes, flags, memo_bytes = struct.unpack(struct_format, message)
        if len(memo_bytes) == 0:
            memo_bytes = None
        elif not (flags & FLAG_BINARY_MEMO):
            memo_bytes = memo_bytes.decode("utf-8")

        # unpack address
        full_address = address.unpack(short_address_bytes)
    except struct.error as e:
        logger.warning(f"sweep send unpack error: {e}")
        raise exceptions.UnpackError("could not unpack")  # noqa: B904

    unpacked = {
        "destination": full_address,
        "flags": flags,
        "memo": memo_bytes,
    }
    return unpacked


def parse(db, tx, message):
    cursor = db.cursor()

    fee_paid = round(config.UNIT / 2)

    # Unpack message.
    try:
        unpacked = unpack(message)
        destination, flags, memo_bytes = (
            unpacked["destination"],
            unpacked["flags"],
            unpacked["memo"],
        )

        status = "valid"
    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:
        destination, flags, memo_bytes = None, None, None
        status = f"invalid: could not unpack ({e})"
    except BalanceError:  # noqa: F405
        destination, flags, memo_bytes = None, None, None
        status = "invalid: insufficient balance for antispam fee for sweep"
    except Exception as err:
        destination, flags, memo_bytes = None, None, None
        status = "invalid: could not unpack, " + str(err)

    if status == "valid":
        problems, total_fee = validate(
            db, tx["source"], destination, flags, memo_bytes, tx["block_index"]
        )
        if problems:
            status = "invalid: " + "; ".join(problems)

    if status == "valid":
        try:
            antispamfee = (
                util.get_value_by_block_index("sweep_antispam_fee", tx["block_index"]) * config.UNIT
            )

            if antispamfee > 0:
                ledger.debit(
                    db,
                    tx["source"],
                    "XCP",
                    total_fee,
                    tx["tx_index"],
                    action="sweep fee",
                    event=tx["tx_hash"],
                )
            else:
                ledger.debit(
                    db,
                    tx["source"],
                    "XCP",
                    fee_paid,
                    tx["tx_index"],
                    action="sweep fee",
                    event=tx["tx_hash"],
                )
        except BalanceError:  # noqa: F405
            destination, flags, memo_bytes = None, None, None
            status = "invalid: insufficient balance for antispam fee for sweep"

    if status == "valid":
        balances = ledger.get_address_balances(db, tx["source"])

        if flags & FLAG_BALANCES:
            for balance in balances:
                ledger.debit(
                    db,
                    tx["source"],
                    balance["asset"],
                    balance["quantity"],
                    tx["tx_index"],
                    action="sweep",
                    event=tx["tx_hash"],
                )
                ledger.credit(
                    db,
                    destination,
                    balance["asset"],
                    balance["quantity"],
                    tx["tx_index"],
                    action="sweep",
                    event=tx["tx_hash"],
                )

        if flags & FLAG_OWNERSHIP:
            sweep_pos = 0

            assets_issued = balances
            if util.enabled("zero_balance_ownership_sweep_fix", tx["block_index"]):
                assets_issued = ledger.get_asset_issued(db, tx["source"])

            for next_asset_issued in assets_issued:
                issuances = ledger.get_issuances(
                    db, asset=next_asset_issued["asset"], status="valid", first=True
                )
                if len(issuances) > 0:
                    last_issuance = issuances[-1]
                    if last_issuance["issuer"] == tx["source"]:
                        bindings = {
                            "tx_index": tx["tx_index"],
                            "tx_hash": tx["tx_hash"],
                            "msg_index": sweep_pos,
                            "block_index": tx["block_index"],
                            "asset": next_asset_issued["asset"],
                            "quantity": 0,
                            "divisible": last_issuance["divisible"],
                            "source": last_issuance["source"],
                            "issuer": destination,
                            "transfer": True,
                            "callable": last_issuance["callable"],
                            "call_date": last_issuance["call_date"],
                            "call_price": last_issuance["call_price"],
                            "description": last_issuance["description"],
                            "fee_paid": 0,
                            "locked": last_issuance["locked"],
                            "status": status,
                            "asset_longname": last_issuance["asset_longname"],
                            "reset": False,
                        }
                        ledger.insert_record(db, "issuances", bindings, "ASSET_TRANSFER")
                        sweep_pos += 1

        bindings = {
            "tx_index": tx["tx_index"],
            "tx_hash": tx["tx_hash"],
            "block_index": tx["block_index"],
            "source": tx["source"],
            "destination": destination,
            "flags": flags,
            "status": status,
            "memo": memo_bytes,
            "fee_paid": total_fee if antispamfee > 0 else fee_paid,
        }
        ledger.insert_record(db, "sweeps", bindings, "SWEEP")

        logger.info("Sweep from %(source)s to %(destination)s (%(tx_hash)s) [%(status)s]", bindings)

    cursor.close()
