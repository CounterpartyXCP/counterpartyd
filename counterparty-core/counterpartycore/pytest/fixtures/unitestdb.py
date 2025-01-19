import os

from counterpartycore.lib import config
from counterpartycore.lib.api import composer
from counterpartycore.lib.ledger.currentstate import CurrentState
from counterpartycore.lib.utils import database

from .params import DP
from .scenarios import UNITTEST_FIXTURE


def buid_unitest_db(bitcoind_mock):
    config.DATABASE = "/tmp/counterparty.testnet.db"  # noqa S108
    config.UNSPENDABLE = DP["unspendable"]
    config.NETWORK_NAME = "testnet"
    config.BURN_START = DP["burn_start"]
    config.BURN_END = DP["burn_end"]
    config.BLOCK_FIRST = 0
    config.TESTNET = True
    config.TESTNET4 = True
    config.REGTEST = False
    config.DB_CONNECTION_POOL_SIZE = 1
    config.UTXO_LOCKS_MAX_AGE = 1
    config.UTXO_LOCKS_MAX_ADDRESSES = 1000
    config.PREFIX = b"TESTXXXX"

    if os.path.exists(config.DATABASE):
        os.unlink(config.DATABASE)
    db = database.get_db_connection(config.DATABASE, read_only=False)
    db.close()

    database.apply_outstanding_migration(config.DATABASE, config.LEDGER_DB_MIGRATIONS_DIR)
    db = database.get_db_connection(config.DATABASE, read_only=False)

    CurrentState().set_current_block_index(DP["default_block_index"])

    for tx_params in UNITTEST_FIXTURE[0:1]:
        name, params, construct_params = tx_params
        tx = composer.compose_transaction(db, name, params, construct_params)
        assert "rawtransaction" in tx
        bitcoind_mock.sendrawtransaction(db, tx["rawtransaction"])

    return db
