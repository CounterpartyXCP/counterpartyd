import json
import logging
import os
import time
from threading import Thread

from counterpartycore.lib import config, database
from counterpartycore.lib.api import queries, util

logger = logging.getLogger(config.LOGGER_NAME)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
MIGRATIONS_FILE = os.path.join(CURRENT_DIR, "migrations", "0001.create-api-database.sql")

UPDATE_EVENTS_ID_FIELDS = {
    "BLOCK_PARSED": ["block_index"],
    "TRANSACTION_PARSED": ["tx_index"],
    "BET_MATCH_UPDATE": ["id"],
    "BET_UPDATE": ["tx_hash"],
    "DISPENSER_UPDATE": ["source", "asset"],
    "ORDER_FILLED": ["tx_hash"],
    "ORDER_MATCH_UPDATE": ["id"],
    "ORDER_UPDATE": ["tx_hash"],
    "RPS_MATCH_UPDATE": ["id"],
    "RPS_UPDATE": ["tx_hash"],
}

EXPIRATION_EVENTS_OBJECT_ID = {
    "ORDER_EXPIRATION": "order_hash",
    "ORDER_MATCH_EXPIRATION": "order_match_id",
    "RPS_EXPIRATION": "rps_hash",
    "RPS_MATCH_EXPIRATION": "rps_match_id",
    "BET_EXPIRATION": "bet_hash",
    "BET_MATCH_EXPIRATION": "bet_match_id",
}


def get_last_parsed_message_index(api_db):
    cursor = api_db.cursor()
    sql = "SELECT * FROM messages ORDER BY message_index DESC LIMIT 1"
    cursor.execute(sql)
    last_event = cursor.fetchone()
    last_message_index = -1
    if last_event:
        last_message_index = last_event["message_index"]
    return last_message_index


def get_next_event_to_parse(api_db, ledger_db):
    last_parsed_message_index = get_last_parsed_message_index(api_db)
    cursor = ledger_db.cursor()
    sql = "SELECT * FROM messages WHERE message_index > ? ORDER BY message_index ASC LIMIT 1"
    cursor.execute(sql, (last_parsed_message_index,))
    next_event = cursor.fetchone()
    return next_event


def get_event_to_parse_count(api_db, ledger_db):
    last_parsed_message_index = get_last_parsed_message_index(api_db)
    cursor = ledger_db.cursor()
    sql = "SELECT message_index FROM messages ORDER BY message_index DESC LIMIT 1"
    cursor.execute(sql)
    last_event = cursor.fetchone()
    return last_event["message_index"] - last_parsed_message_index


def get_event_bindings(event):
    event_bindings = json.loads(event["bindings"])
    if "order_match_id" in event_bindings:
        del event_bindings["order_match_id"]
    elif event["category"] == "dispenses" and "btc_amount" in event_bindings:
        del event_bindings["btc_amount"]
    return event_bindings


def insert_event_to_sql(event):
    event_bindings = get_event_bindings(event)
    sql_bindings = []
    sql = f"INSERT INTO {event['category']} "
    names = []
    for key, value in event_bindings.items():
        names.append(key)
        sql_bindings.append(value)
    sql += f"({', '.join(names)}) VALUES ({', '.join(['?' for _ in names])})"
    return sql, sql_bindings


def update_event_to_sql(event):
    event_bindings = get_event_bindings(event)
    sql_bindings = []
    sql = f"UPDATE {event['category']} SET "  # noqa: S608
    id_field_names = UPDATE_EVENTS_ID_FIELDS[event["event"]]
    for key, value in event_bindings.items():
        if key in id_field_names:
            continue
        sql += f"{key} = ?, "
        sql_bindings.append(value)
    sql = sql[:-2]  # remove trailing comma
    sql += " WHERE "
    for id_field_name in id_field_names:
        sql += f"{id_field_name} = ? AND "
        sql_bindings.append(event_bindings[id_field_name])
    sql = sql[:-5]  # remove trailing " AND "
    return sql, sql_bindings


def event_to_sql(event):
    if event["command"] == "insert":
        return insert_event_to_sql(event)
    if event["command"] in ["update", "parse"]:
        return update_event_to_sql(event)
    return None, []


def get_event_previous_state(api_db, event):
    previous_state = None
    if event["command"] in ["update", "parse"]:
        cursor = api_db.cursor()
        id_field_names = UPDATE_EVENTS_ID_FIELDS[event["event"]]
        sql = f"SELECT * FROM {event['category']} WHERE "  # noqa: S608
        for id_field_name in id_field_names:
            sql += f"{id_field_name} = :{id_field_name} AND "
        sql = sql[:-5]  # remove trailing " AND "
        event_bindings = json.loads(event["bindings"])
        cursor.execute(sql, event_bindings)
        previous_state = cursor.fetchone()
    return previous_state


def delete_event(api_db, event):
    bindings = get_event_bindings(event)
    sql = f"DELETE FROM {event['category']} WHERE "  # noqa: S608
    for field_name in bindings:
        sql += f"{field_name} = :{field_name} AND "
    sql = sql[:-5]  # remove trailing " AND "
    cursor = api_db.cursor()
    cursor.execute(sql, bindings)
    changes = cursor.execute("SELECT changes()").fetchone()
    logger.warning(changes)


def insert_event(api_db, event):
    previous_state = get_event_previous_state(api_db, event)
    if previous_state is not None:
        event["previous_state"] = util.to_json(previous_state)
    else:
        event["previous_state"] = None
    sql = """
        INSERT INTO messages 
            (message_index, block_index, event, category, command, bindings, tx_hash, previous_state)
        VALUES (:message_index, :block_index, :event, :category, :command, :bindings, :tx_hash, :previous_state)
    """
    cursor = api_db.cursor()
    cursor.execute(sql, event)


def rollback_event(api_db, event):
    logger.debug(f"Rolling back event: {event}")
    if event["previous_state"] is None or event["previous_state"] == "null":
        delete_event(api_db, event)
        return
    previous_state = json.loads(event["previous_state"])

    sql = f"UPDATE {event['category']} SET "  # noqa: S608
    id_field_names = UPDATE_EVENTS_ID_FIELDS[event["event"]]
    for key in previous_state.keys():
        if key in id_field_names:
            continue
        sql += f"{key} = :{key}, "
    sql = sql[:-2]  # remove trailing comma
    sql += " WHERE "
    for id_field_name in id_field_names:
        sql += f"{id_field_name} = :{id_field_name} AND "
    sql = sql[:-5]  # remove trailing " AND "

    cursor = api_db.cursor()
    cursor.execute(sql, previous_state)

    if event["event"] in ["CREDIT", "DEBIT"]:
        revert_event = event.copy()
        revert_event["event"] = "DEBIT" if event["event"] == "CREDIT" else "CREDIT"
        update_balances(api_db, revert_event)


def rollback_events(api_db, block_index):
    logger.info(f"Rolling back events to block {block_index}...")
    with api_db:
        cursor = api_db.cursor()
        sql = "SELECT * FROM messages WHERE block_index >= ? ORDER BY message_index DESC"
        cursor.execute(sql, (block_index,))
        events = cursor.fetchall()
        for event in events:
            rollback_event(api_db, event)
        cursor.execute("DELETE FROM messages WHERE block_index >= ?", (block_index,))


def update_balances(api_db, event):
    if event["event"] not in ["DEBIT", "CREDIT"]:
        return

    cursor = api_db.cursor()

    event_bindings = get_event_bindings(event)
    quantity = event_bindings["quantity"]
    if event["event"] == "DEBIT":
        quantity = -quantity

    existing_balance = cursor.execute(
        "SELECT * FROM balances WHERE address = :address AND asset = :asset",
        event_bindings,
    ).fetchone()

    if existing_balance is None:
        sql = """
            UPDATE balances
            SET quantity = quantity + :quantity
            WHERE address = :address AND asset = :asset
            """
    else:
        sql = """
            INSERT INTO balances (address, asset, quantity)
            VALUES (:address, :asset, :quantity)
            """
    insert_bindings = {
        "address": event_bindings["address"],
        "asset": event_bindings["asset"],
        "quantity": quantity,
    }
    cursor.execute(sql, insert_bindings)


def update_expiration(api_db, event):
    if event["event"] not in EXPIRATION_EVENTS_OBJECT_ID:
        return
    event_bindings = json.loads(event["bindings"])

    cursor = api_db.cursor()
    sql = """
        INSERT INTO all_expirations (object_id, block_index, type) 
        VALUES (:object_id, :block_index, :type)
        """
    bindings = {
        "object_id": event_bindings[EXPIRATION_EVENTS_OBJECT_ID[event["event"]]],
        "block_index": event_bindings["block_index"],
        "type": event["event"].replace("_EXPIRATION", "").lower(),
    }
    cursor.execute(sql, bindings)


def execute_event(api_db, event):
    sql, sql_bindings = event_to_sql(event)
    if sql is not None:
        cursor = api_db.cursor()
        cursor.execute(sql, sql_bindings)
        if event["command"] == "insert":
            cursor.execute("SELECT last_insert_rowid() AS rowid")
            return cursor.fetchone()["rowid"]
    return None


def parse_event(api_db, event):
    with api_db:
        event["insert_rowid"] = execute_event(api_db, event)
        update_balances(api_db, event)
        update_expiration(api_db, event)
        insert_event(api_db, event)
        logger.trace(f"Event parsed: {event['message_index']} {event['event']}")


def catch_up(api_db, ledger_db):
    event_to_parse_count = get_event_to_parse_count(api_db, ledger_db)
    if event_to_parse_count > 0:
        logger.info(f"{event_to_parse_count} events to catch up...")
        start_time = time.time()
        event_parsed = 0
        next_event = get_next_event_to_parse(api_db, ledger_db)
        while next_event:
            logger.trace(f"Parsing event: {next_event}")
            parse_event(api_db, next_event)
            event_parsed += 1
            if event_parsed % 10000 == 0:
                duration = time.time() - start_time
                expected_duration = duration / event_parsed * event_to_parse_count
                logger.info(
                    f"{event_parsed}/{event_to_parse_count} events parsed in {duration:.2f} seconds (expected {expected_duration:.2f} seconds)"
                )
            next_event = get_next_event_to_parse(api_db, ledger_db)
        duration = time.time() - start_time
        logger.info(f"{event_parsed} events parsed in {duration:.2f} seconds")


def initialize_api_db(api_db, ledger_db):
    logger.info("Initializing API Database...")

    cursor = api_db.cursor()

    # TODO: use migrations library
    with open(MIGRATIONS_FILE, "r") as f:
        sql = f.read()
        cursor.execute(sql)

    # Create XCP and BTC assets if they don't exist
    cursor.execute("""SELECT * FROM assets WHERE asset_name = ?""", ("BTC",))
    if not list(cursor):
        cursor.execute("""INSERT INTO assets VALUES (?,?,?,?)""", ("0", "BTC", None, None))
        cursor.execute("""INSERT INTO assets VALUES (?,?,?,?)""", ("1", "XCP", None, None))
    cursor.close()

    # check if rollback is needed
    last_ledger_block = queries.get_last_block(ledger_db)
    if last_ledger_block is not None:
        last_ledger_block = last_ledger_block.result
    last_api_block = queries.get_last_block(api_db)
    if last_api_block is not None:
        last_api_block = last_api_block.result
    if last_api_block is None and last_ledger_block is None:
        return
    elif last_api_block is None and last_ledger_block is not None:
        catch_up(api_db, ledger_db)
    elif last_ledger_block is None and last_api_block is not None:
        rollback_events(api_db, 0)
    elif last_api_block["block_index"] > last_ledger_block["block_index"]:
        rollback_events(api_db, last_ledger_block["block_index"])
    else:
        catch_up(api_db, ledger_db)


class APIWatcher(Thread):
    def __init__(self):
        logger.debug("Initializing API Watcher...")
        self.stopping = False
        self.stopped = False
        self.api_db = database.get_db_connection(
            config.API_DATABASE, read_only=False, check_wal=False
        )
        self.ledger_db = database.get_db_connection(
            config.DATABASE, read_only=True, check_wal=False
        )

        initialize_api_db(self.api_db, self.ledger_db)

        Thread.__init__(self)

    def run(self):
        logger.info("Starting API Watcher...")
        while True and not self.stopping:
            next_event = get_next_event_to_parse(self.api_db, self.ledger_db)
            if next_event:
                last_block = queries.get_last_block(self.api_db).result
                if last_block and last_block["block_index"] > next_event["block_index"]:
                    logger.warning(
                        "Reorg detected, rolling back events to block %s...",
                        next_event["block_index"],
                    )
                    rollback_events(self.api_db, next_event["block_index"])
                logger.debug(f"API Watcher - Parsing event: {next_event}")
                parse_event(self.api_db, next_event)
            else:
                logger.debug("No new events to parse")
                time.sleep(1)
        self.stopped = True
        return

    def stop(self):
        logger.info("Stopping API Watcher...")
        self.stopping = True
        while not self.stopped:
            time.sleep(0.1)
        self.api_db.close()
        self.ledger_db.close()
        logger.trace("API Watcher stopped")
