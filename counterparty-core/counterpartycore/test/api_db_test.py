import tempfile

import pytest

from counterpartycore.lib import config, database
from counterpartycore.test.util_test import CURR_DIR

FIXTURE_SQL_FILE = CURR_DIR + "/fixtures/scenarios/unittest_fixture.sql"
FIXTURE_DB = tempfile.gettempdir() + "/fixtures.unittest_fixture.db"


def compare_balances(api_db, ledger_db):
    # balances
    sql_ledger = (
        "SELECT count(*) AS count FROM (SELECT *, MAX(rowid) FROM balances GROUP BY address, asset)"
    )
    sql_api = "SELECT count(*) AS count FROM balances"
    assert (
        ledger_db.execute(sql_ledger).fetchone()["count"]
        == api_db.execute(sql_api).fetchone()["count"]
    )

    ledger_balances = ledger_db.execute(
        "SELECT *, MAX(rowid) FROM balances GROUP BY address, asset ORDER BY asset, address"
    ).fetchall()
    api_balances = api_db.execute("SELECT * FROM balances ORDER BY asset, address").fetchall()
    assert len(ledger_balances) == len(api_balances)
    for ledger_balance, api_balance in zip(ledger_balances, api_balances):
        assert ledger_balance["address"] == api_balance["address"]
        assert ledger_balance["asset"] == api_balance["asset"]
        assert ledger_balance["quantity"] == api_balance["quantity"]


@pytest.mark.usefixtures("api_server_v2")
def test_api_database():
    print("Testing API database...")
    print(config.DATABASE, config.STATE_DATABASE)
    ledger_db = database.get_db_connection(config.DATABASE, read_only=True, check_wal=False)
    api_db = database.get_db_connection(config.STATE_DATABASE, check_wal=False)

    compare_balances(api_db, ledger_db)

    # orders
    sql_ledger = "SELECT count(*) AS count FROM (SELECT *, MAX(rowid) FROM orders GROUP BY tx_hash)"
    sql_api = "SELECT count(*) AS count FROM orders"
    assert (
        ledger_db.execute(sql_ledger).fetchone()["count"]
        == api_db.execute(sql_api).fetchone()["count"]
    )

    ledger_orders = ledger_db.execute(
        "SELECT *, MAX(rowid) FROM orders GROUP BY tx_hash ORDER BY tx_hash"
    ).fetchall()
    for ledger_order in ledger_orders:
        api_order = api_db.execute(
            "SELECT * FROM orders WHERE tx_hash = ?", (ledger_order["tx_hash"],)
        ).fetchone()
        assert ledger_order["status"] == api_order["status"]
        assert ledger_order["give_asset"] == api_order["give_asset"]
        assert ledger_order["get_asset"] == api_order["get_asset"]
        assert ledger_order["get_remaining"] == api_order["get_remaining"]
        assert ledger_order["give_remaining"] == api_order["give_remaining"]
        assert ledger_order["source"] == api_order["source"]

    # order_matches
    sql_ledger = (
        "SELECT count(*) AS count FROM (SELECT *, MAX(rowid) FROM order_matches GROUP BY id)"
    )
    sql_api = "SELECT count(*) AS count FROM order_matches"
    assert (
        ledger_db.execute(sql_ledger).fetchone()["count"]
        == api_db.execute(sql_api).fetchone()["count"]
    )

    ledger_order_matches = ledger_db.execute(
        "SELECT *, MAX(rowid) FROM order_matches GROUP BY id ORDER BY id"
    ).fetchall()
    api_order_matches = api_db.execute("SELECT * FROM order_matches ORDER BY id").fetchall()
    assert len(ledger_order_matches) == len(api_order_matches)
    for ledger_order_match, api_order_match in zip(ledger_order_matches, api_order_matches):
        assert ledger_order_match["id"] == api_order_match["id"]
        assert ledger_order_match["status"] == api_order_match["status"]
        assert ledger_order_match["tx0_hash"] == api_order_match["tx0_hash"]
        assert ledger_order_match["tx1_hash"] == api_order_match["tx1_hash"]

    # assets_info
    sql_ledger = "SELECT count(*) AS count FROM assets WHERE asset_name NOT IN ('XCP', 'BTC')"
    sql_api = "SELECT count(*) AS count FROM assets_info WHERE asset NOT IN ('XCP', 'BTC')"
    assert (
        ledger_db.execute(sql_ledger).fetchone()["count"]
        == api_db.execute(sql_api).fetchone()["count"]
    )

    ledger_assets_info = ledger_db.execute(
        "SELECT asset_name FROM assets WHERE asset_name NOT IN ('XCP', 'BTC') ORDER BY asset_name"
    ).fetchall()
    api_assets_info = api_db.execute(
        "SELECT asset FROM assets_info WHERE asset NOT IN ('XCP', 'BTC') ORDER BY asset"
    ).fetchall()
    assert len(ledger_assets_info) == len(api_assets_info)
    for ledger_asset_info, api_asset_info in zip(ledger_assets_info, api_assets_info):
        assert ledger_asset_info["asset_name"] == api_asset_info["asset"]
