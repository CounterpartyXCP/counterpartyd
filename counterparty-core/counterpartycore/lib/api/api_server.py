import argparse
import logging
import multiprocessing
import os
import signal
import threading
import time
from collections import OrderedDict
from multiprocessing import Process, Value

import flask
import requests
from bitcoin.wallet import CBitcoinAddressError
from counterpartycore import server
from counterpartycore.lib import (
    check,
    config,
    database,
    exceptions,
    ledger,
    script,
    sentry,
    util,
)
from counterpartycore.lib.api import api_watcher, dbbuilder, queries, wsgi
from counterpartycore.lib.api.routes import ROUTES
from counterpartycore.lib.api.util import (
    clean_rowids_and_confirmed_fields,
    function_needs_db,
    init_api_access_log,
    inject_details,
    to_json,
)
from counterpartycore.lib.database import LedgerDBConnectionPool, StateDBConnectionPool
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from sentry_sdk import capture_exception
from sentry_sdk import configure_scope as configure_sentry_scope
from sentry_sdk import start_span as start_sentry_span

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(config.LOGGER_NAME)
auth = HTTPBasicAuth()


BLOCK_CACHE = OrderedDict()
MAX_BLOCK_CACHE_SIZE = 1000

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
BLUEPRINT_FILEPATH = os.path.join(CURR_DIR, "..", "..", "..", "..", "apiary.apib")


@auth.verify_password
def verify_password(username, password):
    if config.API_PASSWORD is None:
        return True
    return username == config.API_USER and password == config.API_PASSWORD


def is_server_ready():
    # TODO: find a way to mock this function for testing
    try:
        if request.url_root == "http://localhost:10009/":
            return True
    except RuntimeError:
        pass
    if util.CURRENT_BACKEND_HEIGHT is None:
        return False
    if util.CURRENT_BLOCK_INDEX in [util.CURRENT_BACKEND_HEIGHT, util.CURRENT_BACKEND_HEIGHT - 1]:
        return True
    if util.CURRENT_BLOCK_TIME is None:
        return False
    if time.time() - util.CURRENT_BLOCK_TIME < 60:
        return True
    return False


def api_root():
    with StateDBConnectionPool().connection() as state_db:
        counterparty_height = api_watcher.get_last_block_parsed(state_db)

    backend_height = util.CURRENT_BACKEND_HEIGHT
    if backend_height is None:
        if config.FORCE:
            server_ready = True
        else:
            server_ready = False
    else:
        server_ready = counterparty_height >= backend_height

    return {
        "server_ready": server_ready,
        "network": config.NETWORK_NAME,
        "version": config.VERSION_STRING,
        "backend_height": util.CURRENT_BACKEND_HEIGHT,
        "counterparty_height": counterparty_height,
        "documentation": "https://counterpartycore.docs.apiary.io/",
        "routes": f"{request.url_root}v2/routes",
        "blueprint": "https://raw.githubusercontent.com/CounterpartyXCP/counterparty-core/refs/heads/master/apiary.apib",
    }


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


def set_cors_headers(response):
    if not config.API_NO_ALLOW_CORS:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"


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
    response.headers["X-COUNTERPARTY-VERSION"] = config.VERSION_STRING
    response.headers["X-BITCOIN-HEIGHT"] = util.CURRENT_BACKEND_HEIGHT
    response.headers["Content-Type"] = "application/json"
    set_cors_headers(response)

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
        if arg_name in ["verbose"] and "compose" not in route["function"].__name__:
            continue
        if arg_name in function_args:
            continue

        str_arg = query_params().get(arg_name)
        if str_arg is not None and isinstance(str_arg, str) and str_arg.lower() == "none":
            str_arg = None
        if str_arg is None and arg["required"]:
            raise ValueError(f"Missing required parameter: {arg_name}")

        if arg["type"] != "list" and isinstance(str_arg, list):
            str_arg = str_arg[0]  # we take the first argument

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
        elif arg["type"] == "list":
            if not isinstance(str_arg, list):
                function_args[arg_name] = [str_arg]
            else:
                function_args[arg_name] = str_arg
        else:
            function_args[arg_name] = str_arg

    return function_args


def execute_api_function(rule, route, function_args):
    # cache everything for one block
    with StateDBConnectionPool().connection() as state_db:
        current_block_index = api_watcher.get_last_block_parsed(state_db)
    cache_key = f"{current_block_index}:{request.url}"
    # except for blocks and transactions cached forever
    if (
        request.path.startswith("/v2/blocks/") or request.path.startswith("/v2/transactions/")
    ) and not request.path.startswith("/v2/blocks/last"):
        cache_key = request.url

    with start_sentry_span(op="cache.get") as sentry_get_span:
        sentry_get_span.set_data("cache.key", cache_key)
        if cache_key in BLOCK_CACHE:
            result = BLOCK_CACHE[cache_key]
            sentry_get_span.set_data("cache.hit", True)
            return result
        else:
            sentry_get_span.set_data("cache.hit", False)

    with start_sentry_span(op="cache.put") as sentry_put_span:
        needed_db = function_needs_db(route["function"])
        if needed_db == "ledger_db":
            with LedgerDBConnectionPool().connection() as ledger_db:
                result = route["function"](ledger_db, **function_args)
        elif needed_db == "state_db":
            with StateDBConnectionPool().connection() as state_db:
                result = route["function"](state_db, **function_args)
        elif needed_db == "ledger_db state_db":
            with LedgerDBConnectionPool().connection() as ledger_db:
                with StateDBConnectionPool().connection() as state_db:
                    result = route["function"](ledger_db, state_db, **function_args)
        else:
            result = route["function"](**function_args)
        # don't cache API v1 and mempool queries
        if (
            result is not None
            and is_cachable(rule)
            and route["function"].__name__ != "redirect_to_api_v1"
            and not request.path.startswith("/v2/mempool/")
        ):
            sentry_put_span.set_data("cache.key", cache_key)
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


def query_params():
    params = request.args.to_dict(flat=False)
    return {key: value[0] if len(value) == 1 else value for key, value in params.items()}


@auth.login_required
def handle_route(**kwargs):
    if request.method == "OPTIONS":
        return handle_options()

    start_time = time.time()
    query_args = query_params() | kwargs

    logger.trace(f"API Request - {request.remote_addr} {request.method} {request.url}")
    logger.debug(get_log_prefix(query_args))

    if not config.FORCE and util.CURRENT_BACKEND_HEIGHT is None:
        return return_result(
            503,
            error="Backend still not ready. Please try again later.",
            start_time=start_time,
            query_args=query_args,
        )

    rule = str(request.url_rule.rule)

    with configure_sentry_scope() as scope:
        scope.set_transaction_name(get_transaction_name(rule))

    if not config.FORCE and not is_server_ready() and not return_result_if_not_ready(rule):
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
        result = execute_api_function(rule, route, function_args)
    except (
        exceptions.JSONRPCInvalidRequest,
        flask.wrappers.BadRequest,
        exceptions.TransactionError,
        exceptions.BalanceError,
        exceptions.UnknownPubKeyError,
        exceptions.AssetNameError,
        exceptions.BitcoindRPCError,
        exceptions.ComposeError,
        exceptions.UnpackError,
        CBitcoinAddressError,
        script.AddressError,
        exceptions.ElectrsError,
        OverflowError,
    ) as e:
        # import traceback
        # print(traceback.format_exc())
        return return_result(400, error=str(e), start_time=start_time, query_args=query_args)
    except Exception as e:
        capture_exception(e)
        logger.error("Error in API: %s", e)
        import traceback

        print(traceback.format_exc())
        return return_result(
            503, error="Unknown error", start_time=start_time, query_args=query_args
        )

    if isinstance(result, requests.Response):
        message = f"API Request - {request.remote_addr} {request.method} {request.url}"
        message += f" - Response {result.status_code}"
        message += f" - {int((time.time() - start_time) * 1000)}ms"
        logger.debug(message)
        headers = dict(result.headers)
        del headers["Connection"]  # remove "hop-by-hop" headers
        return result.content, result.status_code, headers

    # clean up and return the result
    if result is None:
        return return_result(404, error="Not found", start_time=start_time, query_args=query_args)

    next_cursor = None
    result_count = None
    table = None
    if isinstance(result, queries.QueryResult):
        next_cursor = result.next_cursor
        result_count = result.result_count
        table = result.table
        result = result.result

    result = clean_rowids_and_confirmed_fields(result)

    # inject details
    verbose = request.args.get("verbose", "False")
    if verbose.lower() in ["true", "1"]:
        with LedgerDBConnectionPool().connection() as ledger_db:
            with StateDBConnectionPool().connection() as state_db:
                result = inject_details(ledger_db, state_db, result, table)

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


def handle_options():
    response = flask.Response("", 204)
    set_cors_headers(response)
    return response


def init_flask_app():
    app = Flask(config.APP_NAME)
    with app.app_context():
        # Initialise the API access log
        init_api_access_log(app)
        # Get the last block index
        with LedgerDBConnectionPool().connection() as db:
            util.CURRENT_BLOCK_INDEX = ledger.last_db_index(db)
        methods = ["OPTIONS", "GET"]
        # Add routes
        app.add_url_rule(
            "/v2/",
            view_func=handle_route,
            methods=methods,
            strict_slashes=False,
            provide_automatic_options=False,
        )
        app.add_url_rule(
            "/v2/blueprint",
            view_func=handle_doc,
            methods=methods,
            strict_slashes=False,
            provide_automatic_options=False,
        )
        for path in ROUTES:
            methods = ["OPTIONS", "GET"]
            if path == "/v2/bitcoin/transactions":
                methods = ["OPTIONS", "POST"]
            if not path.startswith("/v2/"):
                methods = ["OPTIONS", "GET", "POST"]
            app.add_url_rule(
                path,
                view_func=handle_route,
                methods=methods,
                strict_slashes=False,
                provide_automatic_options=False,
            )

        app.register_error_handler(404, handle_not_found)

    return app


def check_database_version(state_db):
    try:
        check.database_version(state_db)
    except check.DatabaseVersionError as e:
        logger.info(str(e))
        # rollback or reparse the database
        if e.required_action in ["rollback", "reparse"]:
            dbbuilder.rollback_state_db(state_db, block_index=e.from_block_index)
        else:
            for version in config.STATE_DB_NEED_REFRESH_ON_VERSION_UPDATE:
                if config.VERSION_STRING.startswith(version):
                    dbbuilder.refresh_state_db(state_db)
                    break
        # update the database version
        database.update_version(state_db)


def run_api_server(args, server_ready_value, stop_event, parent_pid):
    logger.info("Starting API Server process...")

    def handle_interrupt_signal(signum, frame):
        logger.warning("Keyboard interrupt received. Shutting down...")
        raise KeyboardInterrupt

    wsgi_server = None
    parent_checker = None
    watcher = None

    try:
        # Set signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_interrupt_signal)
        signal.signal(signal.SIGTERM, handle_interrupt_signal)

        # Initialize Sentry, logging, config, etc.
        sentry.init()
        server.initialise_log_and_config(argparse.Namespace(**args), api=True)

        dbbuilder.apply_outstanding_migration()

        state_db = database.get_db_connection(
            config.STATE_DATABASE, read_only=False, check_wal=False
        )
        check_database_version(state_db)

        watcher = api_watcher.APIWatcher(state_db)
        watcher.start()

        app = init_flask_app()

        wsgi_server = wsgi.WSGIApplication(app, args=args)

        logger.info("Starting Parent Process Checker thread...")
        parent_checker = ParentProcessChecker(wsgi_server, stop_event, parent_pid)
        parent_checker.start()

        app.app_context().push()
        server_ready_value.value = 1

        wsgi_server.run()

    except KeyboardInterrupt as e:
        print("API Server KeyboardInterrupt", e)

    finally:
        logger.info("Stopping API Server...")

        if wsgi_server is not None:
            logger.trace("Stopping WSGI Server thread...")
            wsgi_server.stop()

        logger.trace("Closing Ledger DB and State DB Connection Pool...")
        LedgerDBConnectionPool().close()
        StateDBConnectionPool().close()

        if watcher is not None:
            watcher.stop()
            watcher.join()

        logger.info("API Server stopped.")


def is_process_alive(pid):
    """Check For the existence of a unix pid."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


# This thread is used for the following two reasons:
# 1. `docker-compose stop` does not send a SIGTERM to the child processes (in this case the API v2 process)
# 2. `process.terminate()` does not trigger a `KeyboardInterrupt` or execute the `finally` block.
class ParentProcessChecker(threading.Thread):
    def __init__(self, wsgi_server, stop_event, parent_pid):
        super().__init__(name="ParentProcessChecker")
        self.daemon = True
        self.wsgi_server = wsgi_server
        self.stop_event = stop_event
        self.parent_pid = parent_pid

    def run(self):
        try:
            while not self.stop_event.is_set() and is_process_alive(self.parent_pid):
                time.sleep(1)
            logger.debug("Parent process stopped. Exiting...")
            if self.wsgi_server is not None:
                self.wsgi_server.stop()
        except KeyboardInterrupt:
            pass


class APIServer(object):
    def __init__(self, stop_event):
        self.process = None
        self.server_ready_value = Value("I", 0)
        self.stop_event = stop_event

    def start(self, args):
        if self.process is not None:
            raise Exception("API Server is already running")
        self.process = Process(
            name="API",
            target=run_api_server,
            args=(vars(args), self.server_ready_value, self.stop_event, os.getpid()),
        )
        self.process.start()
        return self.process

    def is_ready(self):
        return self.server_ready_value.value == 1

    def stop(self):
        logger.info("Stopping API Server process...")
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)
            if self.process.is_alive():
                logger.error("API Server process did not stop in time. Terminating forcefully...")
                self.process.kill()
        logger.info("API Server process stopped.")

    def has_stopped(self):
        return self.stop_event.is_set()
