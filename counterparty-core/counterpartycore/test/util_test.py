"""
This module contains a variety of utility functions used in the test suite.
"""

import binascii
import decimal
import difflib
import hashlib
import io
import json
import locale
import logging
import os
import pprint
import re
import sys
import tempfile  # noqa: F401
import time

import appdirs
import apsw
import bitcoin as bitcoinlib
import pycoin
import pytest
from pycoin.coins.bitcoin import Tx  # noqa: F401

CURR_DIR = os.path.dirname(
    os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__)))
)
sys.path.append(os.path.normpath(os.path.join(CURR_DIR, "..")))

from counterpartycore import server  # noqa: E402
from counterpartycore.lib import (  # noqa: E402
    backend,
    blocks,
    check,
    config,
    database,
    deserialize,
    exceptions,
    gettxinfo,
    ledger,
    transaction,
    util,
)
from counterpartycore.lib.messages import fairminter, utxo  # noqa
from counterpartycore.test.fixtures.params import DEFAULT_PARAMS as DP  # noqa: E402
from counterpartycore.test.fixtures.scenarios import (  # noqa: E402
    INTEGRATION_SCENARIOS,
    standard_scenarios_params,
)

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

# Set test environment
os.environ["TZ"] = "EST"
time.tzset()
locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

# TODO: This should grab the correct backend port and password, when used for, e.g., saverawtransactions.
COUNTERPARTYD_OPTIONS = {
    "testcoin": False,
    "rpc_port": 9999,
    "rpc_password": "pass",
    "api_password": None,
    "backend_port": 18332,
    "backend_password": "pass",
    "backend_ssl_no_verify": True,
    "p2sh_dust_return_pubkey": "11" * 33,
    "utxo_locks_max_addresses": 0,  # Disable UTXO locking for base test suite runs
    "estimate_fee_per_kb": False,
}

# used for mocking the UTXO in various places, is automatically reset every test case
MOCK_UTXO_SET = None


def init_database(sqlfile, dbfile, options=None):
    kwargs = COUNTERPARTYD_OPTIONS.copy()
    kwargs.update(options or {})

    server.initialise(database_file=dbfile, testnet=True, verbose=True, **kwargs)

    restore_database(config.DATABASE, sqlfile)
    db = database.get_connection(read_only=False)  # reinit the DB to deal with the restoring
    blocks.create_views(db)
    database.update_version(db)
    util.FIRST_MULTISIG_BLOCK_TESTNET = 1

    return db


def reset_current_block_index(db):
    cursor = db.cursor()
    latest_block = list(
        cursor.execute("""SELECT * FROM blocks ORDER BY block_index DESC LIMIT 1""")
    )[0]
    util.CURRENT_BLOCK_INDEX = latest_block["block_index"]
    cursor.close()

    return util.CURRENT_BLOCK_INDEX


def dump_database(db):
    """Create a new database dump from db object as input."""
    memory_db = apsw.Connection(":memory:")
    with memory_db.backup("main", db, "main") as backup:
        backup.step()

    dump = ""
    base_tables = [
        "blocks",
        "transactions",
        "transaction_outputs",
        "balances",
        "undolog",
        "undolog_block",
    ]
    for table in base_tables + blocks.TABLES:
        output = io.StringIO()
        shell = apsw.Shell(stdout=output, db=memory_db)
        shell.process_command(f".dump {table}")
        lines = output.getvalue().split("\n")[8:]
        new_data = "\n".join(lines)
        dump += new_data

    return dump


def restore_database(database_filename, dump_filename):
    """Delete database dump, then opens another and loads it in-place."""
    remove_database_files(database_filename)
    db = apsw.Connection(database_filename)
    cursor = db.cursor()
    with open(dump_filename, "r") as sql_dump:
        cursor.execute(sql_dump.read())
    cursor.close()


def remove_database_files(database_filename):
    """Delete temporary db dumps."""
    for path in [database_filename, f"{database_filename}-shm", f"{database_filename}-wal"]:
        if os.path.isfile(path):
            os.remove(path)


def insert_block(db, block_index, parse_block=True):
    """Add blocks to the blockchain."""
    block_hash = util.dhash_string(chr(block_index))
    block_time = block_index * 1000
    bindings = {
        "block_index": block_index,
        "block_hash": block_hash,
        "block_time": block_time,
        "ledger_hash": None,
        "txlist_hash": None,
        "previous_block_hash": None,
        "difficulty": None,
    }
    util.CURRENT_BLOCK_INDEX = block_index  # TODO: Correct?!
    ledger.insert_record(db, "blocks", bindings, "NEW_BLOCK")

    if parse_block:
        blocks.parse_block(db, block_index, block_time)

    MOCK_UTXO_SET.increment_confirmations()

    return block_index, block_hash, block_time


def create_next_block(db, block_index=None, parse_block=True):
    """Create faux data for the next block."""

    cursor = db.cursor()
    last_block_index = list(
        cursor.execute("SELECT block_index FROM blocks ORDER BY block_index DESC LIMIT 1")
    )[0]["block_index"]
    if not block_index:
        block_index = last_block_index + 1

    if last_block_index >= block_index:
        raise Exception("create_next_block called with height lower than current height")

    for index in range(last_block_index + 1, block_index + 1):
        inserted_block_index, block_hash, block_time = insert_block(
            db, index, parse_block=parse_block
        )

    cursor.close()
    return inserted_block_index, block_hash, block_time


def insert_raw_transaction(raw_transaction, db):
    """Add a raw transaction to the database."""
    cursor = db.cursor()

    # one transaction per block
    block_index, block_hash, block_time = create_next_block(db, parse_block=False)

    tx_hash = dummy_tx_hash(raw_transaction)
    tx = None
    tx_index = block_index - config.BURN_START + 1
    try:
        deserialized_tx = deserialize.deserialize_tx(raw_transaction, True)
        source, destination, btc_amount, fee, data, extra = gettxinfo._get_tx_info(
            db, deserialized_tx, block_index
        )
        utxos_info = gettxinfo.get_utxos_info(db, deserialized_tx)
        bindings = {
            "tx_index": tx_index,
            "tx_hash": tx_hash,
            "block_index": block_index,
            "block_hash": block_hash,
            "block_time": block_time,
            "source": source,
            "destination": destination,
            "btc_amount": btc_amount,
            "fee": fee,
            "data": data,
            "supported": True,
            "utxos_info": " ".join(utxos_info),
        }
        ledger.insert_record(db, "transactions", bindings, "NEW_TRANSACTION")

        tx = list(cursor.execute("""SELECT * FROM transactions WHERE tx_index = ?""", (tx_index,)))[
            0
        ]
    except exceptions.BTCOnlyError:
        pass

    cursor.close()

    MOCK_UTXO_SET.add_raw_transaction(raw_transaction, tx_id=tx_hash, confirmations=1)

    util.CURRENT_BLOCK_INDEX = block_index
    blocks.parse_block(db, block_index, block_time)
    return tx_hash, tx


def insert_unconfirmed_raw_transaction(raw_transaction, db):
    """Add a raw transaction to the database."""
    # one transaction per block
    cursor = db.cursor()

    tx_hash = dummy_tx_hash(raw_transaction)

    # this isn't really correct, but it will do
    tx_index = list(
        cursor.execute("""SELECT tx_index FROM transactions ORDER BY tx_index DESC LIMIT 1""")
    )
    tx_index = tx_index[0]["tx_index"] if len(tx_index) else 0
    tx_index = tx_index + 1

    deserialized_tx = deserialize.deserialize_tx(raw_transaction, True)
    source, destination, btc_amount, fee, data, extra = gettxinfo._get_tx_info(
        db, deserialized_tx, util.CURRENT_BLOCK_INDEX
    )
    utxos_info = gettxinfo.get_utxos_info(db, deserialized_tx)
    tx = {
        "tx_index": tx_index,
        "tx_hash": tx_hash,
        "block_index": config.MEMPOOL_BLOCK_INDEX,
        "block_hash": config.MEMPOOL_BLOCK_HASH,
        "block_time": int(time.time()),
        "source": source,
        "destination": destination,
        "btc_amount": btc_amount,
        "fee": fee,
        "data": data,
        "supported": True,
        "utxos_info": " ".join(utxos_info),
    }

    cursor.close()

    MOCK_UTXO_SET.add_raw_transaction(raw_transaction, tx_id=tx_hash, confirmations=0)

    return tx


UNIQUE_DUMMY_TX_HASH = {}


def dummy_tx_hash(raw_transaction):
    global UNIQUE_DUMMY_TX_HASH  # noqa: PLW0602

    tx = pycoin.coins.bitcoin.Tx.Tx.from_hex(raw_transaction)

    # normalize inputs
    for txin in tx.txs_in:
        txin.previous_hash = b"\x00" * 32
        txin.previous_index = 0
        txin.script = b"\x00"

    # check if we have a change output
    if tx.txs_out[-1].coin_value not in [
        0,
        config.DEFAULT_REGULAR_DUST_SIZE,
        config.DEFAULT_MULTISIG_DUST_SIZE,
        config.DEFAULT_OP_RETURN_VALUE,
    ]:
        tx.txs_out[-1].coin_value = 0  # set change to 0

    tx_id = tx.id()
    # print(tx_id)

    # check we haven't created this before (if we do 2 exactly the sends for example)
    if tx_id in UNIQUE_DUMMY_TX_HASH:
        logger.warning(f"BUMP TXID {tx_id}")
        UNIQUE_DUMMY_TX_HASH[tx_id] += 1
        tx_id = hashlib.sha256(f"{tx_id}{UNIQUE_DUMMY_TX_HASH[tx_id]}".encode("utf-8")).hexdigest()
    else:
        UNIQUE_DUMMY_TX_HASH[tx_id] = 0

    return tx_id


def insert_transaction(transaction, db):
    """Add a transaction to the database."""

    block_bindings = {
        "block_index": transaction["block_index"],
        "block_hash": transaction["block_hash"],
        "block_time": transaction["block_time"],
        "ledger_hash": None,
        "txlist_hash": None,
        "previous_block_hash": None,
        "difficulty": None,
    }
    ledger.insert_record(db, "blocks", block_bindings, "NEW_BLOCK")
    ledger.insert_record(db, "transactions", transaction, "NEW_TRANSACTION")

    # `dispenser.dispense()` needs some vouts. Let's say one vout per transaction.
    transaction_outputs_bindings = {
        "tx_index": transaction["tx_index"],
        "tx_hash": transaction["tx_hash"],
        "block_index": transaction["block_index"],
        "out_index": 0,
        "destination": transaction["destination"],
        "btc_amount": transaction["btc_amount"],
    }
    ledger.insert_record(
        db, "transaction_outputs", transaction_outputs_bindings, "NEW_TRANSACTION_OUTPUT"
    )

    util.CURRENT_BLOCK_INDEX = transaction["block_index"]


def initialise_rawtransactions_db(db):
    prefill_rawtransactions_db(db)


def prefill_rawtransactions_db(db):
    """Drop old raw transaction table, create new one and populate it from unspent_outputs.json."""
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS raw_transactions")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS raw_transactions(tx_hash TEXT UNIQUE, tx_hex TEXT, confirmations INT)"
    )
    with open(CURR_DIR + "/fixtures/unspent_outputs.json", "r") as listunspent_test_file:
        wallet_unspent = json.load(listunspent_test_file)
        for output in wallet_unspent:
            txid = output["txid"]
            tx = deserialize.deserialize_tx(output["txhex"], True)  # noqa: F841
            cursor.execute(
                "INSERT INTO raw_transactions VALUES (?, ?, ?)",
                (txid, output["txhex"], output["confirmations"]),
            )
    cursor.close()


def save_rawtransaction(db, txid, tx_hex, confirmations=0):
    """Insert the raw transaction into the db."""
    if isinstance(txid, bytes):
        txid = binascii.hexlify(txid).decode("ascii")

    cursor = db.cursor()
    try:
        if isinstance(txid, bytes):
            txid = binascii.hexlify(txid).decode("ascii")
        cursor.execute(
            """INSERT INTO raw_transactions VALUES (?, ?, ?)""", (txid, tx_hex, confirmations)
        )
    except Exception as e:  # TODO  # noqa: F841, S110
        pass
    cursor.close()


def getrawtransaction(db, txid, verbose=False, block_index=None):
    """
    Return raw transactions with specific hash.

    When verbose=True we mock the bitcoind RPC response, it's incomplete atm and only mocks what we need
     if more stuff is needed, add it ..
    """
    cursor = db.cursor()

    if isinstance(txid, bytes):
        txid = binascii.hexlify(txid).decode("ascii")

    tx_hex, confirmations = list(
        cursor.execute(
            """SELECT tx_hex, confirmations FROM raw_transactions WHERE tx_hash = ?""", (txid,)
        )
    )[0]
    cursor.close()

    if verbose:
        return mock_bitcoind_verbose_tx_output(tx_hex, txid, confirmations)
    else:
        return tx_hex


def mock_bitcoind_verbose_tx_output(tx, txid, confirmations):
    if isinstance(tx, bitcoinlib.core.CTransaction):
        ctx = tx
    else:
        if not isinstance(tx, bytes):
            tx = binascii.unhexlify(tx)
        ctx = bitcoinlib.core.CTransaction.deserialize(tx)

    result = {
        "version": ctx.nVersion,
        "locktime": ctx.nLockTime,
        "txid": txid,  # bitcoinlib.core.b2lx(ctx.GetHash()),
        "hex": binascii.hexlify(ctx.serialize()).decode("ascii"),
        "size": len(ctx.serialize()),
        "confirmations": confirmations,
        "vin": [],
        "vout": [],
        # not mocked yet
        "time": None,
        "blockhash": None,
        "blocktime": None,
    }

    for vin in ctx.vin:
        asm = list(
            map(
                lambda op: binascii.hexlify(op).decode("ascii")
                if isinstance(op, bytes)
                else str(op),
                list(vin.scriptSig),
            )
        )
        rvin = {  # noqa: F841
            "txid": bitcoinlib.core.b2lx(vin.prevout.hash),
            "vout": vin.prevout.n,
            "scriptSig": {
                "hex": binascii.hexlify(vin.scriptSig).decode("ascii"),
                "asm": " ".join(asm),
            },
            "sequence": vin.nSequence,
        }

        # result['vin'].append(rvin)

    for idx, vout in enumerate(ctx.vout):
        if list(vout.scriptPubKey)[-1] == bitcoinlib.core.script.OP_CHECKMULTISIG:
            pubkeys = list(vout.scriptPubKey)[1:-2]
            addresses = []
            for pubkey in pubkeys:
                addr = str(bitcoinlib.wallet.P2PKHBitcoinAddress.from_pubkey(pubkey))

                addresses.append(addr)
        else:
            try:
                addresses = [
                    str(bitcoinlib.wallet.CBitcoinAddress.from_scriptPubKey(vout.scriptPubKey))
                ]
            except bitcoinlib.wallet.CBitcoinAddressError:
                addresses = []

        asm = list(
            map(
                lambda op: binascii.hexlify(op).decode("ascii")
                if isinstance(op, bytes)
                else str(op),
                list(vout.scriptPubKey),
            )
        )

        type = "unknown"
        if vout.scriptPubKey[-1] == bitcoinlib.core.script.OP_CHECKMULTISIG:
            type = "multisig"
        elif (
            len(list(vout.scriptPubKey)) == 5
            and vout.scriptPubKey[1] == bitcoinlib.core.script.OP_HASH160
            and vout.scriptPubKey[-2] == bitcoinlib.core.script.OP_EQUALVERIFY
            and vout.scriptPubKey[-1] == bitcoinlib.core.script.OP_CHECKSIG
        ):
            type = "pubkeyhash"
        else:
            type = "witnesspkh"

        rvout = {
            "n": idx,
            "value": vout.nValue / config.UNIT,
            "script_pub_key": {
                "type": type,
                "addresses": addresses,
                "hex": binascii.hexlify(vout.scriptPubKey).decode("ascii"),
                "asm": " ".join(asm),
            },
        }

        result["vout"].append(rvout)

    return result


def getrawtransaction_batch(db, txhash_list, verbose=False):
    result = {}
    for txhash in txhash_list:
        result[txhash] = getrawtransaction(db, txhash, verbose=verbose)

    return result


def extract_addresses_from_txlist(tx_hashes_tx, _getrawtransaction_batch):
    """
    helper for extract_addresses, seperated so we can pass in a mocked _getrawtransaction_batch for test purposes
    """

    tx_hashes_addresses = {}
    tx_inputs_hashes = set()  # use set to avoid duplicates

    for tx_hash, tx in tx_hashes_tx.items():
        tx_hashes_addresses[tx_hash] = set()
        for vout in tx["vout"]:
            if "addresses" in vout["script_pub_key"]:
                tx_hashes_addresses[tx_hash].update(tuple(vout["script_pub_key"]["addresses"]))

        tx_inputs_hashes.update([vin["txid"] for vin in tx["vin"]])

    # chunk txs to avoid huge memory spikes
    for tx_inputs_hashes_chunk in util.chunkify(
        list(tx_inputs_hashes), config.BACKEND_RAW_TRANSACTIONS_CACHE_SIZE
    ):
        raw_transactions = _getrawtransaction_batch(tx_inputs_hashes_chunk, verbose=True)
        for tx_hash, tx in tx_hashes_tx.items():
            for vin in tx["vin"]:
                vin_tx = raw_transactions.get(vin["txid"], None)

                if not vin_tx:
                    continue

                vout = vin_tx["vout"][vin["vout"]]
                if "addresses" in vout["script_pub_key"]:
                    tx_hashes_addresses[tx_hash].update(tuple(vout["script_pub_key"]["addresses"]))

    return tx_hashes_addresses, tx_hashes_tx


def search_raw_transactions(db, address, unconfirmed=False):
    cursor = db.cursor()

    try:
        all_tx_hashes = list(
            map(
                lambda r: r[0],
                cursor.execute(
                    """SELECT tx_hash FROM raw_transactions WHERE confirmations >= ?""",
                    (0 if unconfirmed else 1,),
                ),
            )
        )

        tx_hashes_tx = getrawtransaction_batch(db, all_tx_hashes, verbose=True)

        def _getrawtransaction_batch(txhash_list, verbose=False):
            return getrawtransaction_batch(db, txhash_list, verbose)

        tx_hashes_addresses, tx_hashes_tx = extract_addresses_from_txlist(
            tx_hashes_tx, _getrawtransaction_batch
        )

        reverse_tx_map = {}
        tx_map = {}

        # add txs to cache and reverse cache
        for tx_hash, addresses in tx_hashes_addresses.items():
            reverse_tx_map.setdefault(tx_hash, set())

            for _address in addresses:
                tx_map.setdefault(_address, set())
                tx_map[_address].add(tx_hash)
                reverse_tx_map[tx_hash].add(_address)

        tx_hashes = tx_map.get(address, set())

        if len(tx_hashes):
            return sorted(
                getrawtransaction_batch(db, tx_hashes, verbose=True).values(),
                key=lambda tx: (tx["confirmations"], tx["txid"]),
            )
        else:
            return []
    finally:
        cursor.close()


def initialise_db(db):
    """Initialise blockchain in the db and insert first block."""
    blocks.initialise(db)
    insert_block(db, config.BLOCK_FIRST - 1, parse_block=True)


def run_scenario(scenario):
    """Execute a scenario for integration test, returns a dump of the db, a json with raw transactions and the full log."""
    server.initialise(database_file=":memory:", testnet=True, **COUNTERPARTYD_OPTIONS)
    util.FIRST_MULTISIG_BLOCK_TESTNET = 1
    checkpoints = dict(check.CHECKPOINTS_TESTNET)
    check.CHECKPOINTS_TESTNET = {}

    logger = logging.getLogger(config.LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger_buff = io.StringIO()
    handler = logging.StreamHandler(logger_buff)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    asyncio_log = logging.getLogger("asyncio")
    asyncio_log.setLevel(logging.ERROR)

    db = database.get_connection(read_only=False)
    initialise_db(db)

    raw_transactions = []

    transaction.initialise(force=True)

    for tx in scenario:
        if tx[0] != "create_next_block":
            mock_protocol_changes = tx[3] if len(tx) == 4 else {}
            with MockProtocolChangesContext(**(mock_protocol_changes or {})):
                module = sys.modules[f"counterpartycore.lib.messages.{tx[0]}"]
                compose = module.compose
                unsigned_tx_hex = transaction.construct(
                    db=db, tx_info=compose(db, *tx[1]), regular_dust_size=5430, **tx[2]
                )
                raw_transactions.append({tx[0]: unsigned_tx_hex})
                insert_raw_transaction(unsigned_tx_hex, db)
        else:
            create_next_block(
                db,
                block_index=config.BURN_START + tx[1],
                parse_block=tx[2] if len(tx) == 3 else True,
            )

    check.asset_conservation(db)

    dump = dump_database(db)
    log = logger_buff.getvalue()

    db.close()
    check.CHECKPOINTS_TESTNET = checkpoints
    return dump, log, json.dumps(raw_transactions, indent=4)


def save_scenario(scenario_name):
    """Save currently run scenario's output for comparison with the expected outputs."""
    dump, log, raw_transactions = run_scenario(INTEGRATION_SCENARIOS[scenario_name][0])

    save_scenario_output(scenario_name, dump, log, raw_transactions)


def save_scenario_output(scenario_name, dump, log, raw_transactions):
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".new.sql", "w") as f:
        f.writelines(dump)
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".new.log", "w") as f:
        f.writelines(log)
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".new.json", "w") as f:
        f.writelines(raw_transactions)


def load_scenario_ouput(scenario_name):
    """Read and return the current log output."""
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".sql", "r") as f:
        dump = ("").join(f.readlines())
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".log", "r") as f:
        log = ("").join(f.readlines())
    with open(CURR_DIR + "/fixtures/scenarios/" + scenario_name + ".json", "r") as f:
        raw_transactions = ("").join(f.readlines())
    return dump, log, raw_transactions


def clean_scenario_dump(scenario_name, dump):
    """Replace addresses and hashes to compare a scenario with its base scenario."""
    dump = dump.replace(standard_scenarios_params[scenario_name]["address1"], "address1")
    dump = dump.replace(standard_scenarios_params[scenario_name]["address2"], "address2")
    dump = re.sub(r"[a-f0-9]{64}", "hash", dump)
    dump = re.sub(r"X\'[A-F0-9]+\',1\);", "'data',1);", dump)
    return dump


def check_record(record, server_db, pytest_config):
    """Allow direct record access to the db."""
    cursor = server_db.cursor()

    if record["table"] == "pragma":
        field = record["field"]
        sql = f"""PRAGMA {field}"""
        value = cursor.execute(sql).fetchall()[0][field]
        assert value == record["value"]
    else:
        sql = f"""SELECT COUNT(*) AS c FROM {record['table']} """  # noqa: S608
        sql += """WHERE """
        bindings = []
        conditions = []
        for field in record["values"]:
            if record["values"][field] is not None:
                conditions.append(f"""{field} = ?""")
                bindings.append(record["values"][field])
        sql += " AND ".join(conditions)

        count = list(cursor.execute(sql, tuple(bindings)))[0]["c"]
        ok = (record.get("not", False) and count == 0) or count == 1

        if not ok:
            if pytest_config.getoption("verbose") >= 2:
                print("expected values: ")
                pprint.PrettyPrinter(indent=4).pprint(record["values"])
                print(
                    f"SELECT * FROM {record['table']} WHERE block_index = {record['values']['block_index']}: "  # noqa: S608
                )
                pprint.PrettyPrinter(indent=4).pprint(
                    list(cursor.execute(f"""SELECT * FROM {record['table']}"""))  # noqa: S608
                )

            raise AssertionError(
                "check_record \n"
                + "table="
                + record["table"]
                + " \n"
                + "conditions="
                + ",".join(conditions)
                + " \n"
                + "bindings="
                + ",".join(map(lambda v: str(v), bindings))
            )


def vector_to_args(vector, functions=[], pytest_config=None):  # noqa: B006
    """Translate from UNITTEST_VECTOR style to function arguments."""
    args = []
    for tx_name in sorted(vector.keys()):
        for method in sorted(vector[tx_name].keys()):
            for params in vector[tx_name][method]:
                error = params.get("error", None)
                outputs = params.get("out", None)
                records = params.get("records", None)
                comment = params.get("comment", None)
                mock_protocol_changes = params.get("mock_protocol_changes", None)
                config_context = params.get("config_context", {})
                if functions == [] or (tx_name + "." + method) in functions:
                    args.append(
                        (
                            tx_name,
                            method,
                            params["in"],
                            outputs,
                            error,
                            records,
                            comment,
                            mock_protocol_changes,
                            config_context,
                            pytest_config,
                        )
                    )
    return args


def exec_tested_method(tx_name, method, tested_method, inputs, server_db):
    """Execute tested_method within context and arguments."""
    if tx_name == "transaction" and method == "construct":
        return tested_method(server_db, inputs[0], **inputs[1])
    elif (
        (
            tx_name == "util"
            and (
                method
                in [
                    "api",
                    "date_passed",
                    "dhash_string",
                    "get_url",
                    "hexlify",
                    "parse_subasset_from_asset_name",
                    "compact_subasset_longname",
                    "expand_subasset_longname",
                    "enabled",
                ]
            )
        )
        or (
            tx_name == "ledger"
            and (
                method
                in [
                    "price",
                    "generate_asset_id",
                    "generate_asset_name",
                ]
            )
        )
        or method == "get_tx_info_legacy"
        or tx_name
        in [
            "script",
            "transaction",
            "transaction_helper.serializer",
            "backend",
            "message_type",
            "address",
        ]
        or (
            tx_name
            in [
                "fairminter",
                "fairmint",
                "utxo",
                "versions.enhanced_send",
                "versions.mpma",
                "sweep",
            ]
            and method == "unpack"
        )
    ):
        return tested_method(*inputs)
    else:
        if isinstance(inputs, dict):
            return tested_method(server_db, **inputs)
        else:
            return tested_method(server_db, *inputs)


def check_outputs(
    tx_name,
    method,
    inputs,
    outputs,
    error,
    records,
    comment,
    mock_protocol_changes,
    pytest_config,
    server_db,
):
    """Check actual and expected outputs of a particular function."""

    try:
        tested_module = sys.modules[f"counterpartycore.lib.{tx_name}"]
    except KeyError:  # TODO: hack
        if tx_name == "api_v1":
            tested_module = sys.modules["counterpartycore.lib.api.api_v1"]
        else:
            tested_module = sys.modules[f"counterpartycore.lib.messages.{tx_name}"]
    tested_method = getattr(tested_module, method)

    default_protocol_changes = mock_protocol_changes or {}
    if method in ["compose", "pack"] and "short_tx_type_id" not in default_protocol_changes:
        default_protocol_changes["short_tx_type_id"] = False

    with MockProtocolChangesContext(**default_protocol_changes):
        test_outputs = None
        if error is not None:
            if pytest_config.getoption("verbose") >= 2:
                print("Expected error:", error[0], error[1])
            if error[0] == "Warning":
                with pytest.warns(None) as record:
                    test_outputs = exec_tested_method(
                        tx_name, method, tested_method, inputs, server_db
                    )
                assert str(record[0].message) == error[1]
            else:
                with pytest.raises(error[0]) as exception:
                    test_outputs = exec_tested_method(
                        tx_name, method, tested_method, inputs, server_db
                    )
                assert exception.value.args[0] == error[1]
        else:
            test_outputs = exec_tested_method(tx_name, method, tested_method, inputs, server_db)
            if pytest_config.getoption("gentxhex") and method == "compose":
                print("--------------------------")
                tx_params = {
                    #'encoding': 'multisig'
                }
                if tx_name == "order" and inputs[1] == "BTC":
                    print("give btc")
                    tx_params["fee_provided"] = DP["fee_provided"]
                unsigned_tx_hex = transaction.construct(server_db, test_outputs, **tx_params)
                print(tx_name)
                print(unsigned_tx_hex)
                print("--------------------------")

        if outputs is not None:
            try:
                assert outputs == test_outputs
            except AssertionError:
                if pytest_config.getoption("verbose") >= 2:
                    msg = (
                        "expected outputs don't match test_outputs:\nexpected_outputs=\n"
                        + pprint.pformat(outputs)
                        + "\ntest_outputs=\n"
                        + pprint.pformat(test_outputs)
                    )
                else:
                    msg = f"expected outputs don't match test_outputs: expected_outputs={outputs} test_outputs={test_outputs}"
                import json

                print(json.dumps(test_outputs, indent=4))
                raise Exception(msg)  # noqa: B904
        if records is not None:
            for record in records:
                check_record(record, server_db, pytest_config)


def compare_strings(string1, string2):
    """Compare strings diff-style."""
    diff = list(difflib.unified_diff(string1.splitlines(1), string2.splitlines(1), n=0))
    if len(diff):
        logger.info("\nDifferences:")
        logger.info("\n".join(diff))
    return len(diff)


def get_block_ledger(db, block_index):
    """Return the block's ledger."""
    cursor = db.cursor()
    debits = list(cursor.execute("""SELECT * FROM debits WHERE block_index = ?""", (block_index,)))
    credits = list(
        cursor.execute("""SELECT * FROM credits WHERE block_index = ?""", (block_index,))
    )
    debits = [json.dumps(m).replace('"', "'") for m in debits]
    credits = [json.dumps(m).replace('"', "'") for m in credits]
    ledger = json.dumps(debits + credits, indent=4)
    return ledger


def get_block_txlist(db, block_index):
    """Return block's transaction list."""
    cursor = db.cursor()
    txlist = list(
        cursor.execute("""SELECT * FROM transactions WHERE block_index = ?""", (block_index,))
    )
    txlist = [json.dumps(m).replace('"', "'") for m in txlist]
    txlist = json.dumps(txlist, indent=4)
    return txlist


class ConfigContext(object):
    def __init__(self, **kwargs):
        self.config = config
        self._extend = kwargs
        self._before = {}
        self._before_empty = []

    def __enter__(self):
        self._before = {}
        for k in self._extend:
            if k in vars(self.config):
                self._before[k] = vars(self.config)[k]
            else:
                self._before_empty.append(k)

            vars(self.config)[k] = self._extend[k]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k in self._before:
            vars(self.config)[k] = self._before[k]
        for k in self._before_empty:
            del vars(self.config)[k]


class MockProtocolChangesContext(object):
    def __init__(self, **kwargs):
        from counterpartycore.test.conftest import MOCK_PROTOCOL_CHANGES

        self.mock_protocol_changes = MOCK_PROTOCOL_CHANGES
        self._extend = kwargs
        self._before = {}
        self._before_empty = []

    def __enter__(self):
        self._before = {}
        for k in self._extend:
            if k in self.mock_protocol_changes:
                self._before[k] = self.mock_protocol_changes[k]
            else:
                self._before_empty.append(k)

            self.mock_protocol_changes[k] = self._extend[k]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k in self._before:
            self.mock_protocol_changes[k] = self._before[k]
        for k in self._before_empty:
            del self.mock_protocol_changes[k]


def get_oldest_tx_mock(address, block_index=None):
    if address == "mrHFGUKSiNMeErqByjX97qPKfumdZxe6mC" and block_index == 99999999999:
        return {
            "block_index": 2576100,
            "tx_hash": "d6751cc77da77d9270e16046a19954bfaffc005269f0c6a9248e680be6d1f468",
        }
    return {}


def reparse(testnet=True, checkpoint_count=5):
    """
    Reparse all transaction from the database.
     - Create a new in-memory DB, copy the DB that is on-disk
     - Reparse DB, automatically compares consensus hashes to the original ones from the on-disk DB
    """

    # mock the backend
    backend.addrindexrs.get_oldest_tx = get_oldest_tx_mock

    # create a new in-memory DB
    options = dict(COUNTERPARTYD_OPTIONS)
    server.initialise(database_file=":memory:", testnet=testnet, **options)
    memory_db = database.get_connection(read_only=False)

    # connect to the on-disk DB
    data_dir = appdirs.user_data_dir(
        appauthor=config.XCP_NAME, appname=config.APP_NAME, roaming=True
    )
    prod_db_path = os.path.join(data_dir, f"{config.APP_NAME}{'.testnet' if testnet else ''}.db")
    assert os.path.exists(prod_db_path), f"database path {prod_db_path} does not exist"
    prod_db = apsw.Connection(prod_db_path, flags=apsw.SQLITE_OPEN_READONLY)
    prod_db.setrowtrace(database.rowtracer)

    # Copy DB from file on disk (should be a DB file with at least all the checkpoints)
    #  in-memory DB shouldn't have been written to yet up until this point
    logger.info(f"Copying database from {prod_db_path} to memory...")
    with memory_db.backup("main", prod_db, "main") as backup:
        while not backup.done:
            backup.step(100)

    # Check that all checkpoint blocks are in the database to be tested.
    if testnet:
        CHECKPOINTS = check.CHECKPOINTS_TESTNET
    else:
        CHECKPOINTS = check.CHECKPOINTS_MAINNET

    # we start one block after the checkpoint before the first one we want to check
    block_index = sorted(list(CHECKPOINTS.keys()))[-checkpoint_count - 1]
    print(f"Checking from block {block_index}")

    # Initialise missing tables
    blocks.initialise(memory_db)

    try:
        blocks.reparse(memory_db, block_index)
    except check.ConsensusError as e:
        message = str(e)
        block_pos = message.index("block ") + 6
        error_block_index = int(message[block_pos : message.index(" ", block_pos)])
        if message.find("ledger_hash") != -1:
            new_ledger = get_block_ledger(memory_db, error_block_index)
            old_ledger = get_block_ledger(prod_db, error_block_index)
            compare_strings(f"Old ledger:\n{old_ledger}", f"New ledger:\n{new_ledger}")
        elif message.find("txlist_hash") != -1:
            new_txlist = get_block_txlist(memory_db, error_block_index)
            old_txlist = get_block_txlist(prod_db, error_block_index)
            compare_strings(f"Old TX list:\n{old_txlist}", f"New TX list:\n{new_txlist}")
        raise e
