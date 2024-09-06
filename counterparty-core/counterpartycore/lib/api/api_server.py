import argparse
import logging
import multiprocessing
import os
import time
from collections import OrderedDict
from multiprocessing import Process, Value
from threading import Thread, Timer

import flask
import requests
from bitcoin.wallet import CBitcoinAddressError
from counterpartycore import server
from counterpartycore.lib import (
    backend,
    config,
    exceptions,
    ledger,
    sentry,
    transaction,
    util,
)
from counterpartycore.lib.api import api_watcher, queries
from counterpartycore.lib.api.routes import ROUTES
from counterpartycore.lib.api.util import (
    clean_rowids_and_confirmed_fields,
    function_needs_db,
    get_backend_height,
    init_api_access_log,
    inject_details,
    to_json,
)
from counterpartycore.lib.database import APIDBConnectionPool, get_db_connection
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from sentry_sdk import capture_exception
from sentry_sdk import configure_scope as configure_sentry_scope
from werkzeug.serving import make_server

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(config.LOGGER_NAME)
auth = HTTPBasicAuth()

BACKEND_HEIGHT = None
CURRENT_BLOCK_TIME = None
REFRESH_BACKEND_HEIGHT_INTERVAL = 10
BACKEND_HEIGHT_TIMER = None
BLOCK_CACHE = OrderedDict()
MAX_BLOCK_CACHE_SIZE = 1000

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
BLUEPRINT_FILEPATH = os.path.join(CURR_DIR, "..", "..", "..", "..", "apiary.apib")


@auth.verify_password
def verify_password(username, password):
    if config.API_PASSWORD is None:
        return True
    return username == config.API_USER and password == config.API_PASSWORD


def api_root():
    with APIDBConnectionPool().connection() as db:
        counterparty_height = ledger.last_db_index(db)
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
        "documentation": "https://counterpartycore.docs.apiary.io/",
        "blueprint": f"{request.url_root}v2/blueprint",
    }


def is_server_ready():
    # TODO: find a way to mock this function for testing
    try:
        if request.url_root == "http://localhost:10009/":
            return True
    except RuntimeError:
        pass
    if BACKEND_HEIGHT is None:
        return False
    if util.CURRENT_BLOCK_INDEX in [BACKEND_HEIGHT, BACKEND_HEIGHT - 1]:
        return True
    if time.time() - CURRENT_BLOCK_TIME < 60:
        return True
    return False


def is_cachable(rule):
    if rule.startswith("/v2/blocks"):
        return True
    if rule.startswith("/v2/transactions"):
        return True
    if rule.startswith("/v2/bitcoin"):
        return True
    return False


def return_result_if_not_ready(rule):
    return (
        is_cachable(rule)
        or rule == "/v2/"
        or rule == "/"
        or rule.startswith("/v1")
        or rule.startswith("/rpc")
    )


def get_log_prefix(query_args=None):
    rule = str(request.url_rule.rule)
    if rule == "/v2/":
        query_name = "API Root"
    else:
        route = ROUTES.get(rule)
        query_name = " ".join(
            [part.capitalize() for part in str(route["function"].__name__).split("_")]
        )
    message = f"API Request - {query_name}"

    if query_args:
        query_args_str = " ".join([f"{k}={v}" for k, v in query_args.items()])
        message += f" ({query_args_str})"

    return message


def return_result(
    http_code,
    result=None,
    error=None,
    next_cursor=None,
    result_count=None,
    start_time=None,
    query_args=None,
):
    assert result is None or error is None
    api_result = {}
    if result is not None:
        api_result["result"] = result
        if isinstance(result, list):
            api_result["next_cursor"] = next_cursor
            api_result["result_count"] = result_count
    if error is not None:
        api_result["error"] = error
    response = flask.make_response(to_json(api_result), http_code)
    response.headers["X-COUNTERPARTY-HEIGHT"] = util.CURRENT_BLOCK_INDEX
    response.headers["X-COUNTERPARTY-READY"] = is_server_ready()
    response.headers["X-BITCOIN-HEIGHT"] = BACKEND_HEIGHT
    response.headers["Content-Type"] = "application/json"
    if not config.API_NO_ALLOW_CORS:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"

    if http_code != 404:
        message = get_log_prefix(query_args)
    else:
        message = f"API Request - {request.path}"

    message += f" - Response {http_code}"
    if error:
        message += f" ({error})"
    if start_time:
        message += f" - {int((time.time() - start_time) * 1000)}ms"

    logger.debug(message)

    return response


def prepare_args(route, **kwargs):
    function_args = dict(kwargs)
    # inject args from request.args
    for arg in route["args"]:
        arg_name = arg["name"]
        if arg_name in ["verbose", "show_unconfirmed"]:
            continue
        if arg_name in function_args:
            continue

        str_arg = request.args.get(arg_name)
        if str_arg is not None and str_arg.lower() == "none":
            str_arg = None
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
        elif arg["type"] == "float":
            try:
                function_args[arg_name] = float(str_arg)
            except ValueError as e:
                raise ValueError(f"Invalid float: {arg_name}") from e
        else:
            function_args[arg_name] = str_arg

    return function_args


def execute_api_function(db, rule, route, function_args):
    # cache everything for one block
    cache_key = f"{util.CURRENT_BLOCK_INDEX}:{request.url}"
    # except for blocks and transactions cached forever
    if (
        request.path.startswith("/v2/blocks/") or request.path.startswith("/v2/transactions/")
    ) and not request.path.startswith("/v2/blocks/last"):
        cache_key = request.url

    if cache_key in BLOCK_CACHE:
        result = BLOCK_CACHE[cache_key]
    else:
        if function_needs_db(route["function"]):
            result = route["function"](db, **function_args)
        else:
            result = route["function"](**function_args)
        # don't cache API v1 and mempool queries
        if (
            is_cachable(rule)
            and route["function"].__name__ != "redirect_to_api_v1"
            and not request.path.startswith("/v2/mempool/")
        ):
            BLOCK_CACHE[cache_key] = result
            if len(BLOCK_CACHE) > MAX_BLOCK_CACHE_SIZE:
                BLOCK_CACHE.popitem(last=False)

    return result


def get_transaction_name(rule):
    if rule == "/v2/":
        return "APIRoot"
    if rule == "/healthz":
        return "healthcheck"
    return "".join([part.capitalize() for part in ROUTES[rule]["function"].__name__.split("_")])


def refresh_current_block(db):
    # update the current block index
    global CURRENT_BLOCK_TIME  # noqa F811
    last_block = ledger.get_last_block(db)
    if last_block:
        util.CURRENT_BLOCK_INDEX = last_block["block_index"]
        CURRENT_BLOCK_TIME = last_block["block_time"]
    else:
        util.CURRENT_BLOCK_INDEX = 0
        CURRENT_BLOCK_TIME = 0


@auth.login_required
def handle_route(**kwargs):
    start_time = time.time()
    query_args = request.args.to_dict() | kwargs

    logger.trace(f"API Request - {request.remote_addr} {request.method} {request.url}")
    logger.debug(get_log_prefix(query_args))

    if BACKEND_HEIGHT is None:
        return return_result(
            503,
            error="Backend still not ready. Please try again later.",
            start_time=start_time,
            query_args=query_args,
        )

    rule = str(request.url_rule.rule)

    with configure_sentry_scope() as scope:
        scope.set_transaction_name(get_transaction_name(rule))

    if not is_server_ready() and not return_result_if_not_ready(rule):
        return return_result(
            503, error="Counterparty not ready", start_time=start_time, query_args=query_args
        )

    if rule == "/v2/":
        return return_result(200, result=api_root(), start_time=start_time, query_args=query_args)

    route = ROUTES.get(rule)

    # parse args
    try:
        function_args = prepare_args(route, **kwargs)
    except ValueError as e:
        return return_result(400, error=str(e), start_time=start_time, query_args=query_args)

    logger.trace(f"API Request - Arguments: {function_args}")

    # call the function
    try:
        with APIDBConnectionPool().connection() as db:
            result = execute_api_function(db, rule, route, function_args)
    except (
        exceptions.JSONRPCInvalidRequest,
        exceptions.TransactionError,
        exceptions.BalanceError,
        exceptions.UnknownPubKeyError,
        exceptions.AssetNameError,
        exceptions.BitcoindRPCError,
        exceptions.ComposeError,
        exceptions.UnpackError,
        CBitcoinAddressError,
    ) as e:
        return return_result(400, error=str(e), start_time=start_time, query_args=query_args)
    except Exception as e:
        capture_exception(e)
        logger.error("Error in API: %s", e)
        import traceback

        print(traceback.format_exc())  # for debugging
        return return_result(
            503, error="Unknown error", start_time=start_time, query_args=query_args
        )

    if isinstance(result, requests.Response):
        return result.content, result.status_code, result.headers.items()

    # clean up and return the result
    if result is None:
        return return_result(404, error="Not found", start_time=start_time, query_args=query_args)

    next_cursor = None
    result_count = None
    if isinstance(result, queries.QueryResult):
        next_cursor = result.next_cursor
        result_count = result.result_count
        result = result.result

    result = clean_rowids_and_confirmed_fields(result)

    # inject details
    verbose = request.args.get("verbose", "False")
    if verbose.lower() in ["true", "1"]:
        result = inject_details(db, result)

    return return_result(
        200,
        result=result,
        next_cursor=next_cursor,
        result_count=result_count,
        start_time=start_time,
        query_args=query_args,
    )


def handle_not_found(error):
    return return_result(404, error="Not found")


def handle_doc():
    return flask.send_file(BLUEPRINT_FILEPATH)


def run_api_server(args, interruped_value, server_ready_value):
    sentry.init()
    # Initialise log and config
    server.initialise_log_and_config(argparse.Namespace(**args))

    watcher = api_watcher.APIWatcher()
    watcher.start()

    logger.info("Starting API Server...")
    app = Flask(config.APP_NAME)
    transaction.initialise()
    with app.app_context():
        # Initialise the API access log
        init_api_access_log(app)
        # Get the last block index
        with APIDBConnectionPool().connection() as db:
            util.CURRENT_BLOCK_INDEX = ledger.last_db_index(db)
        # Add routes
        app.add_url_rule("/v2/", view_func=handle_route, strict_slashes=False)
        app.add_url_rule(
            "/v2/blueprint", view_func=handle_doc, methods=["GET"], strict_slashes=False
        )

        for path in ROUTES:
            methods = ["GET"]
            if path == "/v2/bitcoin/transactions":
                methods = ["POST"]
            if not path.startswith("/v2/"):
                methods = ["GET", "POST"]
            app.add_url_rule(path, view_func=handle_route, methods=methods, strict_slashes=False)

        app.register_error_handler(404, handle_not_found)
        # run the scheduler to refresh the backend height
        # `no_refresh_backend_height` used only for testing. TODO: find a way to mock it
        timer_db = get_db_connection(config.API_DATABASE, read_only=True, check_wal=False)
        if "no_refresh_backend_height" not in args or not args["no_refresh_backend_height"]:
            refresh_backend_height(timer_db, start=True)
        else:
            refresh_current_block(timer_db)
            global BACKEND_HEIGHT  # noqa F811
            BACKEND_HEIGHT = 0
    try:
        # Init the HTTP Server.
        werkzeug_server = make_server(config.API_HOST, config.API_PORT, app, threaded=True)
        ParentProcessChecker(interruped_value, werkzeug_server).start()
        app.app_context().push()
        # Run app server (blocking)
        server_ready_value.value = 1
        werkzeug_server.serve_forever()
    except KeyboardInterrupt:
        logger.trace("Keyboard Interrupt!")
    finally:
        logger.trace("Shutting down API Server...")
        watcher.stop()
        watcher.join()
        werkzeug_server.shutdown()
        # ensure timer is cancelled
        if BACKEND_HEIGHT_TIMER:
            BACKEND_HEIGHT_TIMER.cancel()
        if timer_db:
            timer_db.close()
        APIDBConnectionPool().close()


def refresh_backend_height(db, start=False):
    global BACKEND_HEIGHT, BACKEND_HEIGHT_TIMER  # noqa F811
    if not start:
        BACKEND_HEIGHT = get_backend_height()
        refresh_current_block(db)
        backend.addrindexrs.clear_raw_transactions_cache()
        if not is_server_ready():
            if BACKEND_HEIGHT > util.CURRENT_BLOCK_INDEX:
                logger.debug(
                    f"Counterparty is currently behind Bitcoin Core. ({util.CURRENT_BLOCK_INDEX} < {BACKEND_HEIGHT})"
                )
            else:
                logger.debug(
                    f"Bitcoin Core is currently behind the network. ({util.CURRENT_BLOCK_INDEX} > {BACKEND_HEIGHT})"
                )
    else:
        # starting the timer is not blocking in case of Addrindexrs is not ready
        BACKEND_HEIGHT_TIMER = Timer(0.5, refresh_backend_height, (db,))
        BACKEND_HEIGHT_TIMER.start()
        return
    if BACKEND_HEIGHT_TIMER:
        BACKEND_HEIGHT_TIMER.cancel()
    BACKEND_HEIGHT_TIMER = Timer(REFRESH_BACKEND_HEIGHT_INTERVAL, refresh_backend_height, (db,))
    BACKEND_HEIGHT_TIMER.start()


# This thread is used for the following two reasons:
# 1. `docker-compose stop` does not send a SIGTERM to the child processes (in this case the API v2 process)
# 2. `process.terminate()` does not trigger a `KeyboardInterrupt` or execute the `finally` block.
class ParentProcessChecker(Thread):
    def __init__(self, interruped_value, werkzeug_server):
        super().__init__()
        self.interruped_value = interruped_value
        self.werkzeug_server = werkzeug_server

    def run(self):
        try:
            while True:
                if self.interruped_value.value == 0:
                    time.sleep(0.01)
                else:
                    logger.trace("Parent process is dead. Exiting...")
                    break
            self.werkzeug_server.shutdown()
        except KeyboardInterrupt:
            pass


class APIServer(object):
    def __init__(self):
        self.process = None
        self.interrupted = Value("I", 0)
        self.server_ready_value = Value("I", 0)

    def start(self, args):
        if self.process is not None:
            raise Exception("API Server is already running")
        self.process = Process(
            target=run_api_server, args=(vars(args), self.interrupted, self.server_ready_value)
        )
        self.process.start()
        return self.process

    def is_ready(self):
        return self.server_ready_value.value == 1

    def stop(self):
        logger.info("Stopping API Server...")
        self.interrupted.value = 1
        waiting_start_time = time.time()
        while self.process.is_alive():
            time.sleep(0.5)
            logger.trace("Waiting for API Server to stop...")
            if time.time() - waiting_start_time > 2:
                logger.error("API Server did not stop in time. Terminating...")
                self.process.kill()
                break
        logger.trace("API Server stopped.")
