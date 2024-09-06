"""
Initialise database.

Sieve blockchain for Counterparty transactions, and add them to the database.
"""

import binascii
import csv  # noqa: E402
import decimal
import logging  # noqa: E402
import os
import struct
import time
from datetime import timedelta

from counterpartycore.lib import (  # noqa: E402
    backend,
    check,
    config,
    database,
    exceptions,
    gas,
    ledger,
    log,
    message_type,
    util,
)
from counterpartycore.lib.backend import rsfetcher
from counterpartycore.lib.gettxinfo import get_tx_info  # noqa: E402

from .messages import (  # noqa: E402
    bet,
    broadcast,
    btcpay,
    burn,
    cancel,
    destroy,
    dispense,
    dispenser,
    dividend,
    fairmint,
    fairminter,
    issuance,
    order,
    rps,
    rpsresolve,
    send,
    sweep,
    utxo,
)
from .messages.versions import enhanced_send, mpma  # noqa: E402

D = decimal.Decimal
logger = logging.getLogger(config.LOGGER_NAME)

NUM_PREFETCHER_THREADS = 3

# Order matters for FOREIGN KEY constraints.
TABLES = ["balances", "credits", "debits", "messages"] + [
    "order_match_expirations",
    "order_matches",
    "order_expirations",
    "orders",
    "bet_match_expirations",
    "bet_matches",
    "bet_match_resolutions",
    "bet_expirations",
    "bets",
    "broadcasts",
    "btcpays",
    "burns",
    "cancels",
    "dividends",
    "issuances",
    "sends",
    "rps_match_expirations",
    "rps_expirations",
    "rpsresolves",
    "rps_matches",
    "rps",
    "destructions",
    "assets",
    "addresses",
    "sweeps",
    "dispensers",
    "dispenses",
    "dispenser_refills",
    "fairminters",
    "fairmints",
    "transaction_count",
]

MAINNET_BURNS = {}
CURR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CURR_DIR + "/../mainnet_burns.csv", "r") as f:
    mainnet_burns_reader = csv.DictReader(f)
    for line in mainnet_burns_reader:
        MAINNET_BURNS[line["tx_hash"]] = line


def parse_tx(db, tx):
    util.CURRENT_TX_HASH = tx["tx_hash"]
    """Parse the transaction, return True for success."""
    cursor = db.cursor()

    try:
        with db:
            if "utxos_info" in tx and tx["utxos_info"]:
                utxo.move_assets(db, tx)

            if not tx["source"]:  # utxos move only
                return

            # Only one source and one destination allowed for now.
            if len(tx["source"].split("-")) > 1:
                return
            if tx["destination"]:
                if len(tx["destination"].split("-")) > 1:
                    return

            # Burns.
            if tx["destination"] == config.UNSPENDABLE:
                burn.parse(db, tx, MAINNET_BURNS)
                return

            if len(tx["data"]) > 1:
                try:
                    messages = message_type.unpack(tx["data"], tx["block_index"])
                except (struct.error, TypeError):  # Deterministically raised.
                    messages = [(None, None)]
            else:
                messages = [(None, None)]

            # Protocol change.
            rps_enabled = tx["block_index"] >= 308500 or config.TESTNET or config.REGTEST

            supported = []

            for message_type_id, message in messages:
                supported.append(True)
                if message_type_id == send.ID:
                    send.parse(db, tx, message)
                elif message_type_id == enhanced_send.ID and util.enabled(
                    "enhanced_sends", block_index=tx["block_index"]
                ):
                    enhanced_send.parse(db, tx, message)
                elif message_type_id == mpma.ID and util.enabled(
                    "mpma_sends", block_index=tx["block_index"]
                ):
                    mpma.parse(db, tx, message)
                elif message_type_id == order.ID:
                    order.parse(db, tx, message)
                elif message_type_id == btcpay.ID:
                    btcpay.parse(db, tx, message)
                elif message_type_id == issuance.ID or (
                    util.enabled("issuance_backwards_compatibility", block_index=tx["block_index"])
                    and message_type_id == issuance.LR_ISSUANCE_ID
                ):
                    issuance.parse(db, tx, message, message_type_id)
                elif (
                    message_type_id == issuance.SUBASSET_ID
                    and util.enabled("subassets", block_index=tx["block_index"])
                ) or (
                    util.enabled("issuance_backwards_compatibility", block_index=tx["block_index"])
                    and message_type_id == issuance.LR_SUBASSET_ID
                ):
                    issuance.parse(db, tx, message, message_type_id)
                elif message_type_id == broadcast.ID:
                    broadcast.parse(db, tx, message)
                elif message_type_id == bet.ID:
                    bet.parse(db, tx, message)
                elif message_type_id == dividend.ID:
                    dividend.parse(db, tx, message)
                elif message_type_id == cancel.ID:
                    cancel.parse(db, tx, message)
                elif message_type_id == rps.ID and rps_enabled:
                    rps.parse(db, tx, message)
                elif message_type_id == rpsresolve.ID and rps_enabled:
                    rpsresolve.parse(db, tx, message)
                elif message_type_id == destroy.ID and util.enabled(
                    "destroy_reactivated", block_index=tx["block_index"]
                ):
                    destroy.parse(db, tx, message)
                elif message_type_id == sweep.ID and util.enabled(
                    "sweep_send", block_index=tx["block_index"]
                ):
                    sweep.parse(db, tx, message)
                elif message_type_id == dispenser.ID and util.enabled(
                    "dispensers", block_index=tx["block_index"]
                ):
                    dispenser.parse(db, tx, message)
                elif message_type_id == dispenser.DISPENSE_ID and util.enabled(
                    "dispensers", block_index=tx["block_index"]
                ):
                    dispense.parse(db, tx)
                elif message_type_id == fairminter.ID and util.enabled(
                    "fairminter", block_index=tx["block_index"]
                ):
                    fairminter.parse(db, tx, message)
                elif message_type_id == fairmint.ID and util.enabled(
                    "fairminter", block_index=tx["block_index"]
                ):
                    fairmint.parse(db, tx, message)
                elif message_type_id == utxo.ID and util.enabled(
                    "utxo_support", block_index=tx["block_index"]
                ):
                    utxo.parse(db, tx, message)
                else:
                    supported[-1] = False
            supported = any(supported)

            ledger.add_to_journal(
                db,
                tx["block_index"],
                "parse",
                "transactions",
                "TRANSACTION_PARSED",
                {
                    "tx_index": tx["tx_index"],
                    "tx_hash": tx["tx_hash"],
                    "supported": supported,
                },
            )

            if not supported:
                cursor.execute(
                    """UPDATE transactions \
                                    SET supported=$supported \
                                    WHERE tx_hash=$tx_hash""",
                    {"supported": False, "tx_hash": tx["tx_hash"]},
                )
                if tx["block_index"] != config.MEMPOOL_BLOCK_INDEX:
                    logger.info(
                        f"Unsupported transaction: hash {tx['tx_hash']}; ID: {message_type_id}; data {tx['data']}"
                    )
                cursor.close()
                util.CURRENT_TX_HASH = None
                return False

            # NOTE: for debugging (check asset conservation after every `N` transactions).
            # if not tx['tx_index'] % N:
            #     check.asset_conservation(db)
            util.CURRENT_TX_HASH = None
            return True
    except Exception as e:
        raise exceptions.ParseTransactionError(f"{e}")  # noqa: B904
    finally:
        cursor.close()
        util.CURRENT_TX_HASH = None


def replay_transactions_events(db, transactions):
    cursor = db.cursor()
    for tx in transactions:
        util.CURRENT_TX_HASH = tx["tx_hash"]
        transaction_bindings = {
            "tx_index": tx["tx_index"],
            "tx_hash": tx["tx_hash"],
            "block_index": tx["block_index"],
            "block_hash": tx["block_hash"],
            "block_time": tx["block_time"],
            "source": tx["source"],
            "destination": tx["destination"],
            "btc_amount": tx["btc_amount"],
            "fee": tx["fee"],
            "data": tx["data"],
        }
        ledger.add_to_journal(
            db,
            tx["block_index"],
            "insert",
            "transactions",
            "NEW_TRANSACTION",
            transaction_bindings,
        )
        dispensers_outs = cursor.execute(
            "SELECT * FROM transaction_outputs WHERE tx_index = ? ORDER BY rowid",
            (tx["tx_index"],),
        ).fetchall()
        for next_out in dispensers_outs:
            transaction_outputs_bindings = {
                "tx_index": tx["tx_index"],
                "tx_hash": tx["tx_hash"],
                "block_index": tx["block_index"],
                "out_index": next_out["out_index"],
                "destination": next_out["destination"],
                "btc_amount": next_out["btc_amount"],
            }
            ledger.add_to_journal(
                db,
                tx["block_index"],
                "insert",
                "transaction_outputs",
                "NEW_TRANSACTION_OUTPUT",
                transaction_outputs_bindings,
            )
        util.CURRENT_TX_HASH = None


def parse_block(
    db,
    block_index,
    block_time,
    previous_ledger_hash=None,
    previous_txlist_hash=None,
    previous_messages_hash=None,
    reparsing=False,
):
    """Parse the block, return hash of new ledger, txlist and messages.

    The unused arguments `ledger_hash` and `txlist_hash` are for the test suite.
    """

    # Get block transactions
    cursor = db.cursor()
    cursor.execute(
        """SELECT * FROM transactions \
                      WHERE block_index=$block_index ORDER BY tx_index""",
        {"block_index": block_index},
    )
    transactions = cursor.fetchall()

    # Add manual event to journal because transaction already exists
    if reparsing:
        replay_transactions_events(db, transactions)

    ledger.BLOCK_LEDGER = []
    ledger.BLOCK_JOURNAL = []

    if block_index != config.MEMPOOL_BLOCK_INDEX:
        assert block_index == util.CURRENT_BLOCK_INDEX

    # Expire orders, bets and rps.
    order.expire(db, block_index)
    bet.expire(db, block_index, block_time)
    rps.expire(db, block_index)

    # Close dispensers
    dispenser.close_pending(db, block_index)

    # Fairminters operations
    fairminter.before_block(db, block_index)

    txlist = []
    for tx in transactions:
        try:
            parse_tx(db, tx)
            data = binascii.hexlify(tx["data"]).decode("UTF-8") if tx["data"] else ""
            txlist.append(
                f"{tx['tx_hash']}{tx['source']}{tx['destination']}{tx['btc_amount']}{tx['fee']}{data}"
            )
        except exceptions.ParseTransactionError as e:
            logger.warning(f"ParseTransactionError for tx {tx['tx_hash']}: {e}")
            raise e
            # pass

    # Fairminters operations
    fairminter.after_block(db, block_index)

    if block_index != config.MEMPOOL_BLOCK_INDEX:
        # Calculate consensus hashes.
        new_txlist_hash, found_txlist_hash = check.consensus_hash(
            db, "txlist_hash", previous_txlist_hash, txlist
        )
        new_ledger_hash, found_ledger_hash = check.consensus_hash(
            db, "ledger_hash", previous_ledger_hash, ledger.BLOCK_LEDGER
        )
        new_messages_hash, found_messages_hash = check.consensus_hash(
            db, "messages_hash", previous_messages_hash, ledger.BLOCK_JOURNAL
        )

        update_block_query = """
            UPDATE blocks
            SET 
                txlist_hash=:txlist_hash,
                ledger_hash=:ledger_hash,
                messages_hash=:messages_hash,
                transaction_count=:transaction_count
            WHERE block_index=:block_index
        """
        update_block_bindings = {
            "txlist_hash": new_txlist_hash,
            "ledger_hash": new_ledger_hash,
            "messages_hash": new_messages_hash,
            "transaction_count": len(transactions),
            "block_index": block_index,
        }
        cursor.execute(update_block_query, update_block_bindings)

        # trigger BLOCK_PARSED event
        ledger.add_to_journal(
            db,
            block_index,
            "parse",
            "blocks",
            "BLOCK_PARSED",
            {
                "block_index": block_index,
                "ledger_hash": new_ledger_hash,
                "txlist_hash": new_txlist_hash,
                "messages_hash": new_messages_hash,
                "transaction_count": len(transactions),
            },
        )

        cursor.close()

        return new_ledger_hash, new_txlist_hash, new_messages_hash

    cursor.close()
    return None, None, None


def initialise(db):
    """Initialise data, create and populate the database."""
    logger.info("Initializing database...")
    cursor = db.cursor()

    # Drop views that are going to be recreated
    cursor.execute("DROP VIEW IF EXISTS all_expirations")
    cursor.execute("DROP VIEW IF EXISTS all_holders")

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "index_hash_idx",
            "tx_index_idx",
            "tx_hash_idx",
            "index_index_idx",
            "index_hash_index_idx",
            "address_idx",
            "asset_idx",
            "name_idx",
            "id_idx",
            "addresses_idx",
            "block_index_message_index_idx",
            "asset_longname_idx",
        ],
    )

    # Blocks
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS blocks(
                      block_index INTEGER UNIQUE,
                      block_hash TEXT UNIQUE,
                      block_time INTEGER,
                      ledger_hash TEXT,
                      txlist_hash TEXT,
                      messages_hash TEXT,
                      previous_block_hash TEXT UNIQUE,
                      difficulty INTEGER,
                      transaction_count INTEGER,
                      PRIMARY KEY (block_index, block_hash))
                   """
    )

    # SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS`.
    block_columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(blocks)""")]
    if "ledger_hash" not in block_columns:
        cursor.execute("""ALTER TABLE blocks ADD COLUMN ledger_hash TEXT""")
    if "txlist_hash" not in block_columns:
        cursor.execute("""ALTER TABLE blocks ADD COLUMN txlist_hash TEXT""")
    if "messages_hash" not in block_columns:
        cursor.execute("""ALTER TABLE blocks ADD COLUMN messages_hash TEXT""")
    if "previous_block_hash" not in block_columns:
        cursor.execute("""ALTER TABLE blocks ADD COLUMN previous_block_hash TEXT""")
    if "difficulty" not in block_columns:
        cursor.execute("""ALTER TABLE blocks ADD COLUMN difficulty TEXT""")
    if "transaction_count" not in block_columns:
        logger.info("Adding `transaction_count` column to `blocks` table...")
        cursor.execute("""ALTER TABLE blocks ADD COLUMN transaction_count INTEGER""")
        cursor.execute(
            """
            UPDATE blocks SET 
                transaction_count = (
                       SELECT COUNT(*)
                       FROM transactions
                       WHERE transactions.block_index = blocks.block_index
                )
        """
        )

    database.create_indexes(
        cursor,
        "blocks",
        [
            ["block_index"],
            ["block_index", "block_hash"],
        ],
    )

    # Check that first block in DB is BLOCK_FIRST.
    cursor.execute("""SELECT * from blocks ORDER BY block_index LIMIT 1""")
    blocks = list(cursor)
    if len(blocks):
        if blocks[0]["block_index"] != config.BLOCK_FIRST:
            raise exceptions.DatabaseError(
                f"First block in database is not block {config.BLOCK_FIRST}."
            )

    # Transactions
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS transactions(
                      tx_index INTEGER UNIQUE,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      block_hash TEXT,
                      block_time INTEGER,
                      source TEXT,
                      destination TEXT,
                      btc_amount INTEGER,
                      fee INTEGER,
                      data BLOB,
                      supported BOOL DEFAULT 1,
                      utxos_info TEXT,
                      FOREIGN KEY (block_index, block_hash) REFERENCES blocks(block_index, block_hash),
                      PRIMARY KEY (tx_index, tx_hash, block_index))
                    """
    )

    transactions_columns = [
        column["name"] for column in cursor.execute("""PRAGMA table_info(transactions)""")
    ]
    if "utxos_info" not in transactions_columns:
        cursor.execute("""ALTER TABLE transactions ADD COLUMN utxos_info TEXT""")

    database.create_indexes(
        cursor,
        "transactions",
        [
            ["block_index"],
            ["tx_index"],
            ["tx_hash"],
            ["block_index", "tx_index"],
            ["tx_index", "tx_hash", "block_index"],
            ["source"],
        ],
    )

    # Purge database of blocks, transactions from before BLOCK_FIRST.
    cursor.execute("""DELETE FROM blocks WHERE block_index < ?""", (config.BLOCK_FIRST,))
    cursor.execute("""DELETE FROM transactions WHERE block_index < ?""", (config.BLOCK_FIRST,))

    # (Valid) debits
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS debits(
                      block_index INTEGER,
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER,
                      action TEXT,
                      event TEXT,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index))
                   """
    )

    debits_columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(debits)""")]
    if "tx_index" not in debits_columns:
        cursor.execute("""ALTER TABLE debits ADD COLUMN tx_index INTEGER""")
    if "utxo" not in debits_columns:
        cursor.execute("""ALTER TABLE debits ADD COLUMN utxo TEXT""")
        cursor.execute("""ALTER TABLE debits ADD COLUMN utxo_address TEXT""")

    database.create_indexes(
        cursor,
        "debits",
        [
            ["address"],
            ["asset"],
            ["block_index"],
            ["event"],
            ["action"],
            ["quantity"],
            ["utxo"],
            ["utxo_address"],
        ],
    )

    # (Valid) credits
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS credits(
                      block_index INTEGER,
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER,
                      calling_function TEXT,
                      event TEXT,
                      FOREIGN KEY (block_index) REFERENCES blocks(block_index))
                   """
    )

    credits_columns = [
        column["name"] for column in cursor.execute("""PRAGMA table_info(credits)""")
    ]
    if "tx_index" not in credits_columns:
        cursor.execute("""ALTER TABLE credits ADD COLUMN tx_index INTEGER""")
    if "utxo" not in credits_columns:
        cursor.execute("""ALTER TABLE credits ADD COLUMN utxo TEXT""")
        cursor.execute("""ALTER TABLE credits ADD COLUMN utxo_address TEXT""")

    database.create_indexes(
        cursor,
        "credits",
        [
            ["address"],
            ["asset"],
            ["block_index"],
            ["event"],
            ["calling_function"],
            ["quantity"],
            ["utxo"],
            ["utxo_address"],
        ],
    )

    # Balances
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS balances(
                      address TEXT,
                      asset TEXT,
                      quantity INTEGER)
                   """
    )

    balances_columns = [
        column["name"] for column in cursor.execute("""PRAGMA table_info(balances)""")
    ]
    # TODO: add foreign key constraint
    if "block_index" not in balances_columns:
        cursor.execute("""ALTER TABLE balances ADD COLUMN block_index INTEGER""")
    if "tx_index" not in balances_columns:
        cursor.execute("""ALTER TABLE balances ADD COLUMN tx_index INTEGER""")
    if "utxo" not in balances_columns:
        cursor.execute("""ALTER TABLE balances ADD COLUMN utxo TEXT""")
        cursor.execute("""ALTER TABLE balances ADD COLUMN utxo_address TEXT""")

    database.create_indexes(
        cursor,
        "balances",
        [
            ["address", "asset"],
            ["address"],
            ["asset"],
            ["block_index"],
            ["quantity"],
            ["utxo"],
            ["utxo_address"],
        ],
    )

    # Assets
    # TODO: Store more asset info here?!
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS assets(
                      asset_id TEXT UNIQUE,
                      asset_name TEXT UNIQUE,
                      block_index INTEGER,
                      asset_longname TEXT)
                   """
    )

    database.create_indexes(
        cursor,
        "assets",
        [
            ["asset_name"],
            ["asset_id"],
        ],
    )

    # Add asset_longname for sub-assets
    #   SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS`.
    columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(assets)""")]
    if "asset_longname" not in columns:
        cursor.execute("""ALTER TABLE assets ADD COLUMN asset_longname TEXT""")

    database.create_indexes(
        cursor,
        "assets",
        [
            ["asset_longname"],
        ],
        unique=True,
    )

    cursor.execute("""SELECT * FROM assets WHERE asset_name = ?""", ("BTC",))
    if not list(cursor):
        cursor.execute("""INSERT INTO assets VALUES (?,?,?,?)""", ("0", "BTC", None, None))
        cursor.execute("""INSERT INTO assets VALUES (?,?,?,?)""", ("1", "XCP", None, None))

    # Addresses
    # Leaving this here because in the future this could work for other things besides broadcast
    create_addresses_query = """
        CREATE TABLE IF NOT EXISTS addresses(
            address TEXT,
            options INTEGER,
            block_index INTEGER
        )
    """
    if database.table_exists(cursor, "addresses"):
        # migrate old table
        if database.index_exists(cursor, "addresses", "sqlite_autoindex_addresses_1"):
            database.copy_old_table(cursor, "addresses", create_addresses_query)
    else:
        cursor.execute(create_addresses_query)

    database.create_indexes(
        cursor,
        "addresses",
        [
            ["address"],
        ],
    )

    # Consolidated
    send.initialise(db)
    destroy.initialise(db)
    order.initialise(db)
    btcpay.initialise(db)
    issuance.initialise(db)
    broadcast.initialise(db)
    bet.initialise(db)
    dividend.initialise(db)
    burn.initialise(db)
    cancel.initialise(db)
    rps.initialise(db)
    rpsresolve.initialise(db)
    sweep.initialise(db)
    dispenser.initialise(db)
    fairminter.initialise(db)
    fairmint.initialise(db)

    gas.initialise(db)

    # Messages
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS messages(
                      message_index INTEGER PRIMARY KEY,
                      block_index INTEGER,
                      command TEXT,
                      category TEXT,
                      bindings TEXT,
                      timestamp INTEGER,
                      event TEXT,
                      tx_hash TEXT,
                      event_hash TEXT)
                  """
    )
    columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(messages)""")]
    if "event" not in columns:
        cursor.execute("""ALTER TABLE messages ADD COLUMN event TEXT""")
    if "tx_hash" not in columns:
        cursor.execute("""ALTER TABLE messages ADD COLUMN tx_hash TEXT""")
    if "event_hash" not in columns:
        cursor.execute("""ALTER TABLE messages ADD COLUMN event_hash TEXT""")

    # TODO: FOREIGN KEY (block_index) REFERENCES blocks(block_index) DEFERRABLE INITIALLY DEFERRED)
    database.create_indexes(
        cursor,
        "messages",
        [
            ["block_index"],
            ["block_index", "message_index"],
            ["block_index", "event"],
            ["event"],
            ["tx_hash"],
            ["event_hash"],
        ],
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS transaction_outputs(
                        tx_index,
                        tx_hash TEXT,
                        block_index INTEGER,
                        out_index INTEGER,
                        destination TEXT,
                        btc_amount INTEGER,
                        PRIMARY KEY (tx_hash, out_index),
                        FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """
    )

    # Mempool events
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS mempool(
                      tx_hash TEXT,
                      command TEXT,
                      category TEXT,
                      bindings TEXT,
                      timestamp INTEGER,
                      event TEXT)
                  """
    )
    columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(mempool)""")]
    if "event" not in columns:
        cursor.execute("""ALTER TABLE mempool ADD COLUMN event TEXT""")

    create_views(db)

    # Lock UPDATE on all tables
    for table in TABLES:
        cursor.execute(
            f"""CREATE TRIGGER IF NOT EXISTS block_update_{table}
                           BEFORE UPDATE ON {table} BEGIN
                               SELECT RAISE(FAIL, "UPDATES NOT ALLOWED");
                           END;
                        """
        )
    cursor.close()


def create_views(db):
    cursor = db.cursor()
    # Create Expiration View
    expiration_queries = [
        """
        SELECT 'order' AS type, order_hash AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_order_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM order_expirations
        """,
        """
        SELECT 'order_match' AS type, order_match_id AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_order_match_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM order_match_expirations
        """,
        """
        SELECT 'bet' AS type, bet_hash AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_bet_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM bet_expirations
        """,
        """
        SELECT 'bet_match' AS type, bet_match_id AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_bet_match_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM bet_match_expirations
        """,
        """
        SELECT 'rps' AS type, rps_hash AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_rps_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM rps_expirations
        """,
        """
        SELECT 'rps_match' AS type, rps_match_id AS object_id, block_index,
        CONCAT(CAST(block_index AS VARCAHR), '_rps_match_', CAST(rowid AS VARCAHR)) AS cursor_id
        FROM rps_match_expirations
        """,
    ]
    expiration_query = " UNION ALL ".join(expiration_queries)
    expiration_query = f"CREATE VIEW IF NOT EXISTS all_expirations AS {expiration_query}"
    cursor.execute(expiration_query)

    # Create holders view
    holders_queries = [
        """
        SELECT asset, address, quantity, NULL AS escrow, MAX(rowid) AS rowid,
            CONCAT('balances_', CAST(rowid AS VARCAHR)) AS cursor_id, 'balances' AS holding_type, NULL AS status
        FROM balances
        GROUP BY asset, address
        """,
        """
        SELECT * FROM (
            SELECT give_asset AS asset, source AS address, give_remaining AS quantity, tx_hash AS escrow,
                MAX(rowid) AS rowid, CONCAT('open_order_', CAST(rowid AS VARCAHR)) AS cursor_id,
                'open_order' AS holding_type, status
            FROM orders
            GROUP BY tx_hash
        ) WHERE status = 'open'
        """,
        """
        SELECT * FROM (
            SELECT forward_asset AS asset, tx0_address AS address, forward_quantity AS quantity,
                id AS escrow, MAX(rowid) AS rowid, CONCAT('order_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
                'pending_order_match' AS holding_type, status
            FROM order_matches
            GROUP BY id
        ) WHERE status = 'pending'
        """,
        """
        SELECT * FROM (
            SELECT backward_asset AS asset, tx1_address AS address, backward_quantity AS quantity,
                id AS escrow, MAX(rowid) AS rowid, CONCAT('order_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
                'pending_order_match' AS holding_type, status
            FROM order_matches
            GROUP BY id
        ) WHERE status = 'pending'
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, source AS address, wager_remaining AS quantity,
            tx_hash AS escrow, MAX(rowid) AS rowid, CONCAT('open_bet_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'open_bet' AS holding_type, status
            FROM bets
            GROUP BY tx_hash
        ) WHERE status = 'open'
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, tx0_address AS address, forward_quantity AS quantity,
            id AS escrow, MAX(rowid) AS rowid, CONCAT('bet_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'pending_bet_match' AS holding_type, status
            FROM bet_matches
            GROUP BY id
        ) WHERE status = 'pending'
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, tx1_address AS address, backward_quantity AS quantity,
            id AS escrow, MAX(rowid) AS rowid, CONCAT('bet_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'pending_bet_match' AS holding_type, status
            FROM bet_matches
            GROUP BY id
        ) WHERE status = 'pending'
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, source AS address, wager AS quantity,
            tx_hash AS escrow, MAX(rowid) AS rowid, CONCAT('open_rps_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'open_rps' AS holding_type, status
            FROM rps
            GROUP BY tx_hash
        ) WHERE status = 'open'
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, tx0_address AS address, wager AS quantity,
            id AS escrow, MAX(rowid) AS rowid, CONCAT('rps_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'pending_rps_match' AS holding_type, status
            FROM rps_matches
            GROUP BY id
        ) WHERE status IN ('pending', 'pending and resolved', 'resolved and pending')
        """,
        """
        SELECT * FROM (
            SELECT 'XCP' AS asset, tx1_address AS address, wager AS quantity,
            id AS escrow, MAX(rowid) AS rowid, CONCAT('rps_match_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'pending_rps_match' AS holding_type, status
            FROM rps_matches
            GROUP BY id
        ) WHERE status IN ('pending', 'pending and resolved', 'resolved and pending')
        """,
        """
        SELECT * FROM (
            SELECT asset, source AS address, give_remaining AS quantity,
            tx_hash AS escrow, MAX(rowid) AS rowid, CONCAT('open_dispenser_', CAST(rowid AS VARCAHR)) AS cursor_id,
            'open_dispenser' AS holding_type, status
            FROM dispensers
            GROUP BY source, asset
        ) WHERE status = 0
        """,
    ]
    holder_query = " UNION ALL ".join(holders_queries)
    holder_query = f"CREATE VIEW IF NOT EXISTS all_holders AS {holder_query}"
    cursor.execute(holder_query)

    cursor.close()


def list_tx(db, block_hash, block_index, block_time, tx_hash, tx_index, decoded_tx):
    assert type(tx_hash) == str  # noqa: E721
    util.CURRENT_TX_HASH = tx_hash
    cursor = db.cursor()

    source, destination, btc_amount, fee, data, dispensers_outs, utxos_info = get_tx_info(
        db, decoded_tx, block_index
    )

    # For mempool
    if block_hash is None or block_hash == config.MEMPOOL_BLOCK_HASH:
        block_hash = config.MEMPOOL_BLOCK_HASH
        block_index = config.MEMPOOL_BLOCK_INDEX
    else:
        assert block_index == util.CURRENT_BLOCK_INDEX

    if (source and (data or destination == config.UNSPENDABLE or dispensers_outs)) or len(
        utxos_info
    ) > 1:
        transaction_bindings = {
            "tx_index": tx_index,
            "tx_hash": tx_hash,
            "block_index": block_index,
            "block_hash": block_hash,
            "block_time": block_time,
            "source": source,
            "destination": destination,
            "btc_amount": btc_amount,
            "fee": fee,
            "data": data,
            "utxos_info": " ".join(utxos_info),
        }
        ledger.insert_record(db, "transactions", transaction_bindings, "NEW_TRANSACTION")

        if dispensers_outs:
            for next_out in dispensers_outs:
                transaction_outputs_bindings = {
                    "tx_index": tx_index,
                    "tx_hash": tx_hash,
                    "block_index": block_index,
                    "out_index": next_out["out_index"],
                    "destination": next_out["destination"],
                    "btc_amount": next_out["btc_amount"],
                }
                ledger.insert_record(
                    db,
                    "transaction_outputs",
                    transaction_outputs_bindings,
                    "NEW_TRANSACTION_OUTPUT",
                )

        cursor.close()

        return tx_index + 1
    else:
        pass
    util.CURRENT_TX_HASH = None
    return tx_index


def clean_table_from(cursor, table, block_index):
    logger.debug(f"Rolling back table `{table}`...")
    # internal function, no sql injection here
    cursor.execute(f"""DELETE FROM {table} WHERE block_index >= ?""", (block_index,))  # nosec B608  # noqa: S608


def clean_messages_tables(db, block_index=0):
    # clean all tables except assets' blocks', 'transaction_outputs' and 'transactions'
    block_index = max(block_index, config.BLOCK_FIRST)
    if block_index == config.BLOCK_FIRST:
        rebuild_database(db, include_transactions=False)
    else:
        cursor = db.cursor()
        cursor.execute("""PRAGMA foreign_keys=OFF""")
        for table in TABLES:
            clean_table_from(cursor, table, block_index)
        cursor.execute("""PRAGMA foreign_keys=ON""")


def clean_transactions_tables(cursor, block_index=0):
    # clean all tables except assets' blocks', 'transaction_outputs' and 'transactions'
    cursor.execute("""PRAGMA foreign_keys=OFF""")
    for table in ["transaction_outputs", "transactions", "blocks"]:
        clean_table_from(cursor, table, block_index)
    cursor.execute("""PRAGMA foreign_keys=ON""")


def rebuild_database(db, include_transactions=True):
    cursor = db.cursor()
    cursor.execute("""PRAGMA foreign_keys=OFF""")
    tables_to_clean = list(TABLES)
    if include_transactions:
        tables_to_clean += ["transaction_outputs", "transactions", "blocks"]
    for table in tables_to_clean:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")  # nosec B608
    cursor.execute("""PRAGMA foreign_keys=ON""")
    initialise(db)


def rollback(db, block_index=0):
    block_index = max(block_index, config.BLOCK_FIRST)
    # clean all tables
    step = f"Rolling database back to Block {block_index}..."
    done_message = f"Database rolled back to Block {block_index} ({{}}s)"
    with log.Spinner(step, done_message):
        if block_index == config.BLOCK_FIRST:
            rebuild_database(db)
        else:
            clean_messages_tables(db, block_index=block_index)
            cursor = db.cursor()
            clean_transactions_tables(cursor, block_index=block_index)
            cursor.close()
    util.CURRENT_BLOCK_INDEX = block_index - 1


def generate_progression_message(
    block,
    start_time_block_parse,
    start_time_all_blocks_parse,
    block_parsed_count,
    block_count,
    tx_index=None,
):
    block_parsing_duration = time.time() - start_time_block_parse
    cumulated_duration = time.time() - start_time_all_blocks_parse
    expected_duration = (cumulated_duration / block_parsed_count) * block_count
    remaining_duration = expected_duration - cumulated_duration
    current_block = f"Block {block['block_index']} parsed in {block_parsing_duration:.2f}s"
    blocks_parsed = f"{block_parsed_count}/{block_count} blocks parsed"
    txs_indexed = " - "
    if tx_index is not None:
        txs_indexed = f" - tx_index: {tx_index} - "
    cumulated_duration = timedelta(seconds=int(cumulated_duration))
    expected_duration = timedelta(seconds=int(expected_duration))
    remaining_duration = timedelta(seconds=int(remaining_duration))
    duration = f"{cumulated_duration}/{expected_duration} ({remaining_duration})"
    return f"{current_block} [{blocks_parsed}{txs_indexed}{duration}]"


def reparse(db, block_index=0):
    cursor = db.cursor()
    # clean all tables except assets' blocks', 'transaction_outputs' and 'transactions'
    with log.Spinner(f"Rolling database back to Block {block_index}..."):
        clean_messages_tables(db, block_index=block_index)

    step = "Recalculating consensus hashes..."
    with log.Spinner("Recalculating consensus hashes..."):
        query = """
            UPDATE blocks 
            SET ledger_hash=NULL, txlist_hash=NULL, messages_hash=NULL 
            WHERE block_index >= ?
        """
        cursor.execute(query, (block_index,))

    # reparse blocks
    start_time_all_blocks_parse = time.time()
    block_parsed_count = 0
    count_query = "SELECT COUNT(*) AS cnt FROM blocks WHERE block_index >= ?"
    block_count = cursor.execute(count_query, (block_index,)).fetchone()["cnt"]
    step = f"Reparsing blocks from Block {block_index}..."
    message = ""
    with log.Spinner(step) as spinner:
        cursor.execute(
            """SELECT * FROM blocks WHERE block_index >= ? ORDER BY block_index""",
            (block_index,),
        )
        for block in cursor.fetchall():
            start_time_block_parse = time.time()
            util.CURRENT_BLOCK_INDEX = block["block_index"]
            # Add event manually to journal because block already exists
            ledger.add_to_journal(
                db,
                block["block_index"],
                "insert",
                "blocks",
                "NEW_BLOCK",
                {
                    "block_index": block["block_index"],
                    "block_hash": block["block_hash"],
                    "block_time": block["block_time"],
                    "previous_block_hash": block["previous_block_hash"],
                    "difficulty": block["difficulty"],
                },
            )
            previous_ledger_hash = None
            previous_txlist_hash = None
            previous_messages_hash = None
            if util.CURRENT_BLOCK_INDEX > config.BLOCK_FIRST:
                previous_block = ledger.get_block(db, block["block_index"] - 1)
                previous_ledger_hash = previous_block["ledger_hash"]
                previous_txlist_hash = previous_block["txlist_hash"]
                previous_messages_hash = previous_block["messages_hash"]
            parse_block(
                db,
                block["block_index"],
                block["block_time"],
                previous_ledger_hash=previous_ledger_hash,
                previous_txlist_hash=previous_txlist_hash,
                previous_messages_hash=previous_messages_hash,
                reparsing=True,
            )
            block_parsed_count += 1
            message = generate_progression_message(
                block,
                start_time_block_parse,
                start_time_all_blocks_parse,
                block_parsed_count,
                block_count,
            )
            spinner.set_messsage(message)
            spinner.done_message = str(block_parsed_count) + " blocks reparsed in {:.2f}s."


def get_next_tx_index(db):
    """Return index of next transaction."""
    cursor = db.cursor()
    txes = list(
        cursor.execute(
            """SELECT * FROM transactions WHERE tx_index = (SELECT MAX(tx_index) from transactions)"""
        )
    )
    if txes:
        assert len(txes) == 1
        tx_index = txes[0]["tx_index"] + 1
    else:
        tx_index = 0
    cursor.close()
    return tx_index


def parse_new_block(db, decoded_block, tx_index=None):
    start_time = time.time()

    # increment block index
    util.CURRENT_BLOCK_INDEX += 1

    # get next tx index if not provided
    if tx_index is None:
        tx_index = get_next_tx_index(db)

    if util.CURRENT_BLOCK_INDEX > config.BLOCK_FIRST:
        # get previous block
        previous_block = ledger.get_block(db, util.CURRENT_BLOCK_INDEX - 1)

        # check if reorg is needed
        if decoded_block["hash_prev"] != previous_block["block_hash"]:
            if "height" in decoded_block:
                previous_block_index = decoded_block["height"] - 1
            else:
                previous_block_index = backend.bitcoind.get_block_height(decoded_block["hash_prev"])
            logger.warning("Blockchain reorganization detected at Block %s.", previous_block_index)
            # rollback to the previous block
            rollback(db, block_index=previous_block_index + 1)
            util.CURRENT_BLOCK_INDEX = previous_block_index + 1
            tx_index = get_next_tx_index(db)
    else:
        previous_block = {
            "ledger_hash": None,
            "txlist_hash": None,
            "messages_hash": None,
        }

    if "height" not in decoded_block:
        decoded_block["block_index"] = util.CURRENT_BLOCK_INDEX
    else:
        decoded_block["block_index"] = decoded_block["height"]

    with db:  # ensure all the block or nothing
        logger.info(f"Block {decoded_block['block_index']}", extra={"bold": True})
        # insert block
        block_bindings = {
            "block_index": decoded_block["block_index"],
            "block_hash": decoded_block["block_hash"],
            "block_time": decoded_block["block_time"],
            "previous_block_hash": decoded_block["hash_prev"],
            "difficulty": decoded_block["bits"],
        }
        ledger.insert_record(db, "blocks", block_bindings, "NEW_BLOCK")

        # save transactions
        for transaction in decoded_block["transactions"]:
            tx_index = list_tx(
                db,
                decoded_block["block_hash"],
                decoded_block["block_index"],
                decoded_block["block_time"],
                transaction["tx_hash"],
                tx_index,
                decoded_tx=transaction,
            )
        # Parse the transactions in the block.
        new_ledger_hash, new_txlist_hash, new_messages_hash = parse_block(
            db,
            decoded_block["block_index"],
            decoded_block["block_time"],
            previous_ledger_hash=previous_block["ledger_hash"],
            previous_txlist_hash=previous_block["txlist_hash"],
            previous_messages_hash=previous_block["messages_hash"],
        )

        duration = time.time() - start_time

        log_message = "Block %(block_index)s - Parsing complete. L: %(ledger_hash)s, TX: %(txlist_hash)s, M: %(messages_hash)s (%(duration).2fs)"
        logger.info(
            log_message,
            {
                "block_index": decoded_block["block_index"],
                "ledger_hash": new_ledger_hash,
                "txlist_hash": new_txlist_hash,
                "messages_hash": new_messages_hash,
                "duration": duration,
            },
        )

    return tx_index


def check_database_version(db):
    # Update version if new database.
    if util.CURRENT_BLOCK_INDEX <= config.BLOCK_FIRST:
        database.update_version(db)
        return
    try:
        check.database_version(db)
    except check.DatabaseVersionError as e:
        logger.info(str(e))
        # rollback or reparse the database
        if e.required_action == "rollback":
            rollback(db, block_index=e.from_block_index)
        elif e.required_action == "reparse":
            reparse(db, block_index=e.from_block_index)
        # refresh the current block index
        util.CURRENT_BLOCK_INDEX = ledger.last_db_index(db)
        # update the database version
        database.update_version(db)


def catch_up(db, check_asset_conservation=True):
    # update the current block index
    util.CURRENT_BLOCK_INDEX = ledger.last_db_index(db)
    if util.CURRENT_BLOCK_INDEX == 0:
        logger.info("New database.")
        util.CURRENT_BLOCK_INDEX = config.BLOCK_FIRST - 1

    # Get block count.
    block_count = backend.bitcoind.getblockcount()

    # Wait for bitcoind to catch up at least one block after util.CURRENT_BLOCK_INDEX
    if backend.bitcoind.get_blocks_behind() > 0 and block_count <= util.CURRENT_BLOCK_INDEX:
        backend.bitcoind.wait_for_block(util.CURRENT_BLOCK_INDEX + 1)
        block_count = backend.bitcoind.getblockcount()

    # Get index of last transaction.
    tx_index = get_next_tx_index(db)

    start_time = time.time()
    parsed_blocks = 0
    fetcher = None

    while util.CURRENT_BLOCK_INDEX < block_count:
        # Get block information and transactions
        fetch_time_start = time.time()
        if fetcher is None:
            fetcher = rsfetcher.RSFetcher(util.CURRENT_BLOCK_INDEX + 1)

        decoded_block = fetcher.get_block()
        block_height = decoded_block.get("height")
        fetch_time_end = time.time()
        fetch_duration = fetch_time_end - fetch_time_start
        logger.debug(f"Block {block_height} fetched. ({fetch_duration:.6f}s)")

        # Check for gaps in the blockchain
        assert block_height <= util.CURRENT_BLOCK_INDEX + 1

        # Parse the current block
        tx_index = parse_new_block(db, decoded_block, tx_index=tx_index)

        parsed_blocks += 1
        formatted_duration = util.format_duration(time.time() - start_time)
        logger.debug(
            f"Block {util.CURRENT_BLOCK_INDEX}/{block_count} parsed, for {parsed_blocks} blocks in {formatted_duration}."
        )

        # Refresh block count.
        if util.CURRENT_BLOCK_INDEX == block_count:
            # if bitcoind is catching up, wait for the next block
            if backend.bitcoind.get_blocks_behind() > 0:
                backend.bitcoind.wait_for_block(util.CURRENT_BLOCK_INDEX + 1)
            block_count = backend.bitcoind.getblockcount()

    if fetcher is not None:
        fetcher.stop()

    if config.CHECK_ASSET_CONSERVATION and check_asset_conservation:
        # TODO: timer to check asset conservation every N hours
        check.asset_conservation(db)
        # catch up new blocks during asset conservation check
        catch_up(db, check_asset_conservation=False)

    logger.info("Catch up complete.")
