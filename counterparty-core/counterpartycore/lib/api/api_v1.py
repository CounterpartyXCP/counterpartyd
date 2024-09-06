#! /usr/bin/python3

"""
The database connections are read‐only, so SQL injection attacks can’t be a
problem.
"""

import binascii
import collections
import decimal
import json
import logging
import math
import re
import threading
import time

import counterpartycore.lib.sentry as sentry  # noqa: F401
import flask
import jsonrpc
from counterpartycore.lib import (
    backend,
    config,
    database,
    deserialize,
    exceptions,
    gettxinfo,
    ledger,
    message_type,
    script,
    transaction,
    util,
)
from counterpartycore.lib.api import util as api_util
from counterpartycore.lib.database import APIDBConnectionPool
from counterpartycore.lib.messages import (
    bet,  # noqa: F401
    broadcast,  # noqa: F401
    btcpay,  # noqa: F401
    burn,  # noqa: F401
    cancel,  # noqa: F401
    destroy,  # noqa: F401
    dispenser,  # noqa: F401
    dividend,  # noqa: F401
    issuance,  # noqa: F401
    order,  # noqa: F401
    rps,  # noqa: F401
    rpsresolve,  # noqa: F401
    send,
    sweep,  # noqa: F401
)
from counterpartycore.lib.messages.versions import enhanced_send  # noqa: E402
from counterpartycore.lib.telemetry.util import (  # noqa: E402
    get_addrindexrs_version,
    get_uptime,
    is_docker,
    is_force_enabled,
)
from flask import request
from flask_httpauth import HTTPBasicAuth
from jsonrpc import dispatcher
from jsonrpc.exceptions import JSONRPCDispatchException
from sentry_sdk import capture_exception
from sentry_sdk import configure_scope as configure_sentry_scope
from werkzeug.serving import make_server
from xmltodict import unparse as serialize_to_xml

D = decimal.Decimal

logger = logging.getLogger(config.LOGGER_NAME)


API_TABLES = [
    "assets",
    "balances",
    "credits",
    "debits",
    "bets",
    "bet_matches",
    "broadcasts",
    "btcpays",
    "burns",
    "cancels",
    "destructions",
    "dividends",
    "issuances",
    "orders",
    "order_matches",
    "sends",
    "bet_expirations",
    "order_expirations",
    "bet_match_expirations",
    "order_match_expirations",
    "bet_match_resolutions",
    "rps",
    "rpsresolves",
    "rps_matches",
    "rps_expirations",
    "rps_match_expirations",
    "mempool",
    "sweeps",
    "dispensers",
    "dispenses",
    "transactions",
]


JSON_RPC_ERROR_API_COMPOSE = -32001  # code to use for error composing transaction result

CURRENT_API_STATUS_CODE = None  # is updated by the APIStatusPoller
CURRENT_API_STATUS_RESPONSE_JSON = None  # is updated by the APIStatusPoller


class APIError(Exception):
    pass


class BackendError(Exception):
    pass


def check_backend_state():
    f"""Checks blocktime of last block to see if {config.BTC_NAME} Core is running behind."""  # noqa: B021
    block_count = backend.bitcoind.getblockcount()
    block_hash = backend.bitcoind.getblockhash(block_count)
    cblock = backend.bitcoind.getblock(block_hash, verbosity=1)
    time_behind = time.time() - cblock["time"]  # TODO: Block times are not very reliable.
    if time_behind > 60 * 60 * 2:  # Two hours.
        raise BackendError(f"Bitcoind is running about {round(time_behind / 3600)} hours behind.")

    # check backend index
    blocks_behind = backend.bitcoind.get_blocks_behind()
    if blocks_behind > 5:
        raise BackendError(f"Indexd is running {blocks_behind} blocks behind.")

    logger.debug("API Status Poller - Backend state check passed.")


class DatabaseError(Exception):
    pass


# TODO: ALL queries EVERYWHERE should be done with these methods
def db_query(db, statement, bindings=(), callback=None, **callback_args):
    """Allow direct access to the database in a parametrized manner."""
    cursor = db.cursor()

    # Sanitize.
    forbidden_words = ["pragma", "attach", "database", "begin", "transaction"]
    for word in forbidden_words:
        # This will find if the forbidden word is in the statement as a whole word. For example, "transactions" will be allowed because the "s" at the end
        if re.search(r"\b" + word + "\b", statement.lower()):
            raise APIError(f"Forbidden word in query: '{word}'.")

    if callable(callback):
        cursor.execute(statement, bindings)
        for row in cursor:
            callback(row, **callback_args)
        results = None
    else:
        results = list(cursor.execute(statement, bindings))
    cursor.close()
    return results


def get_rows(
    db,
    table,
    filters=None,
    filterop="AND",
    order_by=None,
    order_dir=None,
    start_block=None,
    end_block=None,
    status=None,
    limit=1000,
    offset=0,
    show_expired=True,
):
    """SELECT * FROM wrapper. Filters results based on a filter data structure (as used by the API)."""

    if filters == None:  # noqa: E711
        filters = []

    def value_to_marker(value):
        # if value is an array place holder is (?,?,?,..)
        if isinstance(value, list):
            return f"""({','.join(['?' for e in range(0, len(value))])})"""
        else:
            return """?"""

    # TODO: Document that op can be anything that SQLite3 accepts.
    if not table or table.lower() not in API_TABLES:
        raise APIError("Unknown table")
    if filterop and filterop.upper() not in ["OR", "AND"]:
        raise APIError("Invalid filter operator (OR, AND)")
    if order_dir and order_dir.upper() not in ["ASC", "DESC"]:
        raise APIError("Invalid order direction (ASC, DESC)")
    if not isinstance(limit, int):
        raise APIError("Invalid limit")
    elif config.API_LIMIT_ROWS != 0 and limit > config.API_LIMIT_ROWS:
        raise APIError(f"Limit should be lower or equal to {config.API_LIMIT_ROWS}")
    elif config.API_LIMIT_ROWS != 0 and limit == 0:
        raise APIError("Limit should be greater than 0")
    if not isinstance(offset, int):
        raise APIError("Invalid offset")
    # TODO: accept an object:  {'field1':'ASC', 'field2': 'DESC'}
    if order_by and not re.compile("^[a-z0-9_]+$").match(order_by):
        raise APIError("Invalid order_by, must be a field name")

    if isinstance(filters, dict):  # single filter entry, convert to a one entry list
        filters = [
            filters,
        ]
    elif not isinstance(filters, list):
        filters = []

    # TODO: Document this! (Each filter can be an ordered list.)
    new_filters = []
    for filter_ in filters:
        if type(filter_) in (list, tuple) and len(filter_) in [3, 4]:
            new_filter = {"field": filter_[0], "op": filter_[1], "value": filter_[2]}
            if len(filter_) == 4:
                new_filter["case_sensitive"] = filter_[3]
            new_filters.append(new_filter)
        elif type(filter_) == dict:  # noqa: E721
            new_filters.append(filter_)
        else:
            raise APIError("Unknown filter type")
    filters = new_filters

    # validate filter(s)
    for filter_ in filters:
        for field in ["field", "op", "value"]:  # should have all fields
            if field not in filter_:
                raise APIError(f"A specified filter is missing the '{field}' field")
        if not isinstance(filter_["value"], (str, int, float, list)):
            raise APIError(f"Invalid value for the field '{filter_['field']}'")
        if isinstance(filter_["value"], list) and filter_["op"].upper() not in [
            "IN",
            "NOT IN",
        ]:
            raise APIError(f"Invalid value for the field '{filter_['field']}'")
        if filter_["op"].upper() not in [
            "=",
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "IN",
            "LIKE",
            "NOT IN",
            "NOT LIKE",
        ]:
            raise APIError(f"Invalid operator for the field '{filter_['field']}'")
        if "case_sensitive" in filter_ and not isinstance(filter_["case_sensitive"], bool):
            raise APIError("case_sensitive must be a boolean")

    # special case for memo and memo_hex field searches
    if table == "sends":
        adjust_get_sends_memo_filters(filters)

    # SELECT
    # no sql injection here
    statement = f"""SELECT * FROM ({table})"""  # nosec B608  # noqa: S608
    # WHERE
    bindings = []
    conditions = []
    for filter_ in filters:
        case_sensitive = False if "case_sensitive" not in filter_ else filter_["case_sensitive"]
        if filter_["op"] == "LIKE" and case_sensitive == False:  # noqa: E712
            filter_["field"] = f"""UPPER({filter_['field']})"""
            filter_["value"] = filter_["value"].upper()
        marker = value_to_marker(filter_["value"])
        conditions.append(f"""{filter_['field']} {filter_['op']} {marker}""")
        if isinstance(filter_["value"], list):
            bindings += filter_["value"]
        else:
            bindings.append(filter_["value"])
    # AND filters
    more_conditions = []
    if table not in ["balances", "order_matches", "bet_matches"]:
        if start_block != None:  # noqa: E711
            more_conditions.append("""block_index >= ?""")
            bindings.append(start_block)
        if end_block != None:  # noqa: E711
            more_conditions.append("""block_index <= ?""")
            bindings.append(end_block)
    elif table in ["order_matches", "bet_matches"]:
        if start_block != None:  # noqa: E711
            more_conditions.append("""tx0_block_index >= ?""")
            bindings.append(start_block)
        if end_block != None:  # noqa: E711
            more_conditions.append("""tx1_block_index <= ?""")
            bindings.append(end_block)

    # status
    if isinstance(status, list) and len(status) > 0:
        more_conditions.append(f"""status IN {value_to_marker(status)}""")
        bindings += status
    elif isinstance(status, str) and status != "":
        more_conditions.append("""status == ?""")
        bindings.append(status)

    # legacy filters
    if not show_expired and table == "orders":
        # Ignore BTC orders one block early.
        expire_index = util.CURRENT_BLOCK_INDEX + 1
        more_conditions.append("""((give_asset == ? AND expire_index > ?) OR give_asset != ?)""")
        bindings += [config.BTC, expire_index, config.BTC]

    if (len(conditions) + len(more_conditions)) > 0:
        statement += """ WHERE"""
        all_conditions = []
        if len(conditions) > 0:
            all_conditions.append(f"""({f' {filterop.upper()} '.join(conditions)})""")
        if len(more_conditions) > 0:
            all_conditions.append(f"""({' AND '.join(more_conditions)})""")
        statement += f""" {' AND '.join(all_conditions)}"""

    # ORDER BY
    if order_by != None:  # noqa: E711
        statement += f""" ORDER BY {order_by}"""
        if order_dir != None:  # noqa: E711
            statement += f""" {order_dir.upper()}"""
    # LIMIT
    if limit and limit > 0:
        statement += f""" LIMIT {limit}"""
        if offset:
            statement += f""" OFFSET {offset}"""

    query_result = db_query(db, statement, tuple(bindings))

    if table == "balances":
        return adjust_get_balances_results(query_result, db)

    if table == "destructions":
        return adjust_get_destructions_results(query_result)

    if table == "sends":
        # for sends, handle the memo field properly
        return adjust_get_sends_results(query_result)

    if table == "transactions":
        # for transactions, handle the data field properly
        return adjust_get_transactions_results(query_result)

    return remove_rowids(query_result)


def remove_rowids(query_result):
    """Remove the rowid field from the query result."""
    filtered_results = []
    for row in list(query_result):
        if "rowid" in row:
            del row["rowid"]
        if "MAX(rowid)" in row:
            del row["MAX(rowid)"]
        filtered_results.append(row)

    return filtered_results


def adjust_get_balances_results(query_result, db):
    filtered_results = []
    assets = {}
    for balances_row in list(query_result):
        asset = balances_row["asset"]
        if asset not in assets:
            assets[asset] = ledger.is_divisible(db, asset)

        balances_row["divisible"] = assets[asset]
        filtered_results.append(balances_row)

    return filtered_results


def adjust_get_destructions_results(query_result):
    filtered_results = []
    for destruction_row in list(query_result):
        if type(destruction_row["tag"]) == bytes:  # noqa: E721
            destruction_row["tag"] = destruction_row["tag"].decode("utf-8", "ignore")

        filtered_results.append(destruction_row)

    return filtered_results


def adjust_get_sends_memo_filters(filters):
    """Convert memo to a byte string.  If memo_hex is supplied, attempt to decode it and use that instead."""
    for filter_ in filters:
        if filter_["field"] == "memo":
            filter_["value"] = bytes(filter_["value"], "utf-8")
        if filter_["field"] == "memo_hex":
            # search the indexed memo field with a byte string
            filter_["field"] = "memo"
            try:
                filter_["value"] = bytes.fromhex(filter_["value"])
            except ValueError as e:  # noqa: F841
                raise APIError("Invalid memo_hex value")  # noqa: B904


def adjust_get_sends_results(query_result):
    """Format the memo_hex field.  Try and decode the memo from a utf-8 uncoded string. Invalid utf-8 strings return an empty memo."""
    filtered_results = []
    for send_row in list(query_result):
        try:
            if send_row["memo"] is None:
                send_row["memo_hex"] = None
                send_row["memo"] = None
            else:
                if type(send_row["memo"]) == str:  # noqa: E721
                    send_row["memo"] = bytes(send_row["memo"], "utf-8")

                send_row["memo_hex"] = binascii.hexlify(send_row["memo"]).decode("utf8")
                send_row["memo"] = send_row["memo"].decode("utf-8")
        except UnicodeDecodeError:
            send_row["memo"] = ""
        filtered_results.append(send_row)
    return filtered_results


def adjust_get_transactions_results(query_result):
    """Format the data field.  Try and decode the data from a utf-8 uncoded string. Invalid utf-8 strings return an empty data."""
    filtered_results = []
    for transaction_row in list(query_result):
        transaction_row["data"] = transaction_row["data"].hex()
        filtered_results.append(transaction_row)
    return filtered_results


def conditional_decorator(decorator, condition):
    """Checks the condition and if True applies specified decorator."""

    def gen_decorator(f):
        if not condition:
            return f
        return decorator(f)

    return gen_decorator


class APIStatusPoller(threading.Thread):
    """Perform regular checks on the state of the backend and the database."""

    def __init__(self):
        self.last_database_check = 0
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.stopping = False
        self.stopped = False
        self.db = None

    def stop(self):
        logger.info("Stopping API Status Poller...")
        self.stopping = True
        if self.db is not None:
            self.db.close()
            self.db = None
        self.join()

    def run(self):
        logger.debug("Starting API Status Poller...")
        global CURRENT_API_STATUS_CODE, CURRENT_API_STATUS_RESPONSE_JSON  # noqa: PLW0603
        self.db = database.get_db_connection(config.API_DATABASE, read_only=True, check_wal=False)

        interval_if_ready = 5 * 60  # 5 minutes
        interval_if_not_ready = 60  # 1 minutes
        interval = interval_if_not_ready

        while not self.stopping:  # noqa: E712
            try:
                # Check that backend is running, communicable, and caught up with the blockchain.
                # Check that the database has caught up with bitcoind.
                if (
                    time.time() - self.last_database_check > interval
                ):  # Ten minutes since last check.
                    self.last_database_check = time.time()
                    if not config.FORCE and self.db is not None:
                        code = 11
                        check_backend_state()
                        code = 12
                        api_util.check_last_parsed_block(self.db, backend.bitcoind.getblockcount())
                        interval = interval_if_ready
            except (BackendError, exceptions.DatabaseError) as e:
                interval = interval_if_not_ready
                exception_name = e.__class__.__name__
                exception_text = str(e)
                logger.debug("API Status Poller: %s", exception_text)
                jsonrpc_response = jsonrpc.exceptions.JSONRPCServerError(
                    message=exception_name, data=exception_text
                )
                CURRENT_API_STATUS_CODE = code
                CURRENT_API_STATUS_RESPONSE_JSON = jsonrpc_response.json.encode()
            else:
                CURRENT_API_STATUS_CODE = None
                CURRENT_API_STATUS_RESPONSE_JSON = None
            if not self.stopping:
                time.sleep(0.5)  # sleep for 0.5 seconds


class APIServer(threading.Thread):
    """Handle JSON-RPC API calls."""

    def __init__(self, db=None):
        self.is_ready = False
        self.server = None
        self.ctx = None
        self.connection_pool = APIDBConnectionPool()
        threading.Thread.__init__(self)
        sentry.init()

    def stop(self):
        logger.info("Stopping API Server v1...")
        self.connection_pool.close()
        self.server.shutdown()
        self.join()

    def run(self):
        logger.info("Starting API Server v1...")
        app = flask.Flask(__name__)
        auth = HTTPBasicAuth()

        @auth.get_password
        def get_pw(username):
            if username == config.RPC_USER:
                return config.RPC_PASSWORD
            return None

        ######################
        # READ API

        # Generate dynamically get_{table} methods
        def generate_get_method(table):
            def get_method(**kwargs):
                try:
                    with self.connection_pool.connection() as db:
                        return get_rows(db, table=table, **kwargs)
                except TypeError as e:  # TODO: generalise for all API methods
                    raise APIError(str(e))  # noqa: B904

            return get_method

        for table in API_TABLES:
            new_method = generate_get_method(table)
            new_method.__name__ = f"get_{table}"
            dispatcher.add_method(new_method)

        @dispatcher.add_method
        def sql(query, bindings=None):
            if bindings == None:  # noqa: E711
                bindings = []
            with self.connection_pool.connection() as db:
                return db_query(db, query, tuple(bindings))

        ######################
        # WRITE/ACTION API

        # Generate dynamically create_{transaction} methods
        def generate_create_method(tx):
            def create_method(**kwargs):
                try:
                    transaction_args, common_args, private_key_wif = (
                        transaction.split_compose_params(**kwargs)
                    )
                    with self.connection_pool.connection() as db:
                        return transaction.compose_transaction(
                            db, name=tx, params=transaction_args, api_v1=True, **common_args
                        )
                except (
                    TypeError,
                    script.AddressError,
                    exceptions.ComposeError,
                    exceptions.TransactionError,
                    exceptions.BalanceError,
                ) as error:
                    # TypeError happens when unexpected keyword arguments are passed in
                    error_msg = f"Error composing {tx} transaction via API: {str(error)}"
                    logging.warning(error_msg)
                    raise JSONRPCDispatchException(  # noqa: B904
                        code=JSON_RPC_ERROR_API_COMPOSE, message=error_msg
                    )

            return create_method

        for tx in transaction.COMPOSABLE_TRANSACTIONS:
            create_method = generate_create_method(tx)
            create_method.__name__ = f"create_{tx}"
            dispatcher.add_method(create_method)

        @dispatcher.add_method
        def get_messages(block_index):
            if not isinstance(block_index, int):
                raise APIError("block_index must be an integer.")
            with self.connection_pool.connection() as db:
                messages = ledger.get_messages(db, block_index=block_index)
            return messages

        @dispatcher.add_method
        def get_messages_by_index(message_indexes):
            """Get specific messages from the feed, based on the message_index.

            @param message_index: A single index, or a list of one or more message indexes to retrieve.
            """
            if not isinstance(message_indexes, list):
                message_indexes = [
                    message_indexes,
                ]
            for idx in message_indexes:  # make sure the data is clean
                if not isinstance(idx, int):
                    raise APIError("All items in message_indexes are not integers")
            with self.connection_pool.connection() as db:
                messages = ledger.get_messages(db, message_index_in=message_indexes)
            return messages

        @dispatcher.add_method
        def get_supply(asset):
            with self.connection_pool.connection() as db:
                if asset == "BTC":
                    return backend.bitcoind.get_btc_supply(normalize=False)
                elif asset == "XCP":
                    return ledger.xcp_supply(db)
                else:
                    asset = ledger.resolve_subasset_longname(db, asset)
                    return ledger.asset_supply(db, asset)

        @dispatcher.add_method
        def get_xcp_supply():
            logger.warning("Deprecated method: `get_xcp_supply`")
            with self.connection_pool.connection() as db:
                return ledger.xcp_supply(db)

        @dispatcher.add_method
        def get_asset_info(assets=None, asset=None):
            if asset is not None:
                assets = [asset]

            if not isinstance(assets, list):
                raise APIError(
                    "assets must be a list of asset names, even if it just contains one entry"
                )
            assets_info = []
            with self.connection_pool.connection() as db:
                for asset in assets:
                    asset = ledger.resolve_subasset_longname(db, asset)  # noqa: PLW2901

                    # BTC and XCP.
                    if asset in [config.BTC, config.XCP]:
                        if asset == config.BTC:
                            supply = backend.bitcoind.get_btc_supply(normalize=False)
                        else:
                            supply = ledger.xcp_supply(db)

                        assets_info.append(
                            {
                                "asset": asset,
                                "asset_longname": None,
                                "owner": None,
                                "divisible": True,
                                "locked": False,
                                "supply": supply,
                                "description": "",
                                "issuer": None,
                            }
                        )
                        continue

                    # User‐created asset.
                    cursor = db.cursor()
                    issuances = ledger.get_issuances(db, asset=asset, status="valid", first=True)
                    cursor.close()
                    if not issuances:
                        continue  # asset not found, most likely
                    else:
                        last_issuance = issuances[-1]
                    locked = False
                    for e in issuances:
                        if e["locked"]:
                            locked = True
                    assets_info.append(
                        {
                            "asset": asset,
                            "asset_longname": last_issuance["asset_longname"],
                            "owner": last_issuance["issuer"],
                            "divisible": bool(last_issuance["divisible"]),
                            "locked": locked,
                            "supply": ledger.asset_supply(db, asset),
                            "description": last_issuance["description"],
                            "issuer": last_issuance["issuer"],
                        }
                    )
            return assets_info

        @dispatcher.add_method
        def get_block_info(block_index):
            assert isinstance(block_index, int)
            with self.connection_pool.connection() as db:
                cursor = db.cursor()
                cursor.execute("""SELECT * FROM blocks WHERE block_index = ?""", (block_index,))
                blocks = list(cursor)  # noqa: F811
                if len(blocks) == 1:
                    block = blocks[0]
                elif len(blocks) == 0:
                    raise exceptions.DatabaseError("No blocks found.")
                else:
                    assert False  # noqa: B011
                cursor.close()
                return block

        @dispatcher.add_method
        def fee_per_kb(conf_target=config.ESTIMATE_FEE_CONF_TARGET, mode=config.ESTIMATE_FEE_MODE):
            return backend.bitcoind.fee_per_kb(conf_target, mode)

        @dispatcher.add_method
        def get_blocks(block_indexes, min_message_index=None):
            """fetches block info and messages for the specified block indexes
            @param min_message_index: Retrieve blocks from the message feed on or after this specific message index
              (useful since blocks may appear in the message feed more than once, if a reorg occurred). Note that
              if this parameter is not specified, the messages for the first block will be returned.
            """

            must_be_non_empty_list_int = "block_indexes must be a non-empty list of integers"

            if not isinstance(block_indexes, (list, tuple)):
                raise APIError(must_be_non_empty_list_int)

            if len(block_indexes) == 0:
                raise APIError(must_be_non_empty_list_int)

            if len(block_indexes) >= 250:
                raise APIError("can only specify up to 250 indexes at a time.")
            for block_index in block_indexes:
                if not isinstance(block_index, int):
                    raise APIError(must_be_non_empty_list_int)

            with self.connection_pool.connection() as db:
                cursor = db.cursor()

                block_indexes_placeholder = f"{','.join(['?'] * len(block_indexes))}"
                # no sql injection here
                cursor.execute(
                    f"SELECT * FROM blocks WHERE block_index IN ({block_indexes_placeholder}) ORDER BY block_index ASC",  # nosec B608  # noqa: S608
                    block_indexes,
                )
                blocks = cursor.fetchall()  # noqa: F811

                messages = collections.deque(ledger.get_messages(db, block_index_in=block_indexes))

                # Discard any messages less than min_message_index
                if min_message_index:
                    while len(messages) and messages[0]["message_index"] < min_message_index:
                        messages.popleft()

                # Packages messages into their appropriate block in the data structure to be returned
                for block in blocks:
                    block["_messages"] = []
                    while len(messages) and messages[0]["block_index"] == block["block_index"]:
                        block["_messages"].append(messages.popleft())
                # NOTE: if len(messages), then we're only returning the messages for the first set of blocks before the reorg

                cursor.close()
            return blocks

        @dispatcher.add_method
        def get_running_info():
            latest_block_index = backend.bitcoind.getblockcount()
            with self.connection_pool.connection() as db:
                try:
                    api_util.check_last_parsed_block(db, latest_block_index)
                except exceptions.DatabaseError:
                    caught_up = False
                else:
                    caught_up = True

                try:
                    cursor = db.cursor()
                    blocks = list(
                        cursor.execute(
                            """SELECT * FROM blocks WHERE block_index = ?""",
                            (util.CURRENT_BLOCK_INDEX,),
                        )
                    )
                    assert len(blocks) == 1
                    last_block = blocks[0]
                    cursor.close()
                except:  # noqa: E722
                    last_block = None

                try:
                    last_message = ledger.last_message(db)
                except:  # noqa: E722
                    last_message = None

            try:
                indexd_blocks_behind = backend.bitcoind.get_blocks_behind()
            except:  # noqa: E722
                indexd_blocks_behind = latest_block_index if latest_block_index > 0 else 999999
            indexd_caught_up = indexd_blocks_behind <= 1

            server_ready = caught_up and indexd_caught_up

            addrindexrs_version = get_addrindexrs_version().split(".")

            return {
                "server_ready": server_ready,
                "db_caught_up": caught_up,
                "bitcoin_block_count": latest_block_index,
                "last_block": last_block,
                "indexd_caught_up": indexd_caught_up,
                "indexd_blocks_behind": indexd_blocks_behind,
                "last_message_index": (last_message["message_index"] if last_message else -1),
                "api_limit_rows": config.API_LIMIT_ROWS,
                "running_testnet": config.TESTNET,
                "running_regtest": config.REGTEST,
                "running_testcoin": config.TESTCOIN,
                "version_major": config.VERSION_MAJOR,
                "version_minor": config.VERSION_MINOR,
                "version_revision": config.VERSION_REVISION,
                "addrindexrs_version_major": int(addrindexrs_version[0]),
                "addrindexrs_version_minor": int(addrindexrs_version[1]),
                "addrindexrs_version_revision": int(addrindexrs_version[2]),
                "uptime": int(get_uptime()),
                "dockerized": is_docker(),
                "force_enabled": is_force_enabled(),
            }

        @dispatcher.add_method
        def get_element_counts():
            with self.connection_pool.connection() as db:
                counts = {}
                cursor = db.cursor()
                for element in [
                    "transactions",
                    "blocks",
                    "debits",
                    "credits",
                    "balances",
                    "sends",
                    "orders",
                    "order_matches",
                    "btcpays",
                    "issuances",
                    "broadcasts",
                    "bets",
                    "bet_matches",
                    "dividends",
                    "burns",
                    "cancels",
                    "order_expirations",
                    "bet_expirations",
                    "order_match_expirations",
                    "bet_match_expirations",
                    "messages",
                    "destructions",
                ]:
                    # no sql injection here, element is hardcoded
                    cursor.execute(f"SELECT COUNT(*) AS count FROM {element}")  # nosec B608  # noqa: S608
                    count_list = cursor.fetchall()
                    assert len(count_list) == 1
                    counts[element] = count_list[0]["count"]
                cursor.close()
                return counts

        @dispatcher.add_method
        def get_asset_names(longnames=False):
            with self.connection_pool.connection() as db:
                all_assets = ledger.get_valid_assets(db)
            if longnames:
                names = [
                    {"asset": row["asset"], "asset_longname": row["asset_longname"]}
                    for row in all_assets
                ]
            else:
                names = [row["asset"] for row in all_assets]
            return names

        @dispatcher.add_method
        def get_asset_longnames():
            return get_asset_names(longnames=True)

        @dispatcher.add_method
        def get_holder_count(asset):
            with self.connection_pool.connection() as db:
                asset = ledger.resolve_subasset_longname(db, asset)
                holders = ledger.holders(db, asset, True)
            addresses = []
            for holder in holders:
                addresses.append(holder["address"])
            return {asset: len(set(addresses))}

        @dispatcher.add_method
        def get_holders(asset):
            with self.connection_pool.connection() as db:
                asset = ledger.resolve_subasset_longname(db, asset)
                holders = ledger.holders(db, asset, True)
            return holders

        @dispatcher.add_method
        def search_raw_transactions(address, unconfirmed=True, only_tx_hashes=False):
            return backend.addrindexrs.search_raw_transactions(
                address, unconfirmed=unconfirmed, only_tx_hashes=only_tx_hashes
            )

        @dispatcher.add_method
        def get_oldest_tx(address):
            return backend.addrindexrs.get_oldest_tx(address, block_index=util.CURRENT_BLOCK_INDEX)

        @dispatcher.add_method
        def get_unspent_txouts(address, unconfirmed=False, unspent_tx_hash=None, order_by=None):
            results = backend.addrindexrs.get_unspent_txouts(
                address, unconfirmed=unconfirmed, unspent_tx_hash=unspent_tx_hash
            )
            if order_by is None:
                return results
            else:
                order_key = order_by
                reverse = False
                if order_key.startswith("-"):
                    order_key = order_key[1:]
                    reverse = True
                return sorted(results, key=lambda x: x[order_key], reverse=reverse)

        @dispatcher.add_method
        def getrawtransaction(tx_hash, verbose=False):
            return backend.bitcoind.getrawtransaction(tx_hash, verbose=verbose)

        @dispatcher.add_method
        def getrawtransaction_batch(txhash_list, verbose=False, skip_missing=False):
            return backend.addrindexrs.getrawtransaction_batch(
                txhash_list, verbose=verbose, skip_missing=skip_missing
            )

        @dispatcher.add_method
        def get_tx_info(tx_hex, block_index=None):
            # block_index mandatory for transactions before block 335000
            use_txid = util.enabled("correct_segwit_txids", block_index=block_index)
            with self.connection_pool.connection() as db:
                source, destination, btc_amount, fee, data, _dispensers_outs, _utxos_info = (
                    gettxinfo.get_tx_info(
                        db,
                        deserialize.deserialize_tx(tx_hex, use_txid=use_txid),
                        block_index=block_index,
                    )
                )
            return (
                source,
                destination,
                btc_amount,
                fee,
                util.hexlify(data) if data else "",
            )

        @dispatcher.add_method
        def unpack(data_hex):
            data = binascii.unhexlify(data_hex)
            message_type_id, message = message_type.unpack(data)[0]

            # TODO: Enabled only for `send`.
            if message_type_id == send.ID:
                with self.connection_pool.connection() as db:
                    unpacked = send.unpack(db, message, util.CURRENT_BLOCK_INDEX)
            elif message_type_id == enhanced_send.ID:
                unpacked = enhanced_send.unpack(message, util.CURRENT_BLOCK_INDEX)
            else:
                raise APIError("unsupported message type")
            return message_type_id, unpacked

        @dispatcher.add_method
        # TODO: Rename this method.
        def search_pubkey(pubkeyhash, provided_pubkeys=None):
            return transaction.pubkeyhash_to_pubkey(pubkeyhash, provided_pubkeys=provided_pubkeys)

        @dispatcher.add_method
        def get_dispenser_info(tx_hash=None, tx_index=None):
            if tx_hash is None and tx_index is None:
                raise APIError("You must provided a tx hash or a tx index")

            dispensers = []
            with self.connection_pool.connection() as db:
                if tx_hash is not None:
                    dispensers = ledger.get_dispenser_info(db, tx_hash=tx_hash)
                else:
                    dispensers = ledger.get_dispenser_info(db, tx_index=tx_index)

                if len(dispensers) == 1:
                    dispenser = dispensers[0]
                    oracle_price = ""
                    satoshi_price = ""
                    fiat_price = ""
                    oracle_price_last_updated = ""
                    oracle_fiat_label = ""

                    if dispenser["oracle_address"] != None:  # noqa: E711
                        fiat_price = util.satoshirate_to_fiat(dispenser["satoshirate"])
                        (
                            oracle_price,
                            oracle_fee,
                            oracle_fiat_label,
                            oracle_price_last_updated,
                        ) = ledger.get_oracle_last_price(
                            db, dispenser["oracle_address"], util.CURRENT_BLOCK_INDEX
                        )

                        if oracle_price > 0:
                            satoshi_price = math.ceil((fiat_price / oracle_price) * config.UNIT)
                        else:
                            raise APIError("Last oracle price is zero")

                    return {
                        "tx_index": dispenser["tx_index"],
                        "tx_hash": dispenser["tx_hash"],
                        "block_index": dispenser["block_index"],
                        "source": dispenser["source"],
                        "asset": dispenser["asset"],
                        "give_quantity": dispenser["give_quantity"],
                        "escrow_quantity": dispenser["escrow_quantity"],
                        "mainchainrate": dispenser["satoshirate"],
                        "fiat_price": fiat_price,
                        "fiat_unit": oracle_fiat_label,
                        "oracle_price": oracle_price,
                        "satoshi_price": satoshi_price,
                        "status": dispenser["status"],
                        "give_remaining": dispenser["give_remaining"],
                        "oracle_address": dispenser["oracle_address"],
                        "oracle_price_last_updated": oracle_price_last_updated,
                        "asset_longname": dispenser["asset_longname"],
                    }

            return {}

        def _set_cors_headers(response):
            if not config.RPC_NO_ALLOW_CORS:
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = (
                    "DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization"
                )

        ##### REST ROUTES #####

        @app.route("/healthz", methods=["GET"])
        def handle_healthz():
            with configure_sentry_scope() as scope:
                scope.set_transaction_name("healthcheck")
            check_type = request.args.get("type", "light")
            with self.connection_pool.connection() as db:
                return api_util.handle_healthz_route(db, check_type)

        @app.route("/", defaults={"args_path": ""}, methods=["GET", "POST", "OPTIONS"])
        @app.route("/<path:args_path>", methods=["GET", "POST", "OPTIONS"])
        # Only require authentication if RPC_PASSWORD is set.
        @conditional_decorator(auth.login_required, hasattr(config, "RPC_PASSWORD"))
        def handle_root(args_path):
            """Handle all paths, decide where to forward the query."""
            request_path = args_path.lower()
            if (
                request_path == ""
                or request_path.startswith("api/")
                or request_path.startswith("rpc/")
                or request_path.startswith("v1/")
            ):
                if flask.request.method == "POST":
                    # Need to get those here because it might not be available in this aux function.
                    request_json = flask.request.get_data().decode("utf-8")
                    response = handle_rpc_post(request_json)
                    return response
                elif flask.request.method == "OPTIONS":
                    response = handle_rpc_options()
                    return response
                else:
                    error = "Invalid method."
                    return flask.Response(error, 405, mimetype="application/json")
            elif request_path.startswith("v1/rest/"):
                if flask.request.method == "GET" or flask.request.method == "POST":
                    # Pass the URL path without /REST/ part and Flask request object.
                    rest_path = args_path.split("/", 1)[1]
                    response = handle_rest(rest_path, flask.request)
                    return response
                else:
                    error = "Invalid method."
                    return flask.Response(error, 405, mimetype="application/json")
            else:
                # Not found
                return flask.Response(None, 404, mimetype="application/json")

        ######################
        # JSON-RPC API
        ######################
        def handle_rpc_options():
            response = flask.Response("", 204)
            _set_cors_headers(response)
            # response.headers["X-API-WARN"] = "Deprecated API"
            return response

        def handle_rpc_post(request_json):
            """Handle /API/ POST route. Call relevant get_rows/create_transaction wrapper."""
            # Check for valid request format.
            try:
                request_data = json.loads(request_json)
                assert (
                    "id" in request_data
                    and request_data["jsonrpc"] == "2.0"
                    and request_data["method"]
                )
                # params may be omitted
            except Exception as error:  # noqa: E722
                capture_exception(error)
                obj_error = jsonrpc.exceptions.JSONRPCInvalidRequest(
                    data="Invalid JSON-RPC 2.0 request format"
                )
                return flask.Response(obj_error.json.encode(), 400, mimetype="application/json")

            with configure_sentry_scope() as scope:
                scope.set_transaction_name(request_data["method"])

            # Only arguments passed as a `dict` are supported.
            if request_data.get("params", None) and not isinstance(request_data["params"], dict):
                error_message = "Arguments must be passed as a JSON object (list of unnamed arguments not supported)"
                obj_error = jsonrpc.exceptions.JSONRPCInvalidRequest(data=error_message)
                return flask.Response(obj_error.json.encode(), 400, mimetype="application/json")

            # Return an error if the API Status Poller checks fail.
            if not config.FORCE and CURRENT_API_STATUS_CODE:
                return flask.Response(
                    CURRENT_API_STATUS_RESPONSE_JSON, 503, mimetype="application/json"
                )

            # Answer request normally.
            # NOTE: `UnboundLocalError: local variable 'output' referenced before assignment` means the method doesn’t return anything.
            jsonrpc_response = jsonrpc.JSONRPCResponseManager.handle(request_json, dispatcher)

            response = flask.Response(
                jsonrpc_response.json.encode(), 200, mimetype="application/json"
            )
            _set_cors_headers(response)
            # response.headers["X-API-WARN"] = "Deprecated API"
            # logger.warning(
            #    "API v1 is deprecated and should be removed soon. Please migrate to REST API."
            # )
            return response

        ######################
        # HTTP REST API
        ######################
        def handle_rest(path_args, flask_request):
            """Handle /REST/ route. Query the database using get_rows or create transaction using compose_transaction."""
            url_action = flask_request.path.split("/")[-1]
            if url_action == "compose":
                compose = True
            elif url_action == "get":
                compose = False
            else:
                error = f'Invalid action "{url_action}".'
                return flask.Response(error, 400, mimetype="application/json")

            # Get all arguments passed via URL.
            url_args = path_args.split("/")
            try:
                query_type = url_args.pop(0).lower()
            except IndexError:
                error = "No query_type provided."
                return flask.Response(error, 400, mimetype="application/json")
            # Check if message type or table name are valid.
            if (compose and query_type not in transaction.COMPOSABLE_TRANSACTIONS) or (
                not compose and query_type not in API_TABLES
            ):
                error = f'No such query type in supported queries: "{query_type}".'
                return flask.Response(error, 400, mimetype="application/json")

            # Parse the additional arguments.
            extra_args = flask_request.args.items()
            query_data = {}

            if compose:
                transaction_args, common_args, private_key_wif = transaction.split_compose_params(
                    **extra_args
                )

                # Must have some additional transaction arguments.
                if not len(transaction_args):
                    error = "No transaction arguments provided."
                    return flask.Response(error, 400, mimetype="application/json")

                # Compose the transaction.
                try:
                    with self.connection_pool.connection() as db:
                        query_data = transaction.compose_transaction(
                            db, name=query_type, params=transaction_args, **common_args
                        )
                except (
                    script.AddressError,
                    exceptions.ComposeError,
                    exceptions.TransactionError,
                    exceptions.BalanceError,
                ) as error:
                    error_msg = logging.warning(
                        f"{error.__class__.__name__} -- error composing {query_type} transaction via API: {error}"
                    )
                    return flask.Response(error_msg, 400, mimetype="application/json")
            else:
                # Need to de-generate extra_args to pass it through.
                query_args = dict([item for item in extra_args])
                operator = query_args.pop("op", "AND")
                # Put the data into specific dictionary format.
                data_filter = [
                    {"field": key, "op": "==", "value": value}
                    for (key, value) in query_args.items()
                ]

                # Run the query.
                try:
                    with self.connection_pool.connection() as db:
                        query_data = get_rows(
                            db,
                            table=query_type,
                            filters=data_filter,
                            filterop=operator,
                        )
                except APIError as error:  # noqa: F841
                    return flask.Response("API Error", 400, mimetype="application/json")

            # See which encoding to choose from.
            file_format = flask_request.headers["Accept"]
            # JSON as default.
            if file_format == "application/json" or file_format == "*/*":
                response_data = json.dumps(query_data)
            elif file_format == "application/xml":
                # Add document root for XML. Note when xmltodict encounters a list, it produces separate tags for every item.
                # Hence we end up with multiple query_type roots. To combat this we put it in a separate item dict.
                response_data = serialize_to_xml({query_type: {"item": query_data}})
            else:
                error = f'Invalid file format: "{file_format}".'
                return flask.Response(error, 400, mimetype="application/json")

            response = flask.Response(response_data, 200, mimetype=file_format)
            return response

        # Init the HTTP Server.
        self.is_ready = True
        self.server = make_server(config.RPC_HOST, config.RPC_PORT, app, threaded=True)
        api_util.init_api_access_log(app)
        self.ctx = app.app_context()
        self.ctx.push()
        # Run app server (blocking)
        self.server.serve_forever()
