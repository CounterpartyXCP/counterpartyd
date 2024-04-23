import argparse
import logging
import multiprocessing
import signal
from multiprocessing import Process
from threading import Timer

import flask
from counterpartycore import server
from counterpartycore.lib import (
    blocks,
    config,
    database,
    ledger,
)
from counterpartycore.lib.api.routes import ROUTES
from counterpartycore.lib.api.util import (
    get_backend_height,
    init_api_access_log,
    remove_rowids,
    to_json,
)
from flask import Flask, request
from flask import g as flask_globals
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(config.LOGGER_NAME)
auth = HTTPBasicAuth()

BACKEND_HEIGHT = 0
REFRESH_BACKEND_HEIGHT_INTERVAL = 10
BACKEND_HEIGHT_TIMER = None


def get_db():
    """Get the database connection."""
    if not hasattr(flask_globals, "db"):
        flask_globals.db = database.get_connection(read_only=True)
    return flask_globals.db


@auth.verify_password
def verify_password(username, password):
    return username == config.API_USER and password == config.API_PASSWORD


def api_root():
    counterparty_height = blocks.last_db_index(get_db())
    routes = []
    for path in ROUTES:
        route = ROUTES[path]
        routes.append(
            {
                "path": path,
                "args": route.get("args", []),
                "description": route.get("description", ""),
            }
        )
    network = "mainnet"
    if config.TESTNET:
        network = "testnet"
    elif config.REGTEST:
        network = "regtest"
    elif config.TESTCOIN:
        network = "testcoin"
    return {
        "server_ready": counterparty_height >= BACKEND_HEIGHT,
        "network": network,
        "version": config.VERSION_STRING,
        "backend_height": BACKEND_HEIGHT,
        "counterparty_height": counterparty_height,
        "routes": routes,
    }


def inject_headers(result, return_code=None):
    server_ready = ledger.CURRENT_BLOCK_INDEX >= BACKEND_HEIGHT
    http_code = 200
    if return_code:
        http_code = return_code
    elif not server_ready:
        http_code = config.API_NOT_READY_HTTP_CODE
    if isinstance(result, flask.Response):
        response = result
    else:
        response = flask.make_response(to_json(result), http_code)
    response.headers["X-COUNTERPARTY-HEIGHT"] = ledger.CURRENT_BLOCK_INDEX
    response.headers["X-COUNTERPARTY-READY"] = ledger.CURRENT_BLOCK_INDEX >= BACKEND_HEIGHT
    response.headers["X-BACKEND-HEIGHT"] = BACKEND_HEIGHT
    response.headers["Content-Type"] = "application/json"
    return response


def prepare_args(route, **kwargs):
    function_args = dict(kwargs)
    if "pass_all_args" in route and route["pass_all_args"]:
        function_args = request.args | function_args
    elif "args" in route:
        for arg in route["args"]:
            arg_name = arg["name"]
            if arg_name in function_args:
                continue
            str_arg = request.args.get(arg_name)
            if str_arg is None and arg["required"]:
                raise ValueError(f"Missing required parameter: {arg_name}")
            if str_arg is None:
                function_args[arg_name] = arg["default"]
            elif arg["type"] == "bool":
                function_args[arg_name] = str_arg.lower() in ["true", "1"]
            elif arg["type"] == "int":
                try:
                    function_args[arg_name] = int(str_arg)
                except ValueError as e:
                    raise ValueError(f"Invalid integer: {arg_name}") from e
            else:
                function_args[arg_name] = str_arg
    return function_args


@auth.login_required
def handle_route(**kwargs):
    db = get_db()
    # update the current block index
    ledger.CURRENT_BLOCK_INDEX = blocks.last_db_index(db)
    rule = str(request.url_rule.rule)
    if rule == "/":
        result = api_root()
    else:
        route = ROUTES.get(rule)
        try:
            function_args = prepare_args(route, **kwargs)
        except ValueError as e:
            return inject_headers({"error": str(e)}, return_code=400)
        result = route["function"](db, **function_args)
        result = remove_rowids(result)
    return inject_headers(result)


def run_api_server(args):
    # default signal handlers
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)

    app = Flask(config.APP_NAME)
    # Initialise log and config
    server.initialise_log_and_config(argparse.Namespace(**args))
    with app.app_context():
        if not config.API_NO_ALLOW_CORS:
            CORS(app)
        # Initialise the API access log
        init_api_access_log(app)
        # Get the last block index
        ledger.CURRENT_BLOCK_INDEX = blocks.last_db_index(get_db())
        # Add routes
        app.add_url_rule("/", view_func=handle_route)
        for path in ROUTES:
            app.add_url_rule(path, view_func=handle_route)
        # run the scheduler to refresh the backend height
        # `no_refresh_backend_height` used only for testing. TODO: find a way to mock it
        if "no_refresh_backend_height" not in args or not args["no_refresh_backend_height"]:
            refresh_backend_height()
    try:
        # Start the API server
        app.run(host=config.API_HOST, port=config.API_PORT, debug=False)
    finally:
        # ensure timer is cancelled
        if BACKEND_HEIGHT_TIMER:
            BACKEND_HEIGHT_TIMER.cancel()


def refresh_backend_height():
    global BACKEND_HEIGHT, BACKEND_HEIGHT_TIMER  # noqa F811
    BACKEND_HEIGHT = get_backend_height()
    if BACKEND_HEIGHT_TIMER:
        BACKEND_HEIGHT_TIMER.cancel()
    BACKEND_HEIGHT_TIMER = Timer(REFRESH_BACKEND_HEIGHT_INTERVAL, refresh_backend_height)
    BACKEND_HEIGHT_TIMER.start()


class APIServer(object):
    def __init__(self):
        self.process = None

    def start(self, args):
        if self.process is not None:
            raise Exception("API server is already running")
        self.process = Process(target=run_api_server, args=(vars(args),))
        self.process.start()
        return self.process

    def stop(self):
        logger.info("Stopping API server v2...")
        if self.process and self.process.is_alive():
            self.process.terminate()
        self.process = None