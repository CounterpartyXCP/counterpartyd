#! /usr/bin/env python3

import argparse
import logging
import os
from urllib.parse import quote_plus as urlencode

from termcolor import cprint

from counterpartycore import server
from counterpartycore.lib import bootstrap, config, sentry, setup
from counterpartycore.lib.api import dbbuilder

logger = logging.getLogger(config.LOGGER_NAME)

APP_NAME = "counterparty-server"
APP_VERSION = config.VERSION_STRING


def float_range(min_value):
    def float_range_checker(arg):
        try:
            f = float(arg)
        except ValueError as e:
            raise argparse.ArgumentTypeError("must be a floating point number") from e
        if f < min_value:
            raise argparse.ArgumentTypeError(f"must be in greater than or equal to {min_value}")
        return f

    return float_range_checker


CONFIG_ARGS = [
    [
        ("-v", "--verbose"),
        {
            "dest": "verbose",
            "action": "count",
            "default": 0,
            "help": "verbose output (-v for DEBUG, -vv for TRACE)",
        },
    ],
    [
        ("--quiet",),
        {
            "dest": "quiet",
            "action": "store_true",
            "default": False,
            "help": "sets log level to ERROR",
        },
    ],
    [
        ("--mainnet",),
        {
            "action": "store_true",
            "default": True,
            "help": f"use {config.BTC_NAME} mainet addresses and block numbers",
        },
    ],
    [
        ("--testnet3",),
        {
            "action": "store_true",
            "default": False,
            "help": f"use {config.BTC_NAME} testnet3 addresses and block numbers",
        },
    ],
    [
        ("--testnet4",),
        {
            "action": "store_true",
            "default": False,
            "help": f"use {config.BTC_NAME} testnet4 addresses and block numbers",
        },
    ],
    [
        ("--regtest",),
        {
            "action": "store_true",
            "default": False,
            "help": f"use {config.BTC_NAME} regtest addresses and block numbers",
        },
    ],
    [
        ("--api-limit-rows",),
        {
            "type": int,
            "default": 1000,
            "help": "limit api calls to the set results (defaults to 1000). Setting to 0 removes the limit.",
        },
    ],
    [("--backend-name",), {"default": "addrindex", "help": "the backend name to connect to"}],
    [
        ("--backend-connect",),
        {"default": "localhost", "help": "the hostname or IP of the backend server"},
    ],
    [("--backend-port",), {"type": int, "help": "the backend port to connect to"}],
    [
        ("--backend-user",),
        {"default": "rpc", "help": "the username used to communicate with backend"},
    ],
    [
        ("--backend-password",),
        {"default": "rpc", "help": "the password used to communicate with backend"},
    ],
    [
        ("--backend-ssl",),
        {
            "action": "store_true",
            "default": False,
            "help": "use SSL to connect to backend (default: false)",
        },
    ],
    [
        ("--backend-ssl-no-verify",),
        {
            "action": "store_true",
            "default": False,
            "help": "verify SSL certificate of backend; disallow use of self‐signed certificates (default: true)",
        },
    ],
    [
        ("--backend-poll-interval",),
        {
            "type": float_range(3.0),
            "default": 3.0,
            "help": "poll interval, in seconds. Minimum 3.0. (default: 3.0)",
        },
    ],
    [
        ("--skip-asset-conservation-check",),
        {
            "action": "store_true",
            "default": False,
            "help": "Skip asset conservation checking (default: false)",
        },
    ],
    [
        ("--p2sh-dust-return-pubkey",),
        {
            "help": "pubkey to receive dust when multisig encoding is used for P2SH source (default: none)"
        },
    ],
    [
        ("--rpc-host",),
        {
            "default": "127.0.0.1",
            "help": "the IP of the interface to bind to for providing JSON-RPC API access (0.0.0.0 for all interfaces)",
        },
    ],
    [
        ("--rpc-port",),
        {"type": int, "help": f"port on which to provide the {config.APP_NAME} JSON-RPC API"},
    ],
    [
        ("--rpc-user",),
        {
            "default": "rpc",
            "help": f"required username to use the {config.APP_NAME} JSON-RPC API (via HTTP basic auth)",
        },
    ],
    [
        ("--rpc-password",),
        {
            "default": "rpc",
            "help": f"required password (for rpc-user) to use the {config.APP_NAME} JSON-RPC API (via HTTP basic auth)",
        },
    ],
    [
        ("--rpc-no-allow-cors",),
        {"action": "store_true", "default": False, "help": "allow ajax cross domain request"},
    ],
    [
        ("--rpc-batch-size",),
        {
            "type": int,
            "default": config.DEFAULT_RPC_BATCH_SIZE,
            "help": f"number of RPC queries by batch (default: {config.DEFAULT_RPC_BATCH_SIZE})",
        },
    ],
    [
        ("--api-host",),
        {
            "default": "127.0.0.1",
            "help": "the IP of the interface to bind to for providing  API access (0.0.0.0 for all interfaces)",
        },
    ],
    [
        ("--api-port",),
        {"type": int, "help": f"port on which to provide the {config.APP_NAME} API"},
    ],
    [
        ("--api-user",),
        {
            "default": None,
            "help": f"required username to use the {config.APP_NAME} API (via HTTP basic auth)",
        },
    ],
    [
        ("--api-password",),
        {
            "default": None,
            "help": f"required password (for api-user) to use the {config.APP_NAME} API (via HTTP basic auth)",
        },
    ],
    [
        ("--api-no-allow-cors",),
        {"action": "store_true", "default": False, "help": "allow ajax cross domain request"},
    ],
    [
        ("--requests-timeout",),
        {
            "type": int,
            "default": config.DEFAULT_REQUESTS_TIMEOUT,
            "help": "timeout value (in seconds) used for all HTTP requests (default: 5)",
        },
    ],
    [
        ("--force",),
        {
            "action": "store_true",
            "default": False,
            "help": "skip backend check, version check, process lock (NOT FOR USE ON PRODUCTION SYSTEMS)",
        },
    ],
    [
        ("--no-confirm",),
        {"action": "store_true", "default": False, "help": "don't ask for confirmation"},
    ],
    [("--data-dir",), {"default": None, "help": "the path to the data directory"}],
    [("--cache-dir",), {"default": None, "help": "the path to the cache directory"}],
    [
        ("--log-file",),
        {"nargs": "?", "const": None, "default": False, "help": "log to the specified file"},
    ],
    [
        ("--api-log-file",),
        {
            "nargs": "?",
            "const": None,
            "default": False,
            "help": "log API requests to the specified file",
        },
    ],
    [
        ("--no-log-files",),
        {"action": "store_true", "default": False, "help": "Don't write log files"},
    ],
    [
        ("--max-log-file-size",),
        {"type": int, "default": 40 * 1024 * 1024, "help": "maximum size of log files in bytes"},
    ],
    [
        ("--max-log-file-rotations",),
        {"type": int, "default": 20, "help": "maximum number of log file rotations"},
    ],
    [
        ("--log-exclude-filters",),
        {"nargs": "*", "help": "excludes messages whose topic starts with the provided values"},
    ],
    [
        ("--log-include-filters",),
        {
            "nargs": "*",
            "help": "includes only messages whose topic starts with the provided values",
        },
    ],
    [
        ("--utxo-locks-max-addresses",),
        {
            "type": int,
            "default": config.DEFAULT_UTXO_LOCKS_MAX_ADDRESSES,
            "help": "max number of addresses for which to track UTXO locks",
        },
    ],
    [
        ("--utxo-locks-max-age",),
        {
            "type": int,
            "default": config.DEFAULT_UTXO_LOCKS_MAX_AGE,
            "help": "how long to keep a lock on a UTXO being tracked",
        },
    ],
    [
        ("--no-mempool",),
        {"action": "store_true", "default": False, "help": "Disable mempool parsing"},
    ],
    [
        ("--no-telemetry",),
        {
            "action": "store_true",
            "default": False,
            "help": "Do not send anonymous node telemetry data to telemetry server",
        },
    ],
    [
        ("--enable-zmq-publisher",),
        {"action": "store_true", "default": False, "help": "Enable ZeroMQ events publisher"},
    ],
    [
        ("--zmq-publisher-port",),
        {
            "type": int,
            "help": "port on which Counterparty server will publish ZeroMQ notificiations for every event",
        },
    ],
    [
        ("--db-connection-pool-size",),
        {
            "type": int,
            "default": 20,
            "help": "size of the database connection pool",
        },
    ],
    [
        ("--json-logs",),
        {
            "action": "store_true",
            "default": False,
            "help": "show logs in JSON format",
        },
    ],
    [
        ("--wsgi-server",),
        {
            "default": "waitress",
            "help": "WSGI server to use (waitress, gunicorn or werkzeug)",
            "choices": ["waitress", "gunicorn", "werkzeug"],
        },
    ],
    [
        ("--waitress-threads",),
        {
            "type": int,
            "default": 10,
            "help": "number of threads for the Waitress WSGI server (if enabled)",
        },
    ],
    [
        ("--gunicorn-workers",),
        {
            "type": int,
            "default": 2 * os.cpu_count() + 1,
            "help": "number of worker processes for gunicorn (if enabled)",
        },
    ],
    [
        ("--gunicorn-threads-per-worker",),
        {
            "type": int,
            "default": 2,
            "help": "number of threads per worker for the Gunicorn WSGI server (if enabled)",
        },
    ],
    [("--bootstrap-url",), {"type": str, "help": "the URL of the bootstrap snapshot to use"}],
    [
        ("--electrs-url",),
        {
            "help": "the complete URL of the Electrs API, possibly including a specific port, for example: `https://mempool.space/api`",
        },
    ],
    [
        ("--refresh-state-db",),
        {
            "help": "On startup, rebuild non rollbackable tables in the state database",
            "action": "store_true",
            "default": False,
        },
    ],
    [
        ("--rebuild-state-db",),
        {
            "help": "On startup, rebuild all tables in the state database",
            "action": "store_true",
            "default": False,
        },
    ],
]


def welcome_message(action, server_configfile):
    cprint(f"\nCounterparty Core v{config.__version__}", "white", attrs=["bold"])

    # print some info
    cprint(f"Verbosity: {config.VERBOSE}", "light_grey")
    cprint(f"Quiet: {config.QUIET}", "light_grey")
    cprint(f"Network: {config.NETWORK_NAME}", "light_grey")
    cprint(f"Configuration File: {server_configfile}", "light_grey")
    cprint(f"Counterparty Database: {config.DATABASE}", "light_grey")
    cprint(f"Counterparty State Database: {config.STATE_DATABASE}", "light_grey")
    cprint(f"Rust Fetcher Database: {config.FETCHER_DB}", "light_grey")

    if config.VERBOSE:
        pass_str = f":{urlencode(config.BACKEND_PASSWORD)}@"
        cleaned_backend_url = config.BACKEND_URL.replace(pass_str, ":*****@")
        cprint(f"Bitcoin Core: {cleaned_backend_url}", "light_grey")

        api_url = "http://"
        if config.API_USER and config.API_PASSWORD:
            api_url += f"{config.API_USER}:*****@"
        api_url += f"{config.API_HOST}:{config.API_PORT}/v2/"
        cprint(f"Counterparty API Server: {api_url}", "light_grey")

    if config.LOG:
        cprint(f"Server Log: {config.LOG}", "light_grey")
    else:
        cprint("Warning: Server logging disabled", "yellow")
    if config.API_LOG:
        cprint(f"API Access Log: {config.API_LOG}", "light_grey")
    else:
        cprint("Warning: API access log disabled", "yellow")

    cprint(f"\n{'-' * 30} {action.upper()} {'-' * 30}\n", "green")


class VersionError(Exception):
    pass


def main():
    sentry.init()
    # Post installation tasks
    server_configfile = setup.generate_server_config_file(CONFIG_ARGS)

    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"Server for the {config.XCP_NAME} protocol",
        add_help=False,
        exit_on_error=False,
    )
    parser.add_argument(
        "-h", "--help", dest="help", action="store_true", help="show this help message and exit"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{APP_NAME} v{APP_VERSION}; counterparty-core v{config.VERSION_STRING}",
    )
    parser.add_argument("--config-file", help="the path to the configuration file")

    cmd_args = parser.parse_known_args()[0]
    config_file_path = getattr(cmd_args, "config_file", None)
    configfile = setup.read_config_file("server.conf", config_file_path)

    setup.add_config_arguments(parser, CONFIG_ARGS, configfile, add_default=True)

    subparsers = parser.add_subparsers(dest="action", help="the action to be taken")

    parser_server = subparsers.add_parser("start", help="run the server")
    parser_server.add_argument("--config-file", help="the path to the configuration file")
    parser_server.add_argument(
        "--catch-up",
        choices=["normal", "bootstrap", "bootstrap-always"],
        default="normal",
        help="Catch up mode (default: normal)",
    )
    setup.add_config_arguments(parser_server, CONFIG_ARGS, configfile)

    parser_reparse = subparsers.add_parser(
        "reparse", help="reparse all transactions in the database"
    )
    parser_reparse.add_argument(
        "block_index", type=int, help="the index of the last known good block"
    )
    setup.add_config_arguments(parser_reparse, CONFIG_ARGS, configfile)

    parser_vacuum = subparsers.add_parser(
        "vacuum", help="VACUUM the database (to improve performance)"
    )
    setup.add_config_arguments(parser_vacuum, CONFIG_ARGS, configfile)

    parser_rollback = subparsers.add_parser("rollback", help="rollback database")
    parser_rollback.add_argument(
        "block_index", type=int, help="the index of the last known good block"
    )
    setup.add_config_arguments(parser_rollback, CONFIG_ARGS, configfile)

    parser_bootstrap = subparsers.add_parser(
        "bootstrap", help="bootstrap database with hosted snapshot"
    )
    setup.add_config_arguments(parser_bootstrap, CONFIG_ARGS, configfile)

    parser_checkdb = subparsers.add_parser("check-db", help="do an integrity check on the database")
    setup.add_config_arguments(parser_checkdb, CONFIG_ARGS, configfile)

    parser_show_config = subparsers.add_parser(
        "show-params", help="Show counterparty-server configuration"
    )
    setup.add_config_arguments(parser_show_config, CONFIG_ARGS, configfile)

    parser_show_config = subparsers.add_parser(
        "build-state-db", help="Build the API database from the ledger database"
    )
    setup.add_config_arguments(parser_show_config, CONFIG_ARGS, configfile)

    args = parser.parse_args()

    # Help message
    if args.help:
        parser.print_help()
        exit(0)

    if args.action is None:
        parser.print_help()
        exit(1)

    # Configuration and logging
    server.initialise_log_and_config(args)

    welcome_message(args.action, server_configfile)

    # Bootstrapping
    if args.action == "bootstrap":
        bootstrap.bootstrap(no_confirm=args.no_confirm, snapshot_url=args.bootstrap_url)

    # PARSING
    elif args.action == "reparse":
        server.reparse(block_index=args.block_index)

    elif args.action == "rollback":
        server.rollback(block_index=args.block_index)

    elif args.action == "start":
        server.start_all(args)

    elif args.action == "show-params":
        server.show_params()

    elif args.action == "vacuum":
        server.vacuum()

    elif args.action == "check-db":
        server.check_database()

    elif args.action == "build-state-db":
        dbbuilder.build_state_db()

    else:
        parser.print_help()
