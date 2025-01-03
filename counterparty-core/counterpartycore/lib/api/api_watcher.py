import json
import logging
import os
import threading
import time

from counterpartycore.lib import config, database, exceptions, util
from counterpartycore.lib.api import dbbuilder
from counterpartycore.lib.util import format_duration

logger = logging.getLogger(config.LOGGER_NAME)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
MIGRATIONS_DIR = os.path.join(CURRENT_DIR, "migrations")

UPDATE_EVENTS_ID_FIELDS = {
    "BLOCK_PARSED": ["block_index"],
    "TRANSACTION_PARSED": ["tx_hash"],
    "BET_MATCH_UPDATE": ["id"],
    "BET_UPDATE": ["tx_hash"],
    "DISPENSER_UPDATE": ["tx_hash"],
    "ORDER_FILLED": ["tx_hash"],
    "ORDER_MATCH_UPDATE": ["id"],
    "ORDER_UPDATE": ["tx_hash"],
    "RPS_MATCH_UPDATE": ["id"],
    "RPS_UPDATE": ["tx_hash"],
    "ADDRESS_OPTIONS_UPDATE": ["address"],
    "FAIRMINTER_UPDATE": ["tx_hash"],
}

EVENTS_ADDRESS_FIELDS = {
    "NEW_TRANSACTION": ["source", "destination"],
    "DEBIT": ["address"],
    "CREDIT": ["address"],
    "ENHANCED_SEND": ["source", "destination"],
    "MPMA_SEND": ["source", "destination"],
    "SEND": ["source", "destination"],
    "ASSET_TRANSFER": ["source", "issuer"],
    "SWEEP": ["source", "destination"],
    "ASSET_DIVIDEND": ["source"],
    "RESET_ISSUANCE": ["source", "issuer"],
    "ASSET_ISSUANCE": ["source", "issuer"],
    "ASSET_DESTRUCTION": ["source"],
    "OPEN_ORDER": ["source"],
    "ORDER_MATCH": ["tx0_address", "tx1_address"],
    "BTC_PAY": ["source", "destination"],
    "CANCEL_ORDER": ["source"],
    "ORDER_EXPIRATION": ["source"],
    "ORDER_MATCH_EXPIRATION": ["tx0_address", "tx1_address"],
    "OPEN_DISPENSER": ["source", "origin", "oracle_address"],
    "DISPENSER_UPDATE": ["source"],
    "REFILL_DISPENSER": ["source", "destination"],
    "DISPENSE": ["source", "destination"],
    "BROADCAST": ["source"],
    "BURN": ["source"],
    "NEW_FAIRMINT": ["source"],
    "NEW_FAIRMINTER": ["source"],
    "ATTACH_TO_UTXO": ["source", "destination"],
    "DETACH_FROM_UTXO": ["source", "destination"],
    "UTXO_MOVE": ["source", "destination"],
}

EXPIRATION_EVENTS_OBJECT_ID = {
    "ORDER_EXPIRATION": "order_hash",
    "ORDER_MATCH_EXPIRATION": "order_match_id",
    "RPS_EXPIRATION": "rps_hash",
    "RPS_MATCH_EXPIRATION": "rps_match_id",
    "BET_EXPIRATION": "bet_hash",
    "BET_MATCH_EXPIRATION": "bet_match_id",
}

ASSET_EVENTS = [
    "ASSET_CREATION",
    "ASSET_ISSUANCE",
    "ASSET_DESTRUCTION",
    "RESET_ISSUANCE",
    "ASSET_TRANSFER",
    "BURN",
]

XCP_DESTROY_EVENTS = [
    "ASSET_ISSUANCE",
    "ASSET_DESTRUCTION",
    "SWEEP",
    "ASSET_DIVIDEND",
]

STATE_DB_TABLES = [
    # consolidated from ledger_db
    "fairminters",
    "balances",
    "addresses",
    "dispensers",
    "bet_matches",
    "bets",
    "order_matches",
    "orders",
    "rps",
    "rps_matches",
    # only in state_db
    "address_events",
    "all_expirations",
    "assets_info",
    "events_count",
]

SKIP_EVENTS = ["NEW_TRANSACTION_OUTPUT"]


def fetch_all(db, query, bindings=None):
    cursor = db.cursor()
    cursor.execute(query, bindings)
    return cursor.fetchall()


def fetch_one(db, query, bindings=None):
    cursor = db.cursor()
    cursor.execute(query, bindings)
    return cursor.fetchone()


def delete_all(db, query, bindings=None):
    cursor = db.cursor()
    cursor.execute(query, bindings)
    changes = fetch_one(db, "SELECT changes() AS deleted")
    return changes["deleted"]


def get_next_event_to_parse(ledger_db, state_db):
    last_parsed_message_index = get_last_parsed_event_index(state_db)
    sql = "SELECT * FROM messages WHERE message_index > ? ORDER BY message_index ASC LIMIT 1"
    next_event = fetch_one(ledger_db, sql, (last_parsed_message_index,))
    return next_event


def get_event_to_parse_count(ledger_db, state_db):
    last_parsed_message_index = get_last_parsed_event_index(state_db)
    sql = "SELECT COUNT(*) AS message_count FROM messages WHERE message_index > ?"
    message_count = fetch_one(ledger_db, sql, (last_parsed_message_index,))
    if message_count is None:
        return 0
    return message_count["message_count"]


def get_event_bindings(event):
    event_bindings = json.loads(event["bindings"])
    if (
        "order_match_id" in event_bindings
        and "id" in event_bindings
        and event_bindings["order_match_id"] == event_bindings["id"]
    ):
        del event_bindings["order_match_id"]
    return event_bindings


def insert_event_to_sql(event):
    event_bindings = get_event_bindings(event)
    event_bindings["block_index"] = event["block_index"]
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
    event_bindings["block_index"] = event["block_index"]

    if event_bindings["block_index"] == config.MEMPOOL_BLOCK_INDEX:
        return None, []

    id_field_names = UPDATE_EVENTS_ID_FIELDS[event["event"]]

    sql_bindings = []
    sets = []
    for key, value in event_bindings.items():
        if key in id_field_names:
            continue
        sets.append(f"{key} = ?")
        sql_bindings.append(value)
    sets_clause = ", ".join(sets)

    where = []
    where_bindings = []
    for id_field_name in id_field_names:
        where.append(f"{id_field_name} = ?")
        sql_bindings.append(event_bindings[id_field_name])
        where_bindings.append(event_bindings[id_field_name])
    where_clause = " AND ".join(where)

    sql = f"UPDATE {event['category']} SET {sets_clause} WHERE {where_clause}"  # noqa: S608

    return sql, sql_bindings


def event_to_sql(event):
    if event["command"] == "insert":
        return insert_event_to_sql(event)
    if event["command"] in ["update", "parse"]:
        return update_event_to_sql(event)
    return None, []


def search_address_from_utxo(state_db, utxo):
    cursor = state_db.cursor()
    sql = "SELECT utxo_address FROM balances WHERE utxo = ? LIMIT 1"
    cursor.execute(sql, (utxo,))
    address = cursor.fetchone()
    if address is not None:
        return address["utxo_address"]
    return None


def update_address_events(state_db, event):
    if event["event"] not in EVENTS_ADDRESS_FIELDS:
        return
    event_bindings = json.loads(event["bindings"])
    cursor = state_db.cursor()
    for field in EVENTS_ADDRESS_FIELDS[event["event"]]:
        if field not in event_bindings:
            continue
        address = event_bindings[field]
        sql = """
            INSERT INTO address_events (address, event_index, block_index)
            VALUES (:address, :event_index, :block_index)
            """
        cursor.execute(
            sql,
            {
                "address": address,
                "event_index": event["message_index"],
                "block_index": event["block_index"],
            },
        )
        if util.is_utxo_format(address):
            utxo_address = search_address_from_utxo(state_db, address)
            if utxo_address is not None:
                cursor.execute(
                    sql,
                    {
                        "address": utxo_address,
                        "event_index": event["message_index"],
                        "block_index": event["block_index"],
                    },
                )


def update_all_expiration(state_db, event):
    if event["event"] not in EXPIRATION_EVENTS_OBJECT_ID:
        return
    event_bindings = json.loads(event["bindings"])

    cursor = state_db.cursor()
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


def update_xcp_supply(state_db, event):
    if event["event"] not in XCP_DESTROY_EVENTS:
        return
    event_bindings = json.loads(event["bindings"])
    if "fee_paid" not in event_bindings:
        return
    if event_bindings["fee_paid"] == 0:
        return
    sql = """
        UPDATE assets_info 
        SET supply = supply - :fee_paid
        WHERE asset = 'XCP'
    """
    cursor = state_db.cursor()
    cursor.execute(sql, event_bindings)


def update_assets_info(state_db, event):
    update_xcp_supply(state_db, event)

    if event["event"] not in ASSET_EVENTS:
        return
    event_bindings = json.loads(event["bindings"])

    if event["event"] == "ASSET_CREATION":
        sql = """
            INSERT OR REPLACE INTO assets_info 
                (asset, asset_id, asset_longname, first_issuance_block_index) 
            VALUES 
                (:asset_name, :asset_id, :asset_longname, :block_index)
            """
        cursor = state_db.cursor()
        cursor.execute(sql, event_bindings)
        return

    if event_bindings["status"] != "valid":
        return

    if event["event"] in ["ASSET_ISSUANCE", "RESET_ISSUANCE"]:
        existing_asset = fetch_one(
            state_db,
            "SELECT * FROM assets_info WHERE asset = :asset",
            {"asset": event_bindings["asset"]},
        )
        if existing_asset is None and "asset_longname" in event_bindings:
            existing_asset = fetch_one(
                state_db,
                "SELECT * FROM assets_info WHERE asset_longname = :asset_longname",
                {"asset_longname": event_bindings["asset_longname"]},
            )

        set_data = []
        set_data.append("divisible = :divisible")
        set_data.append("description = :description")
        set_data.append("owner = :issuer")
        set_data.append("supply = supply + :quantity")
        set_data.append("last_issuance_block_index = :block_index")
        set_data.append("asset_longname = :asset_longname")
        if event_bindings["locked"]:
            set_data.append("locked = :locked")
        if existing_asset is None or not existing_asset["issuer"]:  # first issuance
            set_data.append("issuer = :issuer")
        set_data = ", ".join(set_data)

        sql = f"UPDATE assets_info SET {set_data} WHERE asset = :asset"  # noqa: S608
        cursor = state_db.cursor()
        cursor.execute(sql, event_bindings)
        return

    if event["event"] == "ASSET_DESTRUCTION":
        sql = """
            UPDATE assets_info
            SET supply = supply - :quantity
            WHERE asset = :asset
            """
        cursor = state_db.cursor()
        cursor.execute(sql, event_bindings)
        return

    if event["event"] == "ASSET_TRANSFER":
        sql = """
            UPDATE assets_info 
            SET owner = :issuer
            WHERE asset = :asset
            """
        cursor = state_db.cursor()
        cursor.execute(sql, event_bindings)
        return

    if event["event"] == "BURN":
        sql = """
            UPDATE assets_info 
            SET supply = supply + :earned
            WHERE asset = 'XCP'
            """
        cursor = state_db.cursor()
        cursor.execute(sql, event_bindings)
        return


def get_event_count(state_db, event):
    cursor = state_db.cursor()
    cursor.execute("SELECT count FROM events_count WHERE event = ?", (event["event"],))
    count = cursor.fetchone()
    if count is None:
        return None
    return count["count"]


def update_events_count(state_db, event):
    current_count = get_event_count(state_db, event)
    cursor = state_db.cursor()
    if current_count is None:
        cursor.execute("INSERT INTO events_count (event, count) VALUES (?, 1)", (event["event"],))
    else:
        cursor.execute(
            "UPDATE events_count SET count = count + 1 WHERE event = ?", (event["event"],)
        )


def update_transaction_types_count(state_db, event):
    if event["event"] != "NEW_TRANSACTION":
        return
    cursor = state_db.cursor()
    binding = json.loads(event["bindings"])
    transaction_type = binding.get("transaction_type", "unknown")
    current_count = cursor.execute(
        "SELECT count FROM transaction_types_count WHERE transaction_type = ?", (transaction_type,)
    ).fetchone()
    if current_count is None:
        cursor.execute(
            "INSERT INTO transaction_types_count (transaction_type, count) VALUES (?, 1)",
            (transaction_type,),
        )
    else:
        cursor.execute(
            "UPDATE transaction_types_count SET count = count + 1 WHERE transaction_type = ?",
            (transaction_type,),
        )


def update_balances(state_db, event):
    if event["event"] not in ["DEBIT", "CREDIT"]:
        return

    cursor = state_db.cursor()

    event_bindings = get_event_bindings(event)
    quantity = event_bindings["quantity"]
    if quantity == 0:
        return

    if event["event"] == "DEBIT":
        quantity = -quantity

    field_name = "address"
    address_or_utxo = event_bindings["address"]
    if "utxo" in event_bindings and event_bindings["utxo"]:
        field_name = "utxo"
        address_or_utxo = event_bindings["utxo"]
    event_bindings["address_or_utxo"] = address_or_utxo

    sql = f"SELECT * FROM balances WHERE {field_name} = :address_or_utxo AND asset = :asset"  # noqa: S608
    existing_balance = fetch_one(state_db, sql, event_bindings)

    if existing_balance is not None:
        sql = f"""
            UPDATE balances
            SET quantity = quantity + :quantity
            WHERE {field_name} = :address_or_utxo AND asset = :asset
            """  # noqa: S608
    else:
        sql = f"""
            INSERT INTO balances ({field_name}, asset, quantity, utxo_address)
            VALUES (:address_or_utxo, :asset, :quantity, :utxo_address)
            """  # noqa: S608
    utxo_address = None
    if "utxo_address" in event_bindings:
        utxo_address = event_bindings["utxo_address"]
    insert_bindings = {
        "address_or_utxo": address_or_utxo,
        "asset": event_bindings["asset"],
        "utxo_address": utxo_address,
        "quantity": quantity,
    }
    cursor.execute(sql, insert_bindings)


def update_fairminters(state_db, event):
    if event["event"] != "NEW_FAIRMINT":
        return
    event_bindings = json.loads(event["bindings"])
    if event_bindings["status"] != "valid":
        return
    cursor = state_db.cursor()
    sql = """
        UPDATE fairminters SET
            earned_quantity = COALESCE(earned_quantity, 0) + :earn_quantity,
            commission = COALESCE(commission, 0) + :commission,
            paid_quantity = COALESCE(paid_quantity, 0) + :paid_quantity
        WHERE tx_hash = :fairminter_tx_hash
    """
    cursor.execute(sql, event_bindings)


def update_consolidated_tables(state_db, event):
    if event["category"] in STATE_DB_TABLES:
        cursor = state_db.cursor()
        sql, sql_bindings = event_to_sql(event)
        if sql is not None:
            cursor.execute(sql, sql_bindings)
    # because no event for balance update
    # except DEBIT and CREDIT
    update_balances(state_db, event)
    # update counters not present in the ledger
    update_fairminters(state_db, event)


def update_state_db_tables(state_db, event):
    if event["event"] not in SKIP_EVENTS:
        update_address_events(state_db, event)
        update_all_expiration(state_db, event)
        update_assets_info(state_db, event)
        update_consolidated_tables(state_db, event)


def update_last_parsed_events_cache(state_db, event=None):
    if event is None:
        last_event_parsed = get_last_parsed_event_index(state_db, no_cache=True)
        last_block_parsed = get_last_block_parsed(state_db, no_cache=True)
        database.set_config_value(state_db, "LAST_BLOCK_PARSED", last_block_parsed)
        database.set_config_value(state_db, "LAST_EVENT_PARSED", last_event_parsed)
    else:
        last_event_parsed = event["message_index"]
        last_block_parsed = event["block_index"]
        if event["event"] == "BLOCK_PARSED":
            database.set_config_value(state_db, "LAST_BLOCK_PARSED", last_block_parsed)
        database.set_config_value(state_db, "LAST_EVENT_PARSED", last_event_parsed)


def update_last_parsed_events(state_db, event):
    sql = """
    INSERT INTO parsed_events (event_index, event, event_hash, block_index)
    VALUES (:message_index, :event, :event_hash, :block_index)
    """
    cursor = state_db.cursor()
    cursor.execute(sql, event)
    update_last_parsed_events_cache(state_db, event)


def get_last_parsed_event_index(state_db, no_cache=False):
    if not no_cache:
        event_index = database.get_config_value(state_db, "LAST_EVENT_PARSED")
        if event_index is not None:
            return int(event_index)
    cursor = state_db.cursor()
    cursor.execute("SELECT event_index FROM parsed_events ORDER BY event_index DESC LIMIT 1")
    parsed_event = cursor.fetchone()
    if parsed_event:
        return parsed_event["event_index"]
    return 0


def get_last_block_parsed(state_db, no_cache=False):
    if not no_cache:
        block_index = database.get_config_value(state_db, "LAST_BLOCK_PARSED")
        if block_index is not None:
            return int(block_index)
    cursor = state_db.cursor()
    cursor.execute(
        "SELECT block_index FROM parsed_events WHERE event = 'BLOCK_PARSED' ORDER BY event_index DESC LIMIT 1"
    )
    parsed_event = cursor.fetchone()
    if parsed_event:
        return parsed_event["block_index"]
    return 0


def parse_event(state_db, event):
    with state_db:
        logger.trace(f"Parsing event: {event}")
        update_state_db_tables(state_db, event)
        update_last_parsed_events(state_db, event)
        update_events_count(state_db, event)
        update_transaction_types_count(state_db, event)
        logger.event(f"Event parsed: {event['message_index']} {event['event']}")


def catch_up(ledger_db, state_db, watcher=None):
    check_reorg(ledger_db, state_db)
    event_to_parse_count = get_event_to_parse_count(ledger_db, state_db)
    if event_to_parse_count > 0:
        logger.debug(f"{event_to_parse_count} events to catch up...")
        start_time = time.time()
        event_parsed = 0
        next_event = get_next_event_to_parse(ledger_db, state_db)
        while next_event and not watcher.stop_event.is_set():
            parse_event(state_db, next_event)
            event_parsed += 1
            if event_parsed % 50000 == 0:
                duration = time.time() - start_time
                logger.debug(
                    f"{event_parsed} / {event_to_parse_count} events parsed. ({format_duration(duration)})"
                )
            next_event = get_next_event_to_parse(ledger_db, state_db)
        if not watcher.stop_event.is_set():
            duration = time.time() - start_time
            logger.info(f"Catch up completed. ({format_duration(duration)})")
    else:
        logger.info("Catch up completed.")


def search_matching_event(ledger_db, state_db):
    state_db_cursor = state_db.cursor()
    state_db_cursor.execute(
        "SELECT * FROM parsed_events WHERE event = 'BLOCK_PARSED' ORDER BY event_index DESC LIMIT -1 OFFSET 1"
    )
    matching_event = None
    for parsed_event in state_db_cursor:
        ledger_event = fetch_one(
            ledger_db,
            "SELECT * FROM messages WHERE message_index = ?",
            (parsed_event["event_index"],),
        )
        if ledger_event is None:
            continue
        if parsed_event["event_hash"] == ledger_event["event_hash"]:
            matching_event = parsed_event
            break
    state_db_cursor.close()
    return matching_event


def check_reorg(ledger_db, state_db):
    last_event_parsed = fetch_one(
        state_db,
        "SELECT * FROM parsed_events WHERE event = 'BLOCK_PARSED' ORDER BY event_index DESC LIMIT 1 OFFSET 1",
    )
    if last_event_parsed is None:
        return
    ledger_event = fetch_one(
        ledger_db,
        "SELECT * FROM messages WHERE message_index = ?",
        (last_event_parsed["event_index"],),
    )
    if ledger_event is None or last_event_parsed["event_hash"] != ledger_event["event_hash"]:
        matching_event = search_matching_event(ledger_db, state_db)
        target_block_index = 0
        if matching_event is not None:
            target_block_index = matching_event["block_index"] + 1
        logger.warning(f"Blockchain reorganization detected at Block {target_block_index}")
        logger.info(f"Rolling back to block: {target_block_index}")
        dbbuilder.rollback_state_db(state_db, block_index=target_block_index)


def parse_next_event(ledger_db, state_db):
    next_event = get_next_event_to_parse(ledger_db, state_db)

    if next_event is None:
        raise exceptions.NoEventToParse("No event to parse")

    parse_event(state_db, next_event)


class APIWatcher(threading.Thread):
    def __init__(self, state_db):
        threading.Thread.__init__(self, name="Watcher")
        logger.debug("Initializing API Watcher...")
        self.state_db = None
        self.ledger_db = None
        self.stop_event = threading.Event()  # Add stop event
        self.state_db = state_db
        self.ledger_db = database.get_db_connection(
            config.DATABASE, read_only=True, check_wal=False
        )
        update_last_parsed_events_cache(self.state_db, event=None)

    def run(self):
        logger.info("Starting API Watcher thread...")
        catch_up(self.ledger_db, self.state_db, self)
        if not self.stop_event.is_set():
            self.follow()

    def follow(self):
        try:
            no_check_reorg_since = 0
            while not self.stop_event.is_set():
                try:
                    parse_next_event(self.ledger_db, self.state_db)
                except exceptions.NoEventToParse:
                    logger.trace("No new events to parse")
                    if time.time() - no_check_reorg_since > 5:
                        check_reorg(self.ledger_db, self.state_db)
                        no_check_reorg_since = time.time()
                    self.stop_event.wait(timeout=0.1)
                if self.stop_event.is_set():
                    break
        finally:
            logger.warning("Closing API Watcher db...")
            if self.state_db is not None:
                self.state_db.close()
            if self.ledger_db is not None:
                self.ledger_db.close()

    def stop(self):
        logger.info("Stopping API Watcher thread...")
        self.stop_event.set()
        self.join()
        logger.info("API Watcher thread stopped.")
