#! /usr/bin/env python3

import binascii
import decimal
import logging
import os
import signal
import sys
import tarfile
import tempfile
import time
import urllib
from urllib.parse import quote_plus as urlencode

import appdirs
import bitcoin as bitcoinlib
from termcolor import colored, cprint

from counterpartycore.lib import (
    backend,
    blocks,
    check,
    config,
    database,
    exceptions,
    follow,
    log,
    transaction,
    util,
)
from counterpartycore.lib.api import api_server as api_v2
from counterpartycore.lib.api import api_v1
from counterpartycore.lib.backend import rsfetcher
from counterpartycore.lib.public_keys import PUBLIC_KEYS
from counterpartycore.lib.telemetry.oneshot import TelemetryOneShot

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

OK_GREEN = colored("[OK]", "green")
SPINNER_STYLE = "bouncingBar"


class ConfigurationError(Exception):
    pass


def handle_interrupt_signal(signum, _frame):
    raise KeyboardInterrupt(f"Received signal {signal.strsignal(signum)}")


def initialise(*args, **kwargs):
    initialise_log_config(
        verbose=kwargs.pop("verbose", 0),
        quiet=kwargs.pop("quiet", False),
        log_file=kwargs.pop("log_file", None),
        api_log_file=kwargs.pop("api_log_file", None),
        no_log_files=kwargs.pop("no_log_files", False),
        testnet=kwargs.get("testnet", False),
        testcoin=kwargs.get("testcoin", False),
        regtest=kwargs.get("regtest", False),
        action=kwargs.get("action", None),
        json_logs=kwargs.get("json_logs", False),
    )
    initialise_config(*args, **kwargs)
    return database.initialise_db()


def initialise_log_config(
    verbose=0,
    quiet=False,
    log_file=None,
    api_log_file=None,
    no_log_files=False,
    testnet=False,
    testcoin=False,
    regtest=False,
    action=None,
    json_logs=False,
):
    # Log directory
    log_dir = appdirs.user_log_dir(appauthor=config.XCP_NAME, appname=config.APP_NAME)
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir, mode=0o755)

    # Set up logging.
    config.VERBOSE = verbose
    config.QUIET = quiet

    if config.VERBOSE == 0:
        config.LOG_LEVEL_STRING = "info"
    elif config.VERBOSE == 1:
        config.LOG_LEVEL_STRING = "debug"
    elif config.VERBOSE >= 2:
        config.LOG_LEVEL_STRING = "trace"

    network = ""
    if testnet:
        network += ".testnet"
    if regtest:
        network += ".regtest"
    if testcoin:
        network += ".testcoin"

    # Log
    if no_log_files:
        config.LOG = None
    elif not log_file:  # default location
        filename = f"server{network}.log"
        config.LOG = os.path.join(log_dir, filename)
    else:  # user-specified location
        config.LOG = log_file

    if config.LOG:
        config.FETCHER_LOG = os.path.join(os.path.dirname(config.LOG), f"fetcher{network}.log")

    if no_log_files:  # no file logging
        config.API_LOG = None
    elif not api_log_file:  # default location
        filename = f"server{network}.access.log"
        config.API_LOG = os.path.join(log_dir, filename)
    else:  # user-specified location
        config.API_LOG = api_log_file

    config.LOG_IN_CONSOLE = action == "start" or config.VERBOSE > 0
    config.JSON_LOGS = json_logs


def initialise_config(
    database_file=None,
    testnet=False,
    testcoin=False,
    regtest=False,
    api_limit_rows=1000,
    backend_connect=None,
    backend_port=None,
    backend_user=None,
    backend_password=None,
    indexd_connect=None,
    indexd_port=None,
    backend_ssl=False,
    backend_ssl_no_verify=False,
    backend_poll_interval=None,
    rpc_host=None,
    rpc_port=None,
    rpc_user=None,
    rpc_password=None,
    rpc_no_allow_cors=False,
    api_host=None,
    api_port=None,
    api_user=None,
    api_password=None,
    api_no_allow_cors=False,
    force=False,
    requests_timeout=config.DEFAULT_REQUESTS_TIMEOUT,
    rpc_batch_size=config.DEFAULT_RPC_BATCH_SIZE,
    check_asset_conservation=False,
    backend_ssl_verify=None,
    rpc_allow_cors=None,
    p2sh_dust_return_pubkey=None,
    utxo_locks_max_addresses=config.DEFAULT_UTXO_LOCKS_MAX_ADDRESSES,
    utxo_locks_max_age=config.DEFAULT_UTXO_LOCKS_MAX_AGE,
    estimate_fee_per_kb=None,
    customnet=None,
    no_mempool=False,
    no_telemetry=False,
    enable_zmq_publisher=False,
    zmq_publisher_port=None,
    db_connection_pool_size=None,
):
    # log config already initialized

    # Data directory
    data_dir = appdirs.user_data_dir(
        appauthor=config.XCP_NAME, appname=config.APP_NAME, roaming=True
    )
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, mode=0o755)

    # testnet
    if testnet:
        config.TESTNET = testnet
    else:
        config.TESTNET = False

    # testcoin
    if testcoin:
        config.TESTCOIN = testcoin
    else:
        config.TESTCOIN = False

    # regtest
    if regtest:
        config.REGTEST = regtest
    else:
        config.REGTEST = False

    if customnet != None and len(customnet) > 0:  # noqa: E711
        config.CUSTOMNET = True
        config.REGTEST = True  # Custom nets are regtests with different parameters
    else:
        config.CUSTOMNET = False

    if config.TESTNET:
        bitcoinlib.SelectParams("testnet")
    elif config.REGTEST:
        bitcoinlib.SelectParams("regtest")
    else:
        bitcoinlib.SelectParams("mainnet")

    config.NETWORK_NAME = "mainnet"
    if config.TESTNET:
        config.NETWORK_NAME = "testnet"
    if config.REGTEST:
        config.NETWORK_NAME = "regtest"
    if config.TESTCOIN:
        config.NETWORK_NAME = "testcoin"
    network = f".{config.NETWORK_NAME }" if config.NETWORK_NAME != "mainnet" else ""

    # Database
    if database_file:
        config.DATABASE = database_file
    else:
        filename = f"{config.APP_NAME}{network}.db"
        config.DATABASE = os.path.join(data_dir, filename)

    config.FETCHER_DB = os.path.join(os.path.dirname(config.DATABASE), f"fetcherdb{network}")
    config.API_DATABASE = config.DATABASE.replace(".db", ".api.db")
    config.API_LIMIT_ROWS = api_limit_rows

    ##############
    # THINGS WE CONNECT TO

    # Backend name
    config.BACKEND_NAME = "addrindexrs"

    # Backend RPC host (Bitcoin Core)
    if backend_connect:
        config.BACKEND_CONNECT = backend_connect
    else:
        config.BACKEND_CONNECT = "localhost"

    # Backend Core RPC port (Bitcoin Core)
    if backend_port:
        config.BACKEND_PORT = backend_port
    else:
        if config.TESTNET:
            config.BACKEND_PORT = config.DEFAULT_BACKEND_PORT_TESTNET
        elif config.REGTEST:
            config.BACKEND_PORT = config.DEFAULT_BACKEND_PORT_REGTEST
        else:
            config.BACKEND_PORT = config.DEFAULT_BACKEND_PORT

    try:
        config.BACKEND_PORT = int(config.BACKEND_PORT)
        if not (int(config.BACKEND_PORT) > 1 and int(config.BACKEND_PORT) < 65535):
            raise ConfigurationError("invalid backend API port number")
    except:  # noqa: E722
        raise ConfigurationError(  # noqa: B904
            "Please specific a valid port number backend-port configuration parameter"
        )

    # Backend Core RPC user (Bitcoin Core)
    if backend_user:
        config.BACKEND_USER = backend_user
    else:
        config.BACKEND_USER = "rpc"

    # Backend Core RPC password (Bitcoin Core)
    if backend_password:
        config.BACKEND_PASSWORD = backend_password
    else:
        raise ConfigurationError(
            "Please specific a valid password backend-password configuration parameter"
        )

    # Backend Core RPC SSL
    if backend_ssl:
        config.BACKEND_SSL = backend_ssl
    else:
        config.BACKEND_SSL = False  # Default to off.

    # Backend Core RPC SSL Verify
    if backend_ssl_verify is not None:
        cprint(
            "The server parameter `backend_ssl_verify` is deprecated. Use `backend_ssl_no_verify` instead.",
            "yellow",
        )
        config.BACKEND_SSL_NO_VERIFY = not backend_ssl_verify
    else:
        if backend_ssl_no_verify:
            config.BACKEND_SSL_NO_VERIFY = backend_ssl_no_verify
        else:
            config.BACKEND_SSL_NO_VERIFY = (
                False  # Default to on (don't support self‐signed certificates)
            )

    # Backend Poll Interval
    if backend_poll_interval:
        config.BACKEND_POLL_INTERVAL = backend_poll_interval
    else:
        config.BACKEND_POLL_INTERVAL = 3.0

    # Construct backend URL.
    config.BACKEND_URL = (
        config.BACKEND_USER
        + ":"
        + config.BACKEND_PASSWORD
        + "@"
        + config.BACKEND_CONNECT
        + ":"
        + str(config.BACKEND_PORT)
    )
    if config.BACKEND_SSL:
        config.BACKEND_URL = "https://" + config.BACKEND_URL
    else:
        config.BACKEND_URL = "http://" + config.BACKEND_URL

    # Indexd RPC host
    if indexd_connect:
        config.INDEXD_CONNECT = indexd_connect
    else:
        config.INDEXD_CONNECT = "localhost"

    # Indexd RPC port
    if indexd_port:
        config.INDEXD_PORT = indexd_port
    else:
        if config.TESTNET:
            config.INDEXD_PORT = config.DEFAULT_INDEXD_PORT_TESTNET
        elif config.REGTEST:
            config.INDEXD_PORT = config.DEFAULT_INDEXD_PORT_REGTEST
        else:
            config.INDEXD_PORT = config.DEFAULT_INDEXD_PORT

    try:
        config.INDEXD_PORT = int(config.INDEXD_PORT)
        if not (int(config.INDEXD_PORT) > 1 and int(config.INDEXD_PORT) < 65535):
            raise ConfigurationError("invalid Indexd API port number")
    except:  # noqa: E722
        raise ConfigurationError(  # noqa: B904
            "Please specific a valid port number indexd-port configuration parameter"
        )

    # Construct Indexd URL.
    config.INDEXD_URL = "http://" + config.INDEXD_CONNECT + ":" + str(config.INDEXD_PORT)

    ##############
    # THINGS WE SERVE

    # Server API RPC host
    if rpc_host:
        config.RPC_HOST = rpc_host
    else:
        config.RPC_HOST = "localhost"

    # The web root directory for API calls, eg. localhost:14000/rpc/
    config.RPC_WEBROOT = "/rpc/"

    # Server API RPC port
    if rpc_port:
        config.RPC_PORT = rpc_port
    else:
        if config.TESTNET:
            if config.TESTCOIN:
                config.RPC_PORT = config.DEFAULT_RPC_PORT_TESTNET + 1
            else:
                config.RPC_PORT = config.DEFAULT_RPC_PORT_TESTNET
        elif config.REGTEST:
            if config.TESTCOIN:
                config.RPC_PORT = config.DEFAULT_RPC_PORT_REGTEST + 1
            else:
                config.RPC_PORT = config.DEFAULT_RPC_PORT_REGTEST
        else:
            if config.TESTCOIN:
                config.RPC_PORT = config.DEFAULT_RPC_PORT + 1
            else:
                config.RPC_PORT = config.DEFAULT_RPC_PORT
    try:
        config.RPC_PORT = int(config.RPC_PORT)
        if not (int(config.RPC_PORT) > 1 and int(config.RPC_PORT) < 65535):
            raise ConfigurationError("invalid server API port number")
    except:  # noqa: E722
        raise ConfigurationError(  # noqa: B904
            "Please specific a valid port number rpc-port configuration parameter"
        )

    # Server API RPC user
    if rpc_user:
        config.RPC_USER = rpc_user
    else:
        config.RPC_USER = "rpc"

    configure_rpc(rpc_password)

    # RPC CORS
    if rpc_allow_cors is not None:
        cprint(
            "The server parameter `rpc_allow_cors` is deprecated. Use `rpc_no_allow_cors` instead.",
            "yellow",
        )
        config.RPC_NO_ALLOW_CORS = not rpc_allow_cors
    else:
        if rpc_no_allow_cors:
            config.RPC_NO_ALLOW_CORS = rpc_no_allow_cors
        else:
            config.RPC_NO_ALLOW_CORS = False

    config.RPC_BATCH_SIZE = rpc_batch_size

    # Server API RPC host
    if api_host:
        config.API_HOST = api_host
    else:
        config.API_HOST = "localhost"

    # Server API port
    if api_port:
        config.API_PORT = api_port
    else:
        if config.TESTNET:
            if config.TESTCOIN:
                config.API_PORT = config.DEFAULT_API_PORT_TESTNET + 1
            else:
                config.API_PORT = config.DEFAULT_API_PORT_TESTNET
        elif config.REGTEST:
            if config.TESTCOIN:
                config.API_PORT = config.DEFAULT_API_PORT_REGTEST + 1
            else:
                config.API_PORT = config.DEFAULT_API_PORT_REGTEST
        else:
            if config.TESTCOIN:
                config.API_PORT = config.DEFAULT_API_PORT + 1
            else:
                config.API_PORT = config.DEFAULT_API_PORT
    try:
        config.API_PORT = int(config.API_PORT)
        if not (int(config.API_PORT) > 1 and int(config.API_PORT) < 65535):
            raise ConfigurationError("invalid server API port number")
    except:  # noqa: E722
        raise ConfigurationError(  # noqa: B904
            "Please specific a valid port number rpc-port configuration parameter"
        )

    # ZMQ Publisher
    config.ENABLE_ZMQ_PUBLISHER = enable_zmq_publisher

    if zmq_publisher_port:
        config.ZMQ_PUBLISHER_PORT = zmq_publisher_port
    else:
        if config.TESTNET:
            if config.TESTCOIN:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_TESTNET + 1
            else:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_TESTNET
        elif config.REGTEST:
            if config.TESTCOIN:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_REGTEST + 1
            else:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_REGTEST
        else:
            if config.TESTCOIN:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT + 1
            else:
                config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT
    try:
        config.ZMQ_PUBLISHER_PORT = int(config.ZMQ_PUBLISHER_PORT)
        if not (int(config.ZMQ_PUBLISHER_PORT) > 1 and int(config.ZMQ_PUBLISHER_PORT) < 65535):
            raise ConfigurationError("invalid ZeroMQ publisher port number")
    except:  # noqa: E722
        raise ConfigurationError(  # noqa: B904
            "Please specific a valid port number rpc-port configuration parameter"
        )

    # Server API user
    if api_user:
        config.API_USER = api_user
    else:
        config.API_USER = "rpc"

    config.API_PASSWORD = api_password

    if api_no_allow_cors:
        config.API_NO_ALLOW_CORS = api_no_allow_cors
    else:
        config.API_NO_ALLOW_CORS = False

    ##############
    # OTHER SETTINGS

    # skip checks
    if force:
        config.FORCE = force
    else:
        config.FORCE = False

    # (more) Testnet
    if config.TESTNET:
        config.MAGIC_BYTES = config.MAGIC_BYTES_TESTNET
        if config.TESTCOIN:
            config.ADDRESSVERSION = config.ADDRESSVERSION_TESTNET
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_TESTNET
            config.BLOCK_FIRST = config.BLOCK_FIRST_TESTNET_TESTCOIN
            config.BURN_START = config.BURN_START_TESTNET_TESTCOIN
            config.BURN_END = config.BURN_END_TESTNET_TESTCOIN
            config.UNSPENDABLE = config.UNSPENDABLE_TESTNET
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
        else:
            config.ADDRESSVERSION = config.ADDRESSVERSION_TESTNET
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_TESTNET
            config.BLOCK_FIRST = config.BLOCK_FIRST_TESTNET
            config.BURN_START = config.BURN_START_TESTNET
            config.BURN_END = config.BURN_END_TESTNET
            config.UNSPENDABLE = config.UNSPENDABLE_TESTNET
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
    elif config.CUSTOMNET:
        custom_args = customnet.split("|")

        if len(custom_args) == 3:
            config.MAGIC_BYTES = config.MAGIC_BYTES_REGTEST
            config.ADDRESSVERSION = binascii.unhexlify(custom_args[1])
            config.P2SH_ADDRESSVERSION = binascii.unhexlify(custom_args[2])
            config.BLOCK_FIRST = config.BLOCK_FIRST_REGTEST
            config.BURN_START = config.BURN_START_REGTEST
            config.BURN_END = config.BURN_END_REGTEST
            config.UNSPENDABLE = custom_args[0]
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
        else:
            raise "Custom net parameter needs to be like UNSPENDABLE_ADDRESS|ADDRESSVERSION|P2SH_ADDRESSVERSION (version bytes in HH format)"  # noqa: B016
    elif config.REGTEST:
        config.MAGIC_BYTES = config.MAGIC_BYTES_REGTEST
        if config.TESTCOIN:
            config.ADDRESSVERSION = config.ADDRESSVERSION_REGTEST
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_REGTEST
            config.BLOCK_FIRST = config.BLOCK_FIRST_REGTEST_TESTCOIN
            config.BURN_START = config.BURN_START_REGTEST_TESTCOIN
            config.BURN_END = config.BURN_END_REGTEST_TESTCOIN
            config.UNSPENDABLE = config.UNSPENDABLE_REGTEST
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
        else:
            config.ADDRESSVERSION = config.ADDRESSVERSION_REGTEST
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_REGTEST
            config.BLOCK_FIRST = config.BLOCK_FIRST_REGTEST
            config.BURN_START = config.BURN_START_REGTEST
            config.BURN_END = config.BURN_END_REGTEST
            config.UNSPENDABLE = config.UNSPENDABLE_REGTEST
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
    else:
        config.MAGIC_BYTES = config.MAGIC_BYTES_MAINNET
        if config.TESTCOIN:
            config.ADDRESSVERSION = config.ADDRESSVERSION_MAINNET
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_MAINNET
            config.BLOCK_FIRST = config.BLOCK_FIRST_MAINNET_TESTCOIN
            config.BURN_START = config.BURN_START_MAINNET_TESTCOIN
            config.BURN_END = config.BURN_END_MAINNET_TESTCOIN
            config.UNSPENDABLE = config.UNSPENDABLE_MAINNET
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
        else:
            config.ADDRESSVERSION = config.ADDRESSVERSION_MAINNET
            config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_MAINNET
            config.BLOCK_FIRST = config.BLOCK_FIRST_MAINNET
            config.BURN_START = config.BURN_START_MAINNET
            config.BURN_END = config.BURN_END_MAINNET
            config.UNSPENDABLE = config.UNSPENDABLE_MAINNET
            config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey

    # Misc
    config.REQUESTS_TIMEOUT = requests_timeout
    config.CHECK_ASSET_CONSERVATION = check_asset_conservation
    config.UTXO_LOCKS_MAX_ADDRESSES = utxo_locks_max_addresses
    config.UTXO_LOCKS_MAX_AGE = utxo_locks_max_age

    if estimate_fee_per_kb is not None:
        config.ESTIMATE_FEE_PER_KB = estimate_fee_per_kb

    config.NO_MEMPOOL = no_mempool

    config.NO_TELEMETRY = no_telemetry

    if db_connection_pool_size:
        config.DB_CONNECTION_POOL_SIZE = db_connection_pool_size
    else:
        config.DB_CONNECTION_POOL_SIZE = config.DEFAULT_DB_CONNECTION_POOL_SIZE


def initialise_log_and_config(args):
    # Configuration
    init_args = {
        "database_file": args.database_file,
        "testnet": args.testnet,
        "testcoin": args.testcoin,
        "regtest": args.regtest,
        "customnet": args.customnet,
        "api_limit_rows": args.api_limit_rows,
        "backend_connect": args.backend_connect,
        "backend_port": args.backend_port,
        "backend_user": args.backend_user,
        "backend_password": args.backend_password,
        "backend_ssl": args.backend_ssl,
        "backend_ssl_no_verify": args.backend_ssl_no_verify,
        "backend_poll_interval": args.backend_poll_interval,
        "indexd_connect": args.indexd_connect,
        "indexd_port": args.indexd_port,
        "rpc_host": args.rpc_host,
        "rpc_port": args.rpc_port,
        "rpc_user": args.rpc_user,
        "rpc_password": args.rpc_password,
        "rpc_no_allow_cors": args.rpc_no_allow_cors,
        "api_host": args.api_host,
        "api_port": args.api_port,
        "api_user": args.api_user,
        "api_password": args.api_password,
        "api_no_allow_cors": args.api_no_allow_cors,
        "requests_timeout": args.requests_timeout,
        "rpc_batch_size": args.rpc_batch_size,
        "check_asset_conservation": args.check_asset_conservation,
        "force": args.force,
        "p2sh_dust_return_pubkey": args.p2sh_dust_return_pubkey,
        "utxo_locks_max_addresses": args.utxo_locks_max_addresses,
        "utxo_locks_max_age": args.utxo_locks_max_age,
        "no_mempool": args.no_mempool,
        "no_telemetry": args.no_telemetry,
        "enable_zmq_publisher": args.enable_zmq_publisher,
        "zmq_publisher_port": args.zmq_publisher_port,
        "db_connection_pool_size": args.db_connection_pool_size,
    }

    initialise_log_config(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
        api_log_file=args.api_log_file,
        no_log_files=args.no_log_files,
        testnet=args.testnet,
        testcoin=args.testcoin,
        regtest=args.regtest,
        action=args.action,
        json_logs=args.json_logs,
    )

    # set up logging
    log.set_up(
        verbose=config.VERBOSE,
        quiet=config.QUIET,
        log_file=config.LOG,
        json_logs=config.JSON_LOGS,
    )
    initialise_config(**init_args)


def connect_to_backend():
    if not config.FORCE:
        backend.bitcoind.getblockcount()


def start_all(args):
    api_status_poller = None
    api_server_v1 = None
    api_server_v2 = None
    telemetry_daemon = None
    follower_daemon = None
    db = None

    try:
        # set signal handlers (needed for graceful shutdown on SIGINT/SIGTERM)
        signal.signal(signal.SIGINT, handle_interrupt_signal)
        signal.signal(signal.SIGTERM, handle_interrupt_signal)

        # download bootstrap if necessary
        if not os.path.exists(config.DATABASE) and args.catch_up == "bootstrap":
            bootstrap(no_confirm=True)

        # initialise database
        db = database.initialise_db()
        blocks.initialise(db)
        blocks.check_database_version(db)
        database.optimize(db)

        # check software version
        check.software_version()

        # API Server v2.
        api_server_v2 = api_v2.APIServer()
        api_server_v2.start(args)
        while not api_server_v2.is_ready():
            logger.trace("Waiting for API server to start...")
            time.sleep(0.1)

        # Backend.
        connect_to_backend()

        # Reset UTXO_LOCKS.  This previously was done in
        # initilise_config
        transaction.initialise()

        # API Status Poller.
        api_status_poller = api_v1.APIStatusPoller()
        api_status_poller.daemon = True
        api_status_poller.start()

        # API Server v1.
        api_server_v1 = api_v1.APIServer()
        api_server_v1.daemon = True
        api_server_v1.start()

        # catch up
        blocks.catch_up(db)

        # Blockchain watcher
        logger.info("Watching for new blocks...")
        follower_daemon = follow.start_blockchain_watcher(db)

    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt!")
    except Exception as e:
        logger.error("Exception caught!", exc_info=e)
    finally:
        if api_server_v2:
            api_server_v2.stop()
        if telemetry_daemon:
            telemetry_daemon.stop()
        if api_status_poller:
            api_status_poller.stop()
        if api_server_v1:
            api_server_v1.stop()
        if follower_daemon:
            follower_daemon.stop()
        if not config.NO_TELEMETRY:
            TelemetryOneShot().close()
        if db:
            database.close(db)
        backend.addrindexrs.stop()
        log.shutdown()
        rsfetcher.stop()
        try:
            database.check_wal_file(config.DATABASE)
        except exceptions.WALFileFoundError:
            logger.warning(
                "Database WAL file detected. To ensure no data corruption has occurred, run `counterpary-server check-db`."
            )
        except exceptions.DatabaseError:
            logger.warning(
                "Database is in use by another process and was unable to be closed correctly."
            )
        # Ensure that the last closed connection is not read-only in order to delete WAL and SHM files
        api_db = database.get_db_connection(config.API_DATABASE, read_only=False, check_wal=False)
        api_db.close()
        logger.info("Shutdown complete.")


def reparse(block_index):
    backend.addrindexrs.init()
    db = database.initialise_db()
    try:
        blocks.reparse(db, block_index=block_index)
    finally:
        backend.addrindexrs.stop()
        database.optimize(db)
        db.close()


def rollback(block_index=None):
    db = database.initialise_db()
    try:
        blocks.rollback(db, block_index=block_index)
    finally:
        database.optimize(db)
        db.close()


def vacuum():
    db = database.initialise_db()
    with log.Spinner("Vacuuming database..."):
        database.vacuum(db)


def check_database():
    db = database.initialise_db()

    start_all_time = time.time()

    with log.Spinner("Checking asset conservation..."):
        check.asset_conservation(db)

    with log.Spinner("Checking database foreign keys...."):
        database.check_foreign_keys(db)

    with log.Spinner("Checking database integrity..."):
        database.intergrity_check(db)

    cprint(f"Database checks complete in {time.time() - start_all_time:.2f}s.", "green")


def show_params():
    output = vars(config)
    for k in list(output.keys()):
        if k.isupper():
            print(f"{k}: {output[k]}")


def generate_move_random_hash(move):
    move = int(move).to_bytes(2, byteorder="big")
    random_bin = os.urandom(16)
    move_random_hash_bin = util.dhash(random_bin + move)
    return binascii.hexlify(random_bin).decode("utf8"), binascii.hexlify(
        move_random_hash_bin
    ).decode("utf8")


def configure_rpc(rpc_password=None):
    # Server API RPC password
    if rpc_password:
        config.RPC_PASSWORD = rpc_password
        config.API_ROOT = (
            "http://"
            + urlencode(config.RPC_USER)
            + ":"
            + urlencode(config.RPC_PASSWORD)
            + "@"
            + config.RPC_HOST
            + ":"
            + str(config.RPC_PORT)
        )
    else:
        config.API_ROOT = "http://" + config.RPC_HOST + ":" + str(config.RPC_PORT)
    config.RPC = config.API_ROOT + config.RPC_WEBROOT


def bootstrap(no_confirm=False, snapshot_url=None):
    warning_message = """WARNING: `counterparty-server bootstrap` downloads a recent snapshot of a Counterparty database
from a centralized server maintained by the Counterparty Core development team.
Because this method does not involve verifying the history of Counterparty transactions yourself,
the `bootstrap` command should not be used for mission-critical, commercial or public-facing nodes.
        """
    cprint(warning_message, "yellow")

    if not no_confirm:
        confirmation_message = colored("Continue? (y/N): ", "magenta")
        if input(confirmation_message).lower() != "y":
            exit()

    data_dir = appdirs.user_data_dir(
        appauthor=config.XCP_NAME, appname=config.APP_NAME, roaming=True
    )

    # Set Constants.
    if snapshot_url is None:
        bootstrap_url = (
            config.BOOTSTRAP_URL_TESTNET if config.TESTNET else config.BOOTSTRAP_URL_MAINNET
        )
        bootstrap_sig_url = (
            config.BOOTSTRAP_URL_TESTNET_SIG if config.TESTNET else config.BOOTSTRAP_URL_MAINNET_SIG
        )
    else:
        bootstrap_url = snapshot_url
        bootstrap_sig_url = snapshot_url.replace(".tar.gz", ".sig")

    tar_filename = os.path.basename(bootstrap_url)
    sig_filename = os.path.basename(bootstrap_sig_url)
    tarball_path = os.path.join(tempfile.gettempdir(), tar_filename)
    sig_path = os.path.join(tempfile.gettempdir(), sig_filename)
    ledger_database_path = os.path.join(data_dir, config.APP_NAME)
    if config.TESTNET:
        ledger_database_path += ".testnet"
    ledger_database_path += ".db"
    api_database_path = ledger_database_path.replace(".db", ".api.db")

    # Prepare Directory.
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, mode=0o755)

    for database_path in [ledger_database_path, api_database_path]:
        if os.path.exists(database_path):
            os.remove(database_path)
        # Delete SQLite Write-Ahead-Log
        wal_path = database_path + "-wal"
        shm_path = database_path + "-shm"
        if os.path.exists(wal_path):
            os.remove(wal_path)
        if os.path.exists(shm_path):
            os.remove(shm_path)

    # Define Progress Bar.
    spinner = log.Spinner(f"Downloading database from {bootstrap_url}...")

    def bootstrap_progress(blocknum, blocksize, totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = readsofar * 1e2 / totalsize
            message = f"Downloading database: {percent:5.1f}% {readsofar} / {totalsize}"
            spinner.set_messsage(message)

    # Downloading
    spinner.start()
    urllib.request.urlretrieve(bootstrap_url, tarball_path, bootstrap_progress)  # nosec B310  # noqa: S310
    urllib.request.urlretrieve(bootstrap_sig_url, sig_path)  # nosec B310  # noqa: S310
    spinner.stop()

    with log.Spinner("Verifying signature..."):
        if not any(util.verify_signature(k, sig_path, tarball_path) for k in PUBLIC_KEYS):
            print("Snaptshot was not signed by any trusted keys")
            sys.exit(1)

    # TODO: check checksum, filenames, etc.
    with log.Spinner(f"Extracting database to {data_dir}..."):
        with tarfile.open(tarball_path, "r:gz") as tar_file:
            tar_file.extractall(path=data_dir)  # nosec B202  # noqa: S202

    assert os.path.exists(ledger_database_path)
    assert os.path.exists(api_database_path)
    # user and group have "rw" access
    os.chmod(ledger_database_path, 0o660)  # nosec B103
    os.chmod(api_database_path, 0o660)  # nosec B103

    with log.Spinner("Cleaning up..."):
        os.remove(tarball_path)

    cprint(
        f"Databases have been successfully bootstrapped to {ledger_database_path} and {api_database_path}.",
        "green",
    )
