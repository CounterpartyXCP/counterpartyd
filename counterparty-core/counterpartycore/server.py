#! /usr/bin/env python3

import _thread
import binascii
import decimal
import logging
import multiprocessing
import os
import threading
import time
from urllib.parse import quote_plus as urlencode

import appdirs
import bitcoin as bitcoinlib
from termcolor import colored, cprint

from counterpartycore.lib import (
    backend,
    blocks,
    bootstrap,
    check,
    config,
    database,
    exceptions,
    follow,
    ledger,
    log,
    util,
)
from counterpartycore.lib.api import api_server as api_v2
from counterpartycore.lib.api import api_v1, dbbuilder

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

OK_GREEN = colored("[OK]", "green")
SPINNER_STYLE = "bouncingBar"


class ConfigurationError(Exception):
    pass


def initialise(*args, **kwargs):
    initialise_log_config(
        verbose=kwargs.pop("verbose", 0),
        quiet=kwargs.pop("quiet", False),
        log_file=kwargs.pop("log_file", None),
        api_log_file=kwargs.pop("api_log_file", None),
        no_log_files=kwargs.pop("no_log_files", False),
        testnet3=kwargs.get("testnet3", False),
        testnet4=kwargs.get("testnet4", False),
        regtest=kwargs.get("regtest", False),
        action=kwargs.get("action", None),
        json_logs=kwargs.get("json_logs", False),
        max_log_file_size=kwargs.get("max_log_file_size", None),
        max_log_file_rotations=kwargs.get("max_log_file_rotations", None),
    )
    initialise_config(*args, **kwargs)
    return database.initialise_db()


def initialise_log_config(
    verbose=0,
    quiet=False,
    log_file=None,
    api_log_file=None,
    no_log_files=False,
    testnet3=False,
    testnet4=False,
    regtest=False,
    action=None,
    json_logs=False,
    max_log_file_size=40 * 1024 * 1024,
    max_log_file_rotations=20,
    log_exclude_filters=None,
    log_include_filters=None,
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
    if testnet3:
        network += ".testnet3"
    if regtest:
        network += ".regtest"
    if testnet4:
        network += ".testnet4"

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

    config.MAX_LOG_FILE_SIZE = max_log_file_size
    config.MAX_LOG_FILE_ROTATIONS = max_log_file_rotations

    config.LOG_EXCLUDE_FILTERS = log_exclude_filters
    config.LOG_INCLUDE_FILTERS = log_include_filters


def initialise_config(
    data_dir=None,
    cache_dir=None,
    testnet3=False,
    testnet4=False,
    regtest=False,
    api_limit_rows=1000,
    backend_connect=None,
    backend_port=None,
    backend_user=None,
    backend_password=None,
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
    skip_asset_conservation_check=False,
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
    db_connection_pool_size=config.DEFAULT_DB_CONNECTION_POOL_SIZE,
    wsgi_server=None,
    waitress_threads=None,
    gunicorn_workers=None,
    gunicorn_threads_per_worker=None,
    database_file=None,  # for tests
    action=None,
    electrs_url=None,
):
    # log config already initialized

    # Data directory
    if not data_dir:
        data_dir = appdirs.user_data_dir(
            appauthor=config.XCP_NAME, appname=config.APP_NAME, roaming=True
        )
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, mode=0o755)
    config.DATA_DIR = data_dir

    if not cache_dir:
        cache_dir = appdirs.user_cache_dir(appauthor=config.XCP_NAME, appname=config.APP_NAME)
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir, mode=0o755)
    config.CACHE_DIR = cache_dir

    # testnet
    if testnet3:
        config.TESTNET3 = testnet3
    else:
        config.TESTNET3 = False

    if testnet4:
        config.TESTNET4 = testnet4
    else:
        config.TESTNET4 = False

    # regtest
    if regtest:
        config.REGTEST = regtest
    else:
        config.REGTEST = False

    if config.TESTNET3 or config.TESTNET4:
        bitcoinlib.SelectParams("testnet")
    elif config.REGTEST:
        bitcoinlib.SelectParams("regtest")
    else:
        bitcoinlib.SelectParams("mainnet")

    config.NETWORK_NAME = "mainnet"
    if config.TESTNET3:
        config.NETWORK_NAME = "testnet3"
    if config.TESTNET4:
        config.NETWORK_NAME = "testnet4"
    if config.REGTEST:
        config.NETWORK_NAME = "regtest"
    network = f".{config.NETWORK_NAME }" if config.NETWORK_NAME != "mainnet" else ""

    # Database
    if database_file:
        config.DATABASE = database_file
    else:
        filename = f"{config.APP_NAME}{network}.db"
        config.DATABASE = os.path.join(data_dir, filename)

    config.FETCHER_DB_OLD = os.path.join(os.path.dirname(config.DATABASE), f"fetcherdb{network}")
    config.FETCHER_DB = os.path.join(config.CACHE_DIR, f"fetcherdb{network}")

    config.STATE_DATABASE = os.path.join(os.path.dirname(config.DATABASE), f"state{network}.db")

    if not os.path.exists(config.STATE_DATABASE):
        old_db_name = config.DATABASE.replace(".db", ".api.db")
        # delete old API db
        for ext in ["", "-wal", "-shm"]:
            if os.path.exists(old_db_name + ext):
                os.unlink(old_db_name + ext)

    config.API_LIMIT_ROWS = api_limit_rows

    ##############
    # THINGS WE CONNECT TO

    # Backend RPC host (Bitcoin Core)
    if backend_connect:
        config.BACKEND_CONNECT = backend_connect
    else:
        config.BACKEND_CONNECT = "localhost"

    # Backend Core RPC port (Bitcoin Core)
    if backend_port:
        config.BACKEND_PORT = backend_port
    else:
        if config.TESTNET3:
            config.BACKEND_PORT = config.DEFAULT_BACKEND_PORT_TESTNET
        elif config.TESTNET4:
            config.BACKEND_PORT = config.DEFAULT_BACKEND_PORT_TESTNET4
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

    ##############
    # THINGS WE SERVE

    # Server API RPC host
    if rpc_host:
        config.RPC_HOST = rpc_host
    else:
        config.RPC_HOST = "127.0.0.1"

    # The web root directory for API calls, eg. localhost:14000/rpc/
    config.RPC_WEBROOT = "/rpc/"

    # Server API RPC port
    if rpc_port:
        config.RPC_PORT = rpc_port
    else:
        if config.TESTNET3:
            config.RPC_PORT = config.DEFAULT_RPC_PORT_TESTNET
        elif config.TESTNET4:
            config.RPC_PORT = config.DEFAULT_RPC_PORT_TESTNET4
        elif config.REGTEST:
            config.RPC_PORT = config.DEFAULT_RPC_PORT_REGTEST
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
        config.API_HOST = "127.0.0.1"

    # Server API port
    if api_port:
        config.API_PORT = api_port
    else:
        if config.TESTNET3:
            config.API_PORT = config.DEFAULT_API_PORT_TESTNET
        elif config.TESTNET4:
            config.API_PORT = config.DEFAULT_API_PORT_TESTNET4
        elif config.REGTEST:
            config.API_PORT = config.DEFAULT_API_PORT_REGTEST
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
        if config.TESTNET3:
            config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_TESTNET
        elif config.TESTNET4:
            config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_TESTNET4
        elif config.REGTEST:
            config.ZMQ_PUBLISHER_PORT = config.DEFAULT_ZMQ_PUBLISHER_PORT_REGTEST
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

    # Encoding
    config.PREFIX = b"CNTRPRTY"  # 8 bytes

    # (more) Testnet
    if config.TESTNET3:
        config.MAGIC_BYTES = config.MAGIC_BYTES_TESTNET
        config.ADDRESSVERSION = config.ADDRESSVERSION_TESTNET
        config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_TESTNET
        config.BLOCK_FIRST = config.BLOCK_FIRST_TESTNET
        config.BURN_START = config.BURN_START_TESTNET
        config.BURN_END = config.BURN_END_TESTNET
        config.UNSPENDABLE = config.UNSPENDABLE_TESTNET
    elif config.TESTNET4:
        config.MAGIC_BYTES = config.MAGIC_BYTES_TESTNET4
        config.ADDRESSVERSION = config.ADDRESSVERSION_TESTNET4
        config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_TESTNET4
        config.BLOCK_FIRST = config.BLOCK_FIRST_TESTNET4
        config.BURN_START = config.BURN_START_TESTNET4
        config.BURN_END = config.BURN_END_TESTNET4
        config.UNSPENDABLE = config.UNSPENDABLE_TESTNET4
    elif config.REGTEST:
        config.MAGIC_BYTES = config.MAGIC_BYTES_REGTEST
        config.ADDRESSVERSION = config.ADDRESSVERSION_REGTEST
        config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_REGTEST
        config.BLOCK_FIRST = config.BLOCK_FIRST_REGTEST
        config.BURN_START = config.BURN_START_REGTEST
        config.BURN_END = config.BURN_END_REGTEST
        config.UNSPENDABLE = config.UNSPENDABLE_REGTEST
    else:
        config.MAGIC_BYTES = config.MAGIC_BYTES_MAINNET
        config.ADDRESSVERSION = config.ADDRESSVERSION_MAINNET
        config.P2SH_ADDRESSVERSION = config.P2SH_ADDRESSVERSION_MAINNET
        config.BLOCK_FIRST = config.BLOCK_FIRST_MAINNET
        config.BURN_START = config.BURN_START_MAINNET
        config.BURN_END = config.BURN_END_MAINNET
        config.UNSPENDABLE = config.UNSPENDABLE_MAINNET

    # Misc
    config.P2SH_DUST_RETURN_PUBKEY = p2sh_dust_return_pubkey
    config.REQUESTS_TIMEOUT = requests_timeout
    config.CHECK_ASSET_CONSERVATION = not skip_asset_conservation_check
    config.UTXO_LOCKS_MAX_ADDRESSES = utxo_locks_max_addresses
    config.UTXO_LOCKS_MAX_AGE = utxo_locks_max_age

    if estimate_fee_per_kb is not None:
        config.ESTIMATE_FEE_PER_KB = estimate_fee_per_kb

    config.NO_MEMPOOL = no_mempool

    config.NO_TELEMETRY = no_telemetry

    config.DB_CONNECTION_POOL_SIZE = db_connection_pool_size
    config.WSGI_SERVER = wsgi_server
    config.WAITRESS_THREADS = waitress_threads
    config.GUNICORN_THREADS_PER_WORKER = gunicorn_threads_per_worker
    config.GUNICORN_WORKERS = gunicorn_workers

    if electrs_url:
        if not util.is_url(electrs_url):
            raise ConfigurationError("Invalid Electrs URL")
        config.ELECTRS_URL = electrs_url
    else:
        if config.NETWORK_NAME == "testnet3":
            config.ELECTRS_URL = config.DEFAULT_ELECTRS_URL_TESTNET3
        elif config.NETWORK_NAME == "testnet4":
            config.ELECTRS_URL = config.DEFAULT_ELECTRS_URL_TESTNET4
        elif config.NETWORK_NAME == "mainnet":
            config.ELECTRS_URL = config.DEFAULT_ELECTRS_URL_MAINNET
        else:
            config.ELECTRS_URL = None


def initialise_log_and_config(args, api=False):
    # Configuration
    init_args = {
        "data_dir": args.data_dir,
        "cache_dir": args.cache_dir,
        "testnet3": args.testnet3,
        "testnet4": args.testnet4,
        "regtest": args.regtest,
        "api_limit_rows": args.api_limit_rows,
        "backend_connect": args.backend_connect,
        "backend_port": args.backend_port,
        "backend_user": args.backend_user,
        "backend_password": args.backend_password,
        "backend_ssl": args.backend_ssl,
        "backend_ssl_no_verify": args.backend_ssl_no_verify,
        "backend_poll_interval": args.backend_poll_interval,
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
        "skip_asset_conservation_check": args.skip_asset_conservation_check,
        "force": args.force,
        "p2sh_dust_return_pubkey": args.p2sh_dust_return_pubkey,
        "utxo_locks_max_addresses": args.utxo_locks_max_addresses,
        "utxo_locks_max_age": args.utxo_locks_max_age,
        "no_mempool": args.no_mempool,
        "no_telemetry": args.no_telemetry,
        "enable_zmq_publisher": args.enable_zmq_publisher,
        "zmq_publisher_port": args.zmq_publisher_port,
        "db_connection_pool_size": args.db_connection_pool_size,
        "wsgi_server": args.wsgi_server,
        "waitress_threads": args.waitress_threads,
        "gunicorn_workers": args.gunicorn_workers,
        "gunicorn_threads_per_worker": args.gunicorn_threads_per_worker,
        "action": args.action,
        "electrs_url": args.electrs_url,
    }
    # for tests
    if "database_file" in args:
        init_args["database_file"] = args.database_file

    initialise_log_config(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
        api_log_file=args.api_log_file,
        no_log_files=args.no_log_files,
        testnet3=args.testnet3,
        testnet4=args.testnet4,
        regtest=args.regtest,
        action=args.action,
        json_logs=args.json_logs,
        log_exclude_filters=args.log_exclude_filters,
        log_include_filters=args.log_include_filters,
    )

    # set up logging
    log.set_up(
        verbose=config.VERBOSE,
        quiet=config.QUIET,
        log_file=config.LOG if not api else config.API_LOG,
        json_logs=config.JSON_LOGS,
        max_log_file_size=config.MAX_LOG_FILE_SIZE,
        max_log_file_rotations=config.MAX_LOG_FILE_ROTATIONS,
    )
    initialise_config(**init_args)


def connect_to_backend():
    if not config.FORCE:
        backend.bitcoind.getblockcount()


class AssetConservationChecker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="AssetConservationChecker")
        self.daemon = True
        self.last_check = 0
        self.db = None
        self.stop_event = threading.Event()

    def run(self):
        self.db = database.get_db_connection(config.DATABASE, read_only=True, check_wal=False)
        try:
            while not self.stop_event.is_set():
                if time.time() - self.last_check > 60 * 60 * 12:
                    try:
                        check.asset_conservation(self.db, self.stop_event)
                    except check.SanityError as e:
                        logger.error("Asset conservation check failed: %s" % e)
                        _thread.interrupt_main()
                    self.last_check = time.time()
                time.sleep(1)
        finally:
            if self.db is not None:
                self.db.close()
                self.db = None
            logger.info("Thread stopped.")

    def stop(self):
        self.stop_event.set()
        logger.info("Stopping Asset Conservation Checker thread...")
        self.join()


def start_all(args):
    api_status_poller = None
    api_server_v1 = None
    api_server_v2 = None
    follower_daemon = None
    asset_conservation_checker = None
    db = None
    api_stop_event = None

    # Log all config parameters, sorted by key
    # Filter out default values #TODO: these should be set in a different way
    custom_config = {
        k: v
        for k, v in sorted(config.__dict__.items())
        if not k.startswith("__") and not k.startswith("DEFAULT_")
    }
    logger.debug(f"Config: {custom_config}")

    try:
        # download bootstrap if necessary
        if (
            not os.path.exists(config.DATABASE) and args.catch_up == "bootstrap"
        ) or args.catch_up == "bootstrap-always":
            bootstrap.bootstrap(no_confirm=True, snapshot_url=args.bootstrap_url)

        # Initialise database
        db = database.initialise_db()
        blocks.initialise(db)
        blocks.check_database_version(db)
        database.optimize(db)

        if args.rebuild_state_db:
            dbbuilder.build_state_db()
        elif args.refresh_state_db:
            state_db = database.get_db_connection(config.STATE_DATABASE, read_only=False)
            dbbuilder.refresh_state_db(state_db)
            state_db.close()

        # Check software version
        check.software_version()

        # API Server v2
        api_stop_event = multiprocessing.Event()
        api_server_v2 = api_v2.APIServer(api_stop_event)
        api_server_v2.start(args)
        while not api_server_v2.is_ready() and not api_server_v2.has_stopped():
            logger.trace("Waiting for API server to start...")
            time.sleep(0.1)

        # Backend
        connect_to_backend()

        # API Status Poller
        api_status_poller = api_v1.APIStatusPoller()
        api_status_poller.daemon = True
        api_status_poller.start()

        # API Server v1
        api_server_v1 = api_v1.APIServer()
        api_server_v1.daemon = True
        api_server_v1.start()

        # delete blocks with no ledger hashes
        # in case of reparse interrupted
        blocks.rollback_empty_block(db)

        # Asset conservation checker
        if config.CHECK_ASSET_CONSERVATION:
            asset_conservation_checker = AssetConservationChecker()
            asset_conservation_checker.start()

        # Reset (delete) rust fetcher database
        blocks.reset_rust_fetcher_database()

        # catch up
        blocks.catch_up(db)

        # Blockchain watcher
        logger.info("Watching for new blocks...")
        follower_daemon = follow.start_blockchain_watcher(db)
        follower_daemon.start()

    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Shutting down...")
        pass
    except Exception as e:
        logger.error("Exception caught!", exc_info=e)
    finally:
        # Ensure all threads are stopped
        if api_stop_event:
            api_stop_event.set()
        if api_status_poller:
            api_status_poller.stop()
        if api_server_v1:
            api_server_v1.stop()
        if follower_daemon:
            follower_daemon.stop()
        if asset_conservation_checker:
            asset_conservation_checker.stop()
        # then close the database with write access
        if db:
            database.close(db)
        log.shutdown()

        # Now it's safe to check for WAL files
        for db_name, db_path in [
            ("Ledger DB", config.DATABASE),
            ("State DB", config.STATE_DATABASE),
        ]:
            try:
                database.check_wal_file(db_path)
            except exceptions.WALFileFoundError:
                logger.warning(
                    f"{db_name} WAL file detected. To ensure no data corruption has occurred, run `counterparty-server check-db`."
                )
            except exceptions.DatabaseError:
                logger.warning(
                    f"{db_name} is in use by another process and was unable to be closed correctly."
                )

        logger.info("Shutdown complete.")


def reparse(block_index):
    ledger_db = database.initialise_db()

    last_block = ledger.get_last_block(ledger_db)
    if last_block is None or block_index > last_block["block_index"]:
        print(colored("Block index is higher than current block index. No need to reparse.", "red"))
        ledger_db.close()
        return

    state_db = database.get_db_connection(config.STATE_DATABASE, read_only=False)
    try:
        blocks.reparse(ledger_db, block_index=block_index)
        dbbuilder.rollback_state_db(state_db, block_index)
    finally:
        database.optimize(ledger_db)
        database.optimize(state_db)
        ledger_db.close()
        state_db.close()


def rollback(block_index=None):
    ledger_db = database.initialise_db()

    last_block = ledger.get_last_block(ledger_db)
    if last_block is None or block_index > last_block["block_index"]:
        print(
            colored("Block index is higher than current block index. No need to rollback.", "red")
        )
        ledger_db.close()
        return

    state_db = database.get_db_connection(config.STATE_DATABASE, read_only=False)
    try:
        blocks.rollback(ledger_db, block_index=block_index)
        dbbuilder.rollback_state_db(state_db, block_index)
        follow.NotSupportedTransactionsCache().clear()
    finally:
        database.optimize(ledger_db)
        database.optimize(state_db)
        ledger_db.close()
        state_db.close()


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
