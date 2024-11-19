#
# file: counterpartycore/lib/api/migrations/0006.create_and_populate_consolidated_tables.py
#
import logging
import time

from counterpartycore.lib import config
from yoyo import step

logger = logging.getLogger(config.LOGGER_NAME)

__depends__ = {"0005.create_and_populate_events_count"}

CONSOLIDATED_TABLES = {
    "fairminters": "tx_hash",
    "balances": "address, asset",
    "addresses": "address",
    "dispensers": "source, asset",
    "bet_matches": "id",
    "bets": "tx_hash",
    "order_matches": "id",
    "orders": "tx_hash",
    "rps": "tx_hash",
    "rps_matches": "id",
}

ADDITONAL_COLUMNS = {
    "fairminters": [
        "earned_quantity INTEGER",
        "paid_quantity INTEGER",
        "commission INTEGER",
    ]
}

POST_QUERIES = {
    "fairminters": [
        """
        UPDATE fairminters SET 
            earned_quantity = (
                SELECT SUM(earn_quantity) 
                FROM fairmints 
                WHERE fairmints.fairminter_tx_hash = fairminters.tx_hash
            ),
            paid_quantity = (
                SELECT SUM(paid_quantity) 
                FROM fairmints 
                WHERE fairmints.fairminter_tx_hash = fairminters.tx_hash
            ),
            commission = (
                SELECT SUM(commission) 
                FROM fairmints 
                WHERE fairmints.fairminter_tx_hash = fairminters.tx_hash
            );
        """
    ]
}


def build_consolidated_table(state_db, table_name):
    logger.debug(f"Copying the consolidated table `{table_name}` to State DB...")
    start_time = time.time()

    # recreate table
    sqls = []
    indexes = []
    for sql in state_db.execute(f"""
        SELECT sql, type FROM ledger_db.sqlite_master 
        WHERE tbl_name='{table_name}'
        AND type != 'trigger'
    """).fetchall():  # noqa S608
        if sql["type"] == "index":
            indexes.append(sql["sql"])
        else:
            sqls.append(sql["sql"])

    for sql in sqls:
        state_db.execute(sql)

    columns = [column["name"] for column in state_db.execute(f"PRAGMA table_info({table_name})")]
    select_fields = ", ".join(columns)

    sql = f"""
        INSERT INTO {table_name} 
            SELECT {select_fields} FROM (
                SELECT *, MAX(rowid) as rowid FROM ledger_db.{table_name}
                GROUP BY {CONSOLIDATED_TABLES[table_name]}
            )
    """  # noqa S608
    state_db.execute(sql)

    # add additional columns
    if table_name in ADDITONAL_COLUMNS:
        for column in ADDITONAL_COLUMNS[table_name]:
            state_db.execute(f"""
                ALTER TABLE {table_name} ADD COLUMN {column}
            """)

    if table_name in POST_QUERIES:
        for post_query in POST_QUERIES[table_name]:
            state_db.execute(post_query)

    for sql_index in indexes:
        state_db.execute(sql_index)
    logger.debug(f"Copied consolidated table `{table_name}` in {time.time() - start_time:.2f} seconds")


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def apply(db):
    db.row_factory = dict_factory

    logger.debug("Copying consolidated tables from ledger db...")

    db.execute("""PRAGMA foreign_keys=OFF""")
    db.execute("ATTACH DATABASE ? AS ledger_db", (config.DATABASE,))

    for table in CONSOLIDATED_TABLES.keys():
        build_consolidated_table(db, table)

    db.execute("""PRAGMA foreign_keys=ON""")


def rollback(db):
    for table in CONSOLIDATED_TABLES.keys():
        db.execute(f"DROP TABLE {table}")


steps = [step(apply, rollback)]