#
# file: counterpartycore/lib/api/migrations/0004.create_and_populate_assets_info.py
#
import logging
import os
import time

from counterpartycore.lib import config
from yoyo import step

logger = logging.getLogger(config.LOGGER_NAME)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

__depends__ = {"0003.create_and_populate_all_expirations"}


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def apply(db):
    start_time = time.time()
    logger.debug("Populating the `assets_info` table...")
    db.row_factory = dict_factory

    db.execute("ATTACH DATABASE ? AS ledger_db", (config.DATABASE,))

    db.execute("""
        CREATE TABLE assets_info(
            asset TEXT UNIQUE,
            asset_id TEXT UNIQUE,
            asset_longname TEXT,
            issuer TEXT,
            owner TEXT,
            divisible BOOL,
            locked BOOL DEFAULT 0,
            supply INTEGER DEFAULT 0,
            description TEXT,
            description_locked BOOL DEFAULT 0,
            first_issuance_block_index INTEGER,
            last_issuance_block_index INTEGER,
            confirmed BOOLEAN DEFAULT TRUE
    )""")

    sql = """
    INSERT INTO assets_info 
    SELECT 
        asset,
        asset_id,
        asset_longname,
        issuer,
        owner,
        divisible,
        locked,
        supply,
        description,
        description_locked,
        first_issuance_block_index,
        last_issuance_block_index,
        confirmed
    FROM (
        SELECT
            asset,
            ledger_db.assets.asset_id,
            ledger_db.assets.asset_longname,
            (
                SELECT issuer
                FROM ledger_db.issuances AS issuances2
                WHERE ledger_db.assets.asset_name = issuances2.asset
                ORDER BY issuances2.rowid ASC
                LIMIT 1
            ) AS issuer,
            issuer AS owner,
            divisible,
            SUM(locked) AS locked,
            SUM(quantity) AS supply,
            description,
            SUM(description_locked) AS description_locked,
            MIN(ledger_db.issuances.block_index) AS first_issuance_block_index,
            MAX(ledger_db.issuances.block_index) AS last_issuance_block_index,
            TRUE AS confirmed,
            MAX(ledger_db.issuances.rowid) AS rowid
        FROM ledger_db.issuances, ledger_db.assets
        WHERE ledger_db.issuances.asset = ledger_db.assets.asset_name
        AND ledger_db.issuances.status = 'valid'
        GROUP BY asset
    );
    """
    cursor = db.cursor()
    cursor.execute(sql)

    db.execute("CREATE INDEX assets_info_asset_idx ON assets_info (asset)")
    db.execute("CREATE INDEX assets_info_asset_longname_idx ON assets_info (asset_longname)")
    db.execute("CREATE INDEX assets_info_issuer_idx ON assets_info (issuer)")
    db.execute("CREATE INDEX assets_info_owner_idx ON assets_info (owner)")

    logger.debug(f"Populated the `assets_info` table in {time.time() - start_time:.2f} seconds")


def rollback(db):
    db.execute("DROP TABLE assets_info")


steps = [step(apply, rollback)]