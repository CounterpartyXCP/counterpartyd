#! /usr/bin/env python3

import argparse
import logging
from urllib.parse import quote_plus as urlencode

from termcolor import cprint

from counterpartycore import server
from counterpartycore.lib import config, setup

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
        ("--testnet",),
        {
            "action": "store_true",
            "default": False,
            "help": f"use {config.BTC_NAME} testnet addresses and block numbers",
        },
    ],
    [
        ("--testcoin",),
        {
            "action": "store_true",
            "default": False,
            "help": f"use the test {config.XCP_NAME} network on every blockchain",
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
        ("--customnet",),
        {
            "default": "",
            "help": "use a custom network (specify as UNSPENDABLE_ADDRESS|ADDRESSVERSION|P2SH_ADDRESSVERSION with version bytes in HH hex format)",
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
        ("--check-asset-conservation",),
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
        ("--indexd-connect",),
        {"default": "localhost", "help": "the hostname or IP of the indexd server"},
    ],
    [("--indexd-port",), {"type": int, "help": "the indexd server port to connect to"}],
    [
        ("--rpc-host",),
        {
            "default": "localhost",
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
            "default": "localhost",
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
    [("--database-file",), {"default": None, "help": "the path to the SQLite3 database file"}],
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
        ("--zmq-sequence-port",),
        {
            "type": int,
            "help": "port on which bitcoind will publish ZMQ notificiations for `sequence` topic",
        },
    ],
    [
        ("--zmq-rawblock-port",),
        {
            "type": int,
            "help": "port on which bitcoind will publish ZMQ notificiations for `rawblock` topic",
        },
    ],
]


def welcome_message(action, server_configfile):
    cprint(f"Running v{config.__version__} of {config.FULL_APP_NAME}.", "magenta")

    # print some info
    cprint(f"Configuration file: {server_configfile}", "light_grey")
    cprint(f"Counterparty database: {config.DATABASE}", "light_grey")
    if config.LOG:
        cprint(f"Writing log to file: `{config.LOG}`", "light_grey")
    else:
        cprint("Warning: log disabled", "yellow")
    if config.API_LOG:
        cprint(f"Writing API accesses log to file: `{config.API_LOG}`", "light_grey")
    else:
        cprint("Warning: API log disabled", "yellow")

    if config.VERBOSE:
        if config.TESTNET:
            cprint("NETWORK: Testnet", "light_grey")
        elif config.REGTEST:
            cprint("NETWORK: Regtest", "light_grey")
        else:
            cprint("NETWORK: Mainnet", "light_grey")

        pass_str = f":{urlencode(config.BACKEND_PASSWORD)}@"
        cleaned_backend_url = config.BACKEND_URL.replace(pass_str, ":*****@")
        cprint(f"BACKEND_URL: {cleaned_backend_url}", "light_grey")
        cprint(f"INDEXD_URL: {config.INDEXD_URL}", "light_grey")
        pass_str = f":{urlencode(config.RPC_PASSWORD)}@"
        cleaned_rpc_url = config.RPC.replace(pass_str, ":*****@")
        cprint(f"RPC: {cleaned_rpc_url}", "light_grey")

    cprint(f"{'-' * 30} {action} {'-' * 30}\n", "green")


class VersionError(Exception):
    pass


def main():
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
        choices=["normal", "bootstrap"],
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

    parser_kickstart = subparsers.add_parser(
        "kickstart", help="rapidly build database by reading from Bitcoin Core blockchain"
    )
    parser_kickstart.add_argument("--bitcoind-dir", help="Bitcoin Core data directory")
    parser_kickstart.add_argument(
        "--max-queue-size", type=int, help="Size of the multiprocessing.Queue for parsing blocks"
    )
    parser_kickstart.add_argument(
        "--debug-block", type=int, help="Rollback and run kickstart for a single block;"
    )
    setup.add_config_arguments(parser_kickstart, CONFIG_ARGS, configfile)

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

    args = parser.parse_args()

    # Help message
    if args.help:
        parser.print_help()
        exit(0)

    # Configuration and logging
    server.initialise_log_and_config(args)

    logger.info(f"Running v{APP_VERSION} of {APP_NAME}.")

    welcome_message(args.action, server_configfile)

    # Bootstrapping
    if args.action == "bootstrap":
        server.bootstrap(no_confirm=args.no_confirm)

    # PARSING
    elif args.action == "reparse":
        server.reparse(block_index=args.block_index)

    elif args.action == "rollback":
        server.rollback(block_index=args.block_index)

    elif args.action == "kickstart":
        server.kickstart(
            bitcoind_dir=args.bitcoind_dir,
            force=args.force,
            max_queue_size=args.max_queue_size,
            debug_block=args.debug_block,
        )

    elif args.action == "start":
        server.start_all(args)

    elif args.action == "show-params":
        server.show_params()

    elif args.action == "vacuum":
        server.vacuum()

    elif args.action == "check-db":
        server.check_database()
    else:
        parser.print_help()
