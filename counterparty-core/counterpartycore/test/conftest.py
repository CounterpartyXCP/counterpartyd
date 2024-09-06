"""
Test suite configuration
"""

import argparse
import binascii
import json
import logging
import os
import time
from datetime import datetime

import apsw
import bitcoin as bitcoinlib
import pycoin
import pytest
import requests
from Crypto.Cipher import ARC4
from pycoin.coins.bitcoin import Tx  # noqa: F401

from counterpartycore import server
from counterpartycore.lib import arc4, config, database, ledger, log, script, util
from counterpartycore.lib.api import api_server as api_v2
from counterpartycore.lib.api import api_v1 as api
from counterpartycore.test import util_test
from counterpartycore.test.fixtures.params import DEFAULT_PARAMS
from counterpartycore.test.fixtures.scenarios import INTEGRATION_SCENARIOS
from counterpartycore.test.fixtures.vectors import UNITTEST_VECTOR

logger = logging.getLogger(config.LOGGER_NAME)

# used to increment RPC port between test modules to avoid conflicts
TEST_RPC_PORT = 9999

# we swap out util.enabled with a custom one which has the option to mock the protocol changes
MOCK_PROTOCOL_CHANGES = {
    "bytespersigop": False,  # default to False to avoid all old vectors breaking
}
MOCK_PROTOCOL_CHANGES_AT_BLOCK = {
    "subassets": {
        "block_index": 310495,
        "allow_always_latest": True,
    },  # override to be true only at block 310495
    "short_tx_type_id": {
        "block_index": DEFAULT_PARAMS["default_block_index"] + 1,
        "allow_always_latest": False,
    },  # override to be true only at block 310502
    "enhanced_sends": {
        "block_index": 310999,
        "allow_always_latest": False,
    },  # override to be true only at block 310999
    "issuance_lock_fix": {
        "block_index": DEFAULT_PARAMS["default_block_index"] + 1,
        "allow_always_latest": False,
    },  # override to be true only at block 310502
    "segwit_support": {
        "block_index": 0,
        "allow_always_latest": False,
    },  # override to be true only at block 310999,
    "dispensers": {"block_index": 0, "allow_always_latest": True},
    "multisig_addresses": {
        "block_index": DEFAULT_PARAMS["default_block_index"] + 1,
        "allow_always_latest": True,
    },
}
DISABLE_ALL_MOCK_PROTOCOL_CHANGES_AT_BLOCK = (
    False  # if true, never look at MOCK_PROTOCOL_CHANGES_AT_BLOCK
)
ENABLE_MOCK_PROTOCOL_CHANGES_AT_BLOCK = (
    False  # if true, always check MOCK_PROTOCOL_CHANGES_AT_BLOCK
)
ALWAYS_LATEST_PROTOCOL_CHANGES = False  # Even when this is true, this can be overridden if allow_always_latest is False in MOCK_PROTOCOL_CHANGES_AT_BLOCK
_enabled = util.enabled


def enabled(change_name, block_index=None):
    # if explicitly set
    if change_name in MOCK_PROTOCOL_CHANGES:
        return MOCK_PROTOCOL_CHANGES[change_name]

    # enable some protocol changes at a specific block for testing
    if shouldCheckForMockProtocolChangesAtBlock(change_name):
        _block_index = block_index
        if _block_index is None:
            _block_index = util.CURRENT_BLOCK_INDEX
        if _block_index >= MOCK_PROTOCOL_CHANGES_AT_BLOCK[change_name]["block_index"]:
            return True
        return False

    # used to force unit tests to always run against latest protocol changes
    if ALWAYS_LATEST_PROTOCOL_CHANGES:
        # KeyError to mimic real util.enabled
        if change_name not in util.PROTOCOL_CHANGES:
            raise KeyError(change_name)

        # print(f"ALWAYS_LATEST_PROTOCOL_CHANGES {change_name} {block_index or util.CURRENT_BLOCK_INDEX} enabled: True")
        return True
    else:
        # print(f"ALWAYS_LATEST_PROTOCOL_CHANGES {change_name} {block_index or util.CURRENT_BLOCK_INDEX} enabled: {_enabled(change_name, block_index)}")
        return _enabled(change_name, block_index)


util.enabled = enabled


# This is true if ENABLE_MOCK_PROTOCOL_CHANGES_AT_BLOCK is set
def shouldCheckForMockProtocolChangesAtBlock(change_name):
    if DISABLE_ALL_MOCK_PROTOCOL_CHANGES_AT_BLOCK:
        return False
    if change_name not in MOCK_PROTOCOL_CHANGES_AT_BLOCK:
        return False
    if ENABLE_MOCK_PROTOCOL_CHANGES_AT_BLOCK:
        return True
    if (
        "allow_always_latest" in MOCK_PROTOCOL_CHANGES_AT_BLOCK[change_name]
        and not MOCK_PROTOCOL_CHANGES_AT_BLOCK[change_name]["allow_always_latest"]
    ):
        return True
    return False


RANDOM_ASSET_INT = None
_generate_random_asset = util.generate_random_asset


def generate_random_asset():
    if RANDOM_ASSET_INT is None:
        return _generate_random_asset()
    else:
        return "A" + str(RANDOM_ASSET_INT)


util.generate_random_asset = generate_random_asset

DISABLE_ARC4_MOCKING = False


def pytest_generate_tests(metafunc):
    """Generate all py.test cases. Checks for different types of tests and creates proper context."""
    if metafunc.function.__name__ == "test_vector":
        args = util_test.vector_to_args(
            UNITTEST_VECTOR, metafunc.config.getoption("function"), metafunc.config
        )
        metafunc.parametrize(
            "tx_name, method, inputs, outputs, error, records, comment, mock_protocol_changes, config_context, pytest_config",
            args,
        )
    elif metafunc.function.__name__ == "test_scenario":
        args = []
        for scenario_name in INTEGRATION_SCENARIOS:
            if metafunc.config.getoption(
                "scenario"
            ) == [] or scenario_name in metafunc.config.getoption("scenario"):
                args.append(
                    (
                        scenario_name,
                        INTEGRATION_SCENARIOS[scenario_name][1],
                        INTEGRATION_SCENARIOS[scenario_name][0],
                        metafunc.config,
                    )
                )
        metafunc.parametrize("scenario_name, base_scenario_name, transactions, pytest_config", args)
    elif metafunc.function.__name__ == "test_book":
        metafunc.parametrize("skip", [not metafunc.config.getoption("testbook")])
    elif metafunc.function.__name__ == "test_compare_hashes":
        metafunc.parametrize("skip", [not metafunc.config.getoption("comparehashes")])
    elif metafunc.function.__name__ == "test_mainnet_api_db":
        metafunc.parametrize("skip", [not metafunc.config.getoption("testapidb")])


def pytest_addoption(parser):
    """Add useful test suite argument options."""
    parser.addoption("--function", action="append", default=[], help="List of functions to test")
    parser.addoption("--scenario", action="append", default=[], help="List of scenarios to test")
    parser.addoption(
        "--gentxhex",
        action="store_true",
        default=False,
        help="Generate and print unsigned hex for *.compose() tests",
    )
    parser.addoption(
        "--savescenarios",
        action="store_true",
        default=False,
        help="Generate sql dump and log in .new files",
    )
    parser.addoption("--alternative", action="store_true", default=False)
    parser.addoption(
        "--testbook", action="store_true", default=False, help="Include testnet test book"
    )
    parser.addoption(
        "--saveapifixtures",
        action="store_true",
        default=False,
        help="Generate api v2 fixtures for tests",
    )
    parser.addoption(
        "--comparehashes",
        action="store_true",
        default=False,
        help="Compare last block hashes with v9 version",
    )
    parser.addoption(
        "--testapidb",
        action="store_true",
        default=False,
        help="Compare balances from Ledger DB and API DB",
    )


@pytest.fixture(scope="function")
def rawtransactions_db(request):
    """Return a database object."""
    db = apsw.Connection(":memory:")
    util_test.initialise_rawtransactions_db(db)

    return db


@pytest.fixture(scope="function")
def server_db(request, cp_server, api_server):
    """Enable database access for unit test vectors."""
    db = database.get_connection(read_only=False)
    cursor = db.cursor()
    cursor.execute("""BEGIN""")
    util_test.reset_current_block_index(db)

    request.addfinalizer(lambda: cursor.execute("""ROLLBACK"""))
    request.addfinalizer(lambda: util_test.reset_current_block_index(db))

    return db


@pytest.fixture(scope="module")
def api_server(request, cp_server):
    """
    api_server fixture, for each module we bind it to a different port because we're unable to kill it
    also `server_db` will inject itself into APIServer for each function
    """

    global TEST_RPC_PORT  # noqa: PLW0603

    config.RPC_PORT = TEST_RPC_PORT = TEST_RPC_PORT + 1
    server.configure_rpc(config.RPC_PASSWORD)

    print("api_server", config.DATABASE, config.API_DATABASE)

    # start RPC server and wait for server to be ready
    api_server = api.APIServer()
    api_server.daemon = True
    api_server.start()
    for attempt in range(5000):  # wait until server is ready.
        if api_server.is_ready:
            time.sleep(0.5)  # extra time window
            break
        elif attempt == 4999:
            raise Exception("Timeout: RPC server not ready after 5s")
        else:
            time.sleep(
                0.001
            )  # attempt to query the current block_index if possible (scenarios start with empty DB so it's not always possible)

    return api_server


@pytest.fixture(scope="module")
def api_server_v2(request, cp_server):
    default_config = {
        "testnet": False,
        "testcoin": False,
        "regtest": False,
        "api_limit_rows": 1000,
        "backend_connect": None,
        "backend_port": None,
        "backend_user": None,
        "backend_password": None,
        "indexd_connect": None,
        "indexd_port": None,
        "backend_ssl": False,
        "backend_ssl_no_verify": False,
        "backend_poll_interval": None,
        "rpc_host": None,
        "rpc_user": None,
        "rpc_password": None,
        "rpc_no_allow_cors": False,
        "api_host": "localhost",
        "api_user": "rpc",
        "api_password": None,
        "api_no_allow_cors": False,
        "force": False,
        "requests_timeout": config.DEFAULT_REQUESTS_TIMEOUT,
        "rpc_batch_size": config.DEFAULT_RPC_BATCH_SIZE,
        "check_asset_conservation": False,
        "backend_ssl_verify": None,
        "rpc_allow_cors": None,
        "p2sh_dust_return_pubkey": None,
        "utxo_locks_max_addresses": config.DEFAULT_UTXO_LOCKS_MAX_ADDRESSES,
        "utxo_locks_max_age": config.DEFAULT_UTXO_LOCKS_MAX_AGE,
        "estimate_fee_per_kb": None,
        "customnet": None,
        "verbose": 0,
        "quiet": False,
        "log_file": None,
        "api_log_file": None,
        "no_log_files": False,
        "no_check_asset_conservation": True,
        "action": "",
        "no_refresh_backend_height": True,
        "no_mempool": False,
        "skip_db_check": False,
        "no_telemetry": True,
        "enable_zmq_publisher": False,
        "zmq_publisher_port": None,
        "db_connection_pool_size": None,
        "json_logs": False,
    }
    server_config = (
        default_config
        | util_test.COUNTERPARTYD_OPTIONS
        | {
            "database_file": request.module.FIXTURE_DB,
            "api_port": TEST_RPC_PORT + 10,
        }
    )

    if os.path.exists(config.API_DATABASE):
        os.unlink(config.API_DATABASE)
    if os.path.exists(config.API_DATABASE + "-shm"):
        os.unlink(config.API_DATABASE + "-shm")
    if os.path.exists(config.API_DATABASE + "-wal"):
        os.unlink(config.API_DATABASE + "-wal")

    def is_server_ready():
        return True

    api_v2.is_server_ready = is_server_ready

    args = argparse.Namespace(**server_config)
    api_server = api_v2.APIServer()
    api_server.start(args)

    # wait for server to be ready
    while True:
        try:
            result = requests.get("http://localhost:10009/v2/", timeout=30)
            print(result.text)
            print(result.status_code)
            if result.status_code != 200:
                raise requests.exceptions.RequestException
            result = result.json()
            print(DEFAULT_PARAMS["default_block_index"])
            if result["result"]["counterparty_height"] < DEFAULT_PARAMS["default_block_index"] - 1:
                raise requests.exceptions.RequestException
            break
        except requests.exceptions.RequestException:
            print("TimeoutError: waiting for API server to be ready")
            time.sleep(1)
            pass

    request.addfinalizer(lambda: api_server.stop())

    return api_server


@pytest.fixture(scope="module")
def cp_server(request):
    dbfile = request.module.FIXTURE_DB
    sqlfile = request.module.FIXTURE_SQL_FILE
    options = getattr(request.module, "FIXTURE_OPTIONS", {})

    print(f"cp_server: {dbfile} {sqlfile} {options}")
    db = util_test.init_database(sqlfile, dbfile, options)  # noqa: F841

    request.addfinalizer(lambda: util_test.remove_database_files(dbfile))

    return db


class MockUTXOSet(object):
    """
    :type utxos list UTXOs list containing:
                        { 'address': 'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',
                          'amount': 1.9990914,
                          'value': 199909140,
                          'confirmations': 74,
                          'scriptPubKey': '76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac',
                          'txhex': '0100000002eff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b000000006c493046022100ec6fa8316a4f5cfd69816e31011022acce0933bd3b01248caa8b49e60de1b98a022100987ba974b2a4f9976a8d61d94009cb7f7986a827dc5730e999de1fb748d2046c01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffffeff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b010000006a47304402201f8fb2d62df22592cb8d37c68ab26563dbb8e270f7f8409ac0f6d7b24ddb5c940220314e5c767fd12b20116528c028eab2bfbad30eb963bd849993410049cf14a83d01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffff02145fea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000346a32544553540000000a00000000000000010000000005f5e1000000000000000000000000000bebc2000032000000000000271000000000',
                          'txid': 'ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1',
                          'vout': 0}
    """

    utxos = []

    def __init__(self, utxos, rawtransactions_db):
        self.txouts = utxos or []
        self.spent_utxos = []
        self.rawtransactions_db = rawtransactions_db
        # logger.warning('MockUTXOSet %d' % len(utxos))

    def get_unspent_txouts(
        self, address, unconfirmed=False, multisig_inputs=False, unspent_tx_hash=None
    ):
        # filter by address
        txouts = [output for output in self.txouts if output["address"] == address]

        # filter out the spend outputs
        unspent_txouts = filter(
            lambda txout: (txout["txid"], txout["vout"]) not in self.spent_utxos, txouts
        )

        if unconfirmed == False:  # noqa: E712
            unspent_txouts = filter(lambda txout: txout["confirmations"] > 0, unspent_txouts)

        if multisig_inputs:
            raise NotImplementedError(f"{multisig_inputs}")

        if unspent_tx_hash:
            unspent_txouts = filter(lambda txout: txout["txid"] == unspent_tx_hash, unspent_txouts)

        return list(unspent_txouts)

    def update_utxo_set(self, txins, txouts):
        # spent the UTXOs
        for txin in txins:
            self.spent_utxos.append((txin["txid"], txin["vout"]))

        for txout in txouts:
            self.txouts.append(
                {
                    "address": txout["address"],
                    "amount": txout["amount"],
                    "value": round(txout["amount"] * config.UNIT),
                    "confirmations": int(txout["confirmations"]),
                    "script_pub_key": txout["script_pub_key"],
                    "txhex": txout["txhex"],
                    "txid": txout["txid"],
                    "vout": txout["vout"],
                }
            )

    def increment_confirmations(self):
        cursor = self.rawtransactions_db.cursor()
        cursor.execute("""UPDATE raw_transactions SET confirmations = confirmations + 1""")
        cursor.close()

        for utxo in self.txouts:
            utxo["confirmations"] = (utxo["confirmations"] or 0) + 1

    def add_raw_transaction(self, raw_transaction, tx_id=None, confirmations=0):
        tx = pycoin.coins.bitcoin.Tx.Tx.from_hex(raw_transaction)
        tx_id = tx_id or tx.id()

        txins = []
        for txin in tx.txs_in:
            txins.append(
                {
                    "txid": pycoin.encoding.hexbytes.b2h_rev(txin.previous_hash),
                    "vout": txin.previous_index,
                }
            )

        txouts = []
        for idx, txout in enumerate(tx.txs_out):
            txouts.append(
                {
                    "address": script.scriptpubkey_to_address(
                        bitcoinlib.core.CScript(txout.script)
                    ),
                    "confirmations": int(confirmations),
                    "amount": txout.coin_value / 1e8,
                    "value": txout.coin_value,
                    "script_pub_key": binascii.hexlify(txout.script).decode("ascii"),
                    "txhex": raw_transaction,
                    "txid": tx_id,
                    "vout": idx,
                }
            )

        # logger.warning('add_raw_transaction %d/%d' % (len(txins), len(txouts)))
        # logger.debug(pprint.pformat(txins))
        # logger.debug(pprint.pformat(txouts))

        util_test.save_rawtransaction(
            self.rawtransactions_db, tx_id, raw_transaction, confirmations
        )

        self.update_utxo_set(txins, txouts)


@pytest.fixture(scope="module", autouse=True)
def setup_logging():
    print("")  # for --verbose output this makes sure the logs start on a newline
    log.set_up(verbose=True)


@pytest.fixture(scope="function", autouse=True)
def mock_utxos(rawtransactions_db):
    with open(util_test.CURR_DIR + "/fixtures/unspent_outputs.json", "r") as listunspent_test_file:
        util_test.MOCK_UTXO_SET = MockUTXOSet(json.load(listunspent_test_file), rawtransactions_db)

    util_test.UNIQUE_DUMMY_TX_HASH = {}
    util_test.TX_INDEX = 1

    return util_test.MOCK_UTXO_SET


def add_fn_property(**kwargs):
    """
    decorator to assign attributes to a FN
    :param kwargs: attributes assigned
    :return: fn
    """

    def decorator(fn):
        for k, v in kwargs.items():
            setattr(fn, k, v)

        return fn

    return decorator


@pytest.fixture(scope="function", autouse=True)
def init_mock_functions(request, monkeypatch, mock_utxos, rawtransactions_db):
    """Test suit mock functions.

    Mock functions override default behaviour to allow test suit to work - for instance, date_passed is overwritten
    so that every date will pass. Those are available to every test function in this suite."""

    util_test.rawtransactions_db = rawtransactions_db

    def get_unspent_txouts(*args, **kwargs):
        return mock_utxos.get_unspent_txouts(*args, **kwargs)

    def isodt(epoch_time):
        return datetime.utcfromtimestamp(epoch_time).isoformat()

    def curr_time():
        return 0

    def date_passed(date):
        return False

    def init_api_access_log(app):
        pass

    def pubkeyhash_to_pubkey(address, provided_pubkeys=None):
        return DEFAULT_PARAMS["pubkey"][address]

    def multisig_pubkeyhashes_to_pubkeys(address, provided_pubkeys=None):
        # TODO: Should be updated?!
        array = address.split("_")
        signatures_required = int(array[0])
        pubkeyhashes = array[1:-1]
        pubkeys = [DEFAULT_PARAMS["pubkey"][pubkeyhash] for pubkeyhash in pubkeyhashes]
        address = "_".join([str(signatures_required)] + sorted(pubkeys) + [str(len(pubkeys))])
        return address

    def mocked_getrawtransaction(tx_hash, verbose=False, block_index=None):
        return util_test.getrawtransaction(
            rawtransactions_db, tx_hash, verbose=verbose, block_index=block_index
        )

    def mocked_getrawtransaction_batch(txhash_list, verbose=False, skip_missing=False):
        return util_test.getrawtransaction_batch(rawtransactions_db, txhash_list, verbose=verbose)

    def mocked_search_raw_transactions(address, unconfirmed=False):
        return util_test.search_raw_transactions(rawtransactions_db, address, unconfirmed)

    # mock the arc4 with a fixed seed to keep data from changing based on inputs
    _init_arc4 = arc4.init_arc4

    def init_arc4(seed):
        if getattr(config, "DISABLE_ARC4_MOCKING", False):
            return _init_arc4(seed)
        else:
            return ARC4.new(binascii.unhexlify("00" * 32))

    def check_wal_file(dbfile):
        pass

    def rps_expire(db, block_index):
        pass

    def is_valid_utxo(value):
        return util.is_utxo_format(value)

    def get_utxo_address_and_value(value):
        return "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc", 100

    def get_transaction_fee(db, transaction_type, block_index):
        return 10

    def prefix(block_index):
        return b"TESTXXXX"

    monkeypatch.setattr("counterpartycore.lib.transaction.arc4.init_arc4", init_arc4)
    monkeypatch.setattr(
        "counterpartycore.lib.backend.addrindexrs.get_unspent_txouts", get_unspent_txouts
    )
    monkeypatch.setattr("counterpartycore.lib.log.isodt", isodt)
    monkeypatch.setattr("counterpartycore.lib.ledger.curr_time", curr_time)
    monkeypatch.setattr("counterpartycore.lib.util.date_passed", date_passed)
    monkeypatch.setattr("counterpartycore.lib.api.util.init_api_access_log", init_api_access_log)

    monkeypatch.setattr(
        "counterpartycore.lib.backend.bitcoind.getrawtransaction", mocked_getrawtransaction
    )
    monkeypatch.setattr("counterpartycore.lib.backend.bitcoind.is_valid_utxo", is_valid_utxo)
    monkeypatch.setattr(
        "counterpartycore.lib.backend.bitcoind.get_utxo_address_and_value",
        get_utxo_address_and_value,
    )
    monkeypatch.setattr(
        "counterpartycore.lib.backend.addrindexrs.getrawtransaction_batch",
        mocked_getrawtransaction_batch,
    )
    monkeypatch.setattr(
        "counterpartycore.lib.backend.addrindexrs.search_raw_transactions",
        mocked_search_raw_transactions,
    )
    monkeypatch.setattr(
        "counterpartycore.lib.transaction.pubkeyhash_to_pubkey", pubkeyhash_to_pubkey
    )
    monkeypatch.setattr(
        "counterpartycore.lib.transaction.multisig_pubkeyhashes_to_pubkeys",
        multisig_pubkeyhashes_to_pubkeys,
    )
    monkeypatch.setattr("counterpartycore.lib.database.check_wal_file", check_wal_file)
    monkeypatch.setattr("counterpartycore.lib.messages.rps.expire", rps_expire)

    monkeypatch.setattr(
        "counterpartycore.lib.ledger.get_matching_orders", ledger.get_matching_orders_no_cache
    )

    monkeypatch.setattr("counterpartycore.lib.gas.get_transaction_fee", get_transaction_fee)
    monkeypatch.setattr("counterpartycore.lib.util.prefix", prefix)
