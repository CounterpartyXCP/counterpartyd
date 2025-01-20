#!/usr/bin/env python3

import binascii
import json
import os
import signal
import struct
import sys
import threading
import time
import urllib.parse
from io import StringIO

import sh
from arc4 import ARC4
from bitcoinutils.keys import P2wpkhAddress
from bitcoinutils.script import Script, b_to_h
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from counterpartycore.lib import config, exceptions
from counterpartycore.lib.utils import database

setup("regtest")

WALLET_NAME = "xcpwallet"


class RegtestNode:
    def __init__(
        self,
        datadir="regtestnode",
        show_output=False,
        wsgi_server="waitress",
        burn_in_one_block=False,
    ):
        self.datadir = datadir
        self.bitcoin_cli = sh.bitcoin_cli.bake(
            "-regtest",
            "-rpcuser=rpc",
            "-rpcpassword=rpc",
            "-rpcconnect=localhost",
            f"-datadir={self.datadir}",
        )
        self.bitcoin_cli_2 = sh.bitcoin_cli.bake(
            "-regtest",
            "-rpcuser=rpc",
            "-rpcpassword=rpc",
            "-rpcconnect=localhost",
            "-rpcport=28443",
            f"-datadir={self.datadir}/node2",
        )
        self.bitcoin_wallet = self.bitcoin_cli.bake(f"-rpcwallet={WALLET_NAME}")
        self.bitcoin_wallet_2 = self.bitcoin_cli_2.bake(f"-rpcwallet={WALLET_NAME}")
        self.bitcoind_process = None
        self.addresses = []
        self.block_count = 0
        self.tx_index = -1
        self.ready = False
        self.show_output = show_output
        self.counterparty_server = sh.counterparty_server.bake(
            "--regtest",
            f"--data-dir={self.datadir}",
            f"--wsgi-server={wsgi_server}",
            "--gunicorn-workers=2",
            "--no-telemetry",
            "--electrs-url=http://localhost:3002",
            "-vv",
        )
        self.burn_in_one_block = burn_in_one_block
        self.electrs_process = None
        self.electrs_process_2 = None
        self.electrs_process_pid = None
        self.electrs_process_2_pid = None
        self.second_node_started = False

    def api_call(self, url):
        result = sh.curl(f"http://localhost:24000/v2/{url}").strip()
        # print(result)
        return json.loads(result)

    def get_mempool_event_count(self):
        result = self.api_call("mempool/events")
        return result["result_count"]

    def wait_for_bitcoind(self, node=1):
        while True:
            try:
                if node == 1:
                    self.bitcoin_cli("getblockchaininfo")
                else:
                    self.bitcoin_cli_2("getblockchaininfo")
                break
            except sh.ErrorReturnCode:
                print("Waiting for bitcoind to start...")
                time.sleep(1)

    def disable_protocol_changes(self, change_names):
        regtest_protocole_file = os.path.join(self.datadir, "regtest_disabled_changes.json")
        with open(regtest_protocole_file, "w") as f:
            f.write(json.dumps(change_names))

    def enable_all_protocol_changes(self):
        regtest_protocole_file = os.path.join(self.datadir, "regtest_disabled_changes.json")
        if os.path.exists(regtest_protocole_file):
            os.remove(regtest_protocole_file)

    def broadcast_transaction(
        self, signed_transaction, no_confirmation=False, dont_wait_mempool=False, retry=0
    ):
        mempool_event_count_before = self.get_mempool_event_count()
        tx_hash = self.bitcoin_wallet("sendrawtransaction", signed_transaction, 0).strip()
        if not no_confirmation:
            block_hash, block_time = self.mine_blocks(1)
        else:
            block_hash, block_time = "mempool", 9999999
            while (
                not dont_wait_mempool
                and self.get_mempool_event_count() == mempool_event_count_before
            ):
                print("waiting for mempool event parsing...")
                time.sleep(5)
        self.tx_index += 1
        self.wait_for_counterparty_server()
        return tx_hash, block_hash, block_time

    def compose_and_send_transaction(
        self, source, messsage_id=None, data=None, no_confirmation=False, dont_wait_mempool=False
    ):
        list_unspent = json.loads(
            self.bitcoin_cli("listunspent", 0, 9999999, json.dumps([source])).strip()
        )
        sorted(list_unspent, key=lambda x: -x["amount"])
        utxo = list_unspent[0]

        tx_inputs = [TxInput(utxo["txid"], utxo["vout"])]
        tx_outputs = []

        if data is not None:
            tx_data = b"CNTRPRTY"
            if messsage_id is not None:
                tx_data += struct.pack(config.SHORT_TXTYPE_FORMAT, messsage_id)
            tx_data += data
            key = binascii.unhexlify(utxo["txid"])
            encrypted_data = ARC4(key).encrypt(data)
            tx_outputs.append(TxOutput(0, Script(["OP_RETURN", b_to_h(encrypted_data)])))

        tx_outputs.append(
            TxOutput(int(utxo["amount"] * 1e8), P2wpkhAddress(source).to_script_pub_key())
        )

        tx = Transaction(tx_inputs, tx_outputs)
        tx_hex = tx.to_hex()

        signed_transaction_json = self.bitcoin_wallet(
            "signrawtransactionwithwallet", tx_hex
        ).strip()
        signed_transaction = json.loads(signed_transaction_json)["hex"]

        tx_hash, _block_hash, _block_time = self.broadcast_transaction(
            signed_transaction, no_confirmation, dont_wait_mempool
        )

        print(f"Transaction sent: {source} {data} ({tx_hash})")

        return f"{utxo['txid']}:{utxo['vout']}", tx_hash

    def compose(self, source, tx_name, params):
        query_string = []
        for key, value in params.items():
            if not isinstance(value, list):
                query_string.append(urllib.parse.urlencode({key: value}))
            else:
                for i in range(len(value)):
                    query_string.append(urllib.parse.urlencode({key: value[i]}))
        query_string = "&".join(query_string)

        if tx_name in ["detach", "movetoutxo"]:
            compose_url = f"utxos/{source}/compose/{tx_name}?{query_string}"
        else:
            compose_url = f"addresses/{source}/compose/{tx_name}?{query_string}"
        return self.api_call(compose_url)

    def send_transaction(
        self,
        source,
        tx_name,
        params,
        return_only_data=False,
        no_confirmation=False,
        dont_wait_mempool=False,
        retry=0,
    ):
        self.wait_for_counterparty_server()

        if return_only_data:
            params["return_only_data"] = True
        if "exact_fee" not in params:
            params["exact_fee"] = 10000  # fixed fee
        # print("Inputs set:", params["inputs_set"])
        params["verbose"] = True

        result = self.compose(source, tx_name, params)

        # print(result)
        if "error" in result:
            if result["error"] == "Counterparty not ready":
                print("Counterparty not ready")
                print("Sleeping for 5 seconds and retrying...")
                time.sleep(5)
                return self.send_transaction(
                    source,
                    tx_name,
                    params,
                    return_only_data,
                    no_confirmation,
                    dont_wait_mempool=dont_wait_mempool,
                )
            raise exceptions.ComposeError(result["error"])
        if return_only_data:
            return result["result"]["data"]
        raw_transaction = result["result"]["rawtransaction"]
        # print(f"Raw transaction: {raw_transaction}")
        signed_transaction_json = self.bitcoin_wallet(
            "signrawtransactionwithwallet", raw_transaction
        ).strip()
        signed_transaction = json.loads(signed_transaction_json)["hex"]
        try:
            tx_hash, block_hash, block_time = self.broadcast_transaction(
                signed_transaction, no_confirmation, dont_wait_mempool=dont_wait_mempool
            )
        except sh.ErrorReturnCode_25 as e:
            if retry < 6:
                print("Error: bad-txns-inputs-missingorspent")
                print("Sleeping for 5 seconds and retrying...")
                time.sleep(10)
                return self.send_transaction(
                    source,
                    tx_name,
                    params,
                    return_only_data,
                    no_confirmation,
                    dont_wait_mempool,
                    retry + 1,
                )
            else:
                raise e
        print(f"Transaction sent: {tx_name} {params} ({tx_hash})")
        return tx_hash, block_hash, block_time, result["result"]["data"]

    def wait_for_counterparty_server(self, block=None):
        target_block = block or self.block_count
        while True:
            try:
                result = self.api_call("")
                if result and "result" in result and result["result"]["server_ready"]:
                    current_block = result["result"]["counterparty_height"]
                    if current_block < target_block:
                        print(f"Waiting for block {current_block} < {target_block}")
                        raise exceptions.ServerNotReady
                    else:
                        return
                elif result and "result" in result:
                    print(
                        f"Server not ready: {result['result']['counterparty_height']} < {result['result']['backend_height']}"
                    )
                    raise exceptions.ServerNotReady
                raise json.JSONDecodeError("Invalid response", "", 0)
            except (sh.ErrorReturnCode, exceptions.ServerNotReady, json.JSONDecodeError) as e:
                if not isinstance(e, exceptions.ServerNotReady):
                    print("Waiting for counterparty...")
                time.sleep(1)

    def wait_for_counterparty_follower(self):
        while True:
            if "Starting blockchain watcher..." in self.server_out.getvalue():
                print("Server ready")
                return
            print("Waiting for counterparty server...")
            time.sleep(2)

    def wait_for_counterparty_watcher(self):
        while True:
            if "API.Watcher - Catch up completed." in self.server_out.getvalue():
                print("Server ready")
                return
            print("Waiting for counterparty server...")
            time.sleep(2)

    def mine_blocks(self, blocks=1, address=None):
        reward_address = address or self.addresses[0]
        block_hashes_json = self.bitcoin_wallet("generatetoaddress", blocks, reward_address)
        block_hashes = json.loads(block_hashes_json)
        block_hash = block_hashes.pop()
        block_info_json = self.bitcoin_cli("getblock", block_hash, 1)
        block_time = json.loads(block_info_json)["time"]
        self.block_count += blocks
        return block_hash, block_time

    def generate_addresses_with_btc(self):
        for i in range(10):
            address = self.bitcoin_wallet("getnewaddress", WALLET_NAME, "bech32").strip()
            print(f"Address {i}: {address}")
            self.addresses.append(address)
            self.mine_blocks(1, address)
        self.addresses.sort()
        empty_address = self.bitcoin_wallet("getnewaddress", WALLET_NAME, "legacy").strip()
        self.addresses.append(empty_address)
        print(f"Empty address: {empty_address}")
        self.mine_blocks(101)

    def generate_xcp(self):
        print("Generating XCP...", self.burn_in_one_block)
        for address in self.addresses[0:10]:
            self.send_transaction(
                address,
                "burn",
                {"quantity": 50000000},
                no_confirmation=self.burn_in_one_block,
                dont_wait_mempool=self.burn_in_one_block,
            )
        if self.burn_in_one_block:
            self.mine_blocks(1)
            self.wait_for_counterparty_server()

    def get_inputs_set(self, address, node=1):
        if node == 1:
            list_unspent = json.loads(
                self.bitcoin_cli("listunspent", 0, 9999999, json.dumps([address])).strip()
            )
        else:
            list_unspent = json.loads(
                self.bitcoin_cli_2("listunspent", 0, 9999999, json.dumps([address])).strip()
            )
        # print(list_unspent)
        sorted(list_unspent, key=lambda x: -x["amount"])
        inputs = []
        for utxo in list_unspent[0:99]:
            inputs.append(f"{utxo['txid']}:{utxo['vout']}")
        return ",".join(inputs)

    def start_bitcoin_node(self):
        self.bitcoind_process = sh.bitcoind(
            "-regtest",
            "-daemon",
            "-server",
            "-txindex",
            "-rpcuser=rpc",
            "-rpcpassword=rpc",
            "-rpcallowip=0.0.0.0",
            "-zmqpubrawtx=tcp://0.0.0.0:29332",
            "-zmqpubhashtx=tcp://0.0.0.0:29332",
            "-zmqpubsequence=tcp://0.0.0.0:29332",
            "-zmqpubrawblock=tcp://0.0.0.0:29333",
            "-fallbackfee=0.0002",
            "-acceptnonstdtxn",
            "-minrelaytxfee=0",
            "-blockmintxfee=0",
            "-mempoolfullrbf",
            f"-datadir={self.datadir}",
            _bg=True,
            _out=sys.stdout,
        )
        self.wait_for_bitcoind()

    def start_bitcoin_node_2(self):
        self.bitcoind_process_2 = sh.bitcoind(
            "-regtest",
            "-daemon",
            "-server",
            "-txindex",
            "-rpcuser=rpc",
            "-rpcpassword=rpc",
            "-rpcallowip=0.0.0.0",
            "-fallbackfee=0.0002",
            "-acceptnonstdtxn",
            f"-datadir={self.datadir}/node2",
            "-port=28444",
            "-rpcport=28443",
            "-minrelaytxfee=0",
            "-blockmintxfee=0",
            "-bind=127.0.0.1:2223=onion",
            "-mempoolfullrbf",
            _bg=True,
            _out=sys.stdout,
        )
        self.wait_for_bitcoind(node=2)

    def get_electrs_tip(self, node=1):
        port = 3002 if node == 1 else 3003
        url = f"http://127.0.0.1:{port}/blocks/tip/height"
        return int(sh.curl(url).strip())

    def wait_for_electrs(self, node=1):
        while True:
            try:
                current_block = self.api_call("")["result"]["counterparty_height"]
                tip = self.get_electrs_tip(node)
                if tip >= current_block:
                    print("Electrs ready")
                    break
                print(f"Waiting for electr to catch up ({tip} < {current_block})...")
            except sh.ErrorReturnCode:
                print("Waiting for electr to be ready...")
                time.sleep(1)

    def start_electrs(self, node=1):
        daemon_dir = self.datadir if node == 1 else f"{self.datadir}/node2"
        daemon_rpc_address = "127.0.0.1:18443" if node == 1 else "127.0.0.1:28443"
        electr_port = 3002 if node == 1 else 3003
        self.electrs = sh.electrs.bake(
            "--cookie=rpc:rpc",
            "--network=regtest",
            f"--daemon-dir={daemon_dir}",
            f"--daemon-rpc-addr={daemon_rpc_address}",
            f"--db-dir={self.datadir}/electrsdb",
            f"--http-addr=127.0.0.1:{electr_port}",
        )
        if node == 1:
            self.electrs_process = self.electrs(_bg=True, _out=sys.stdout)
            self.electrs_process_pid = self.electrs_process.process.pid
        else:
            self.electrs_process_2 = self.electrs(_bg=True, _out=sys.stdout)
            self.electrs_process_2_pid = self.electrs_process_2.process.pid

    def stop_electrs(self):
        if self.electrs_process_pid:
            os.kill(self.electrs_process_pid, signal.SIGTERM)

        if self.electrs_process_2_pid:
            os.kill(self.electrs_process_2_pid, signal.SIGTERM)

    def start(self):
        if os.path.exists(self.datadir):
            sh.rm("-rf", self.datadir)
        sh.mkdir(self.datadir)
        sh.mkdir(f"{self.datadir}/node2")

        self.start_bitcoin_node()

        self.bitcoin_cli("createwallet", WALLET_NAME)
        print("Wallet created")

        self.generate_addresses_with_btc()

        # print(self.bitcoin_cli("listreceivedbyaddress"))

        self.server_out = StringIO()
        self.counterparty_server_process = self.counterparty_server(
            "start",
            _bg=True,
            _out=self.server_out,
            _err_to_out=True,
            _bg_exc=False,
        )
        self.wait_for_counterparty_follower()

        self.generate_xcp()

        balances = self.api_call("assets/XCP/balances")["result"]
        for balance in balances:
            print(f"{balance['address']}: {balance['quantity'] / 1e8} XCP")

        print("Regtest node ready")
        self.ready = True

        if self.show_output:
            printed_line_count = 0
            print("Server ready, ctrl-c to stop.")
            while True:
                printed_line_count = print_server_output(self, printed_line_count)
                time.sleep(1)

        while True:
            time.sleep(1)

    def get_gunicorn_workers_pids(self):
        logs = self.server_out.getvalue()
        pids = []
        for line in logs.splitlines():
            if "Booting Gunicorn worker with pid: " in line:
                pid = int(line.split("Booting Gunicorn worker with pid: ")[1].split(" ")[0])
                pids.append(pid)
        return pids

    def kill_gunicorn_workers(self):
        pids = self.get_gunicorn_workers_pids()
        print(f"Killing Gunicorn workers: {pids}")
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def stop_counterparty_server(self):
        try:
            self.counterparty_server_process.terminate()
            self.counterparty_server_process.wait()
            self.kill_gunicorn_workers()
        except Exception as e:
            print(e)
            pass

    def stop_bitcoin_node(self, node=1):
        try:
            if node == 1:
                self.bitcoin_cli("stop", _out=sys.stdout)
            else:
                self.bitcoin_cli_2("stop", _out=sys.stdout)
        except sh.ErrorReturnCode:
            pass

    def stop(self):
        print("Stopping electrs...")
        self.stop_electrs()
        print("Stopping bitcoin node 1...")
        self.stop_bitcoin_node()
        print("Stopping bitcoin node 2...")
        self.stop_bitcoin_node(node=2)
        print("Stopping counterparty-server...")
        self.stop_counterparty_server()

    def get_node_state(self):
        try:
            return {
                "last_block": self.api_call("blocks/last")["result"],
                "last_event": self.api_call("events?limit=1")["result"],
            }
        except KeyError:
            print("Error getting node state, retrying in 2 seconds...")
            time.sleep(2)
            return self.get_node_state()

    def check_node_state(self, command, previous_state):
        self.server_out = StringIO()
        self.counterparty_server_process = self.counterparty_server(
            "start",
            _bg=True,
            _out=self.server_out,
            _err_to_out=True,
            _bg_exc=False,
        )
        self.wait_for_counterparty_follower()
        self.wait_for_counterparty_watcher()
        time.sleep(2)
        state = self.get_node_state()
        if state["last_block"] != previous_state["last_block"]:
            raise Exception(f"{command} failed, last block is different")
        if state["last_event"] != previous_state["last_event"]:
            raise Exception(f"{command} failed, last event is different")

    def test_command(self, command):
        state_before = self.get_node_state()
        self.stop_counterparty_server()
        print(f"Running `{command}`...")
        if command == "check-db":
            self.counterparty_server(
                command,
                _out=sys.stdout,
                _err_to_out=True,
                _bg_exc=False,
            )
        else:
            self.counterparty_server(
                command,
                150,  # avoid tx using `disable_protocol_changes` params (scenario_6_dispenser.py)
                _out=sys.stdout,
                _err_to_out=True,
                _bg_exc=False,
            )
        self.check_node_state(command, state_before)
        print(f"`{command}` successful")

    def test_empty_ledger_hash(self):
        print("Test empty ledger hash...")
        state_before = self.get_node_state()
        self.stop_counterparty_server()
        # delete some ledger hash
        db = database.get_db_connection(
            f"{self.datadir}/counterparty.regtest.db", read_only=False, check_wal=False
        )
        db.execute("UPDATE blocks SET ledger_hash = NULL WHERE block_index > 150")
        db.close()
        self.check_node_state("auto-rollback", state_before)
        print("Empty ledger hash test successful")

    def reparse(self):
        self.test_command("reparse")

    def rollback(self):
        self.test_command("rollback")

    def wait_for_node_to_sync(self):
        block_count_1 = self.bitcoin_cli("getblockcount").strip()
        block_count_2 = self.bitcoin_cli_2("getblockcount").strip()
        while block_count_1 != block_count_2:
            print(f"Waiting for nodes to sync ({block_count_1} != {block_count_2})...")
            block_count_1 = self.bitcoin_cli("getblockcount").strip()
            block_count_2 = self.bitcoin_cli_2("getblockcount").strip()
            time.sleep(1)
        return int(block_count_1)

    def get_burn_count(self, address):
        try:
            return self.api_call(f"addresses/{address}/burns")["result_count"]
        except KeyError:
            print("Error getting burn count, retrying in 2 seconds...")
            time.sleep(2)
            return self.get_burn_count(address)

    def get_xcp_balance(self, address):
        try:
            return self.api_call(f"addresses/{address}/balances/XCP")["result"][0]["quantity"]
        except IndexError:  # no XCP balance
            return 0
        except KeyError:
            print("Error getting XCP balance, retrying in 2 seconds...")
            time.sleep(2)
            return self.get_xcp_balance(address)

    def start_and_wait_second_node(self):
        if self.second_node_started:
            return
        self.second_node_started = True

        print("Start a second node...")
        self.start_bitcoin_node_2()

        print("Connect to the first node...")
        self.bitcoin_cli_2(
            "addnode",
            "localhost:18445",
            "add",
            _out=sys.stdout,
            _err=sys.stdout,
        )

        print("Wait for the two nodes to sync...")
        self.wait_for_node_to_sync()

    def test_reorg(self):
        self.start_and_wait_second_node()

        print("Disconnect from the first node...")
        self.bitcoin_cli_2("disconnectnode", "localhost:18445")

        initial_xcp_balance = self.get_xcp_balance(self.addresses[0])
        print("Initial XCP balance: ", initial_xcp_balance)

        print("Make a burn transaction on first node...")
        self.mine_blocks(3)
        self.send_transaction(self.addresses[0], "burn", {"quantity": 5000})

        print("Burn count before reorganization: ", self.get_burn_count(self.addresses[0]))
        assert self.get_burn_count(self.addresses[0]) == 2

        intermediate_xcp_balance = self.get_xcp_balance(self.addresses[0])
        print("Intermediate XCP balance: ", intermediate_xcp_balance)
        assert intermediate_xcp_balance > initial_xcp_balance

        print("Mine a longest chain on the second node...")
        before_reorg_block = int(self.bitcoin_cli_2("getblockcount").strip())
        self.bitcoin_cli_2("generatetoaddress", 6, self.addresses[0])

        print("Re-connect to the first node...")
        self.bitcoin_cli_2(
            "addnode",
            "localhost:18445",
            "onetry",
            _out=sys.stdout,
            _err=sys.stdout,
        )

        print("Wait for the two nodes to sync...")
        last_block = self.wait_for_node_to_sync()

        self.wait_for_counterparty_server(block=last_block)

        print("Burn count after reorganization: ", self.get_burn_count(self.addresses[0]))

        assert (
            f"Blockchain reorganization detected at block {last_block - 1}"
            in self.server_out.getvalue()
        )
        assert f"Hashes don't match ({before_reorg_block + 1})" in self.server_out.getvalue()
        assert self.get_burn_count(self.addresses[0]) == 1

        final_xcp_balance = self.get_xcp_balance(self.addresses[0])
        print("Final XCP balance: ", final_xcp_balance)
        assert final_xcp_balance == initial_xcp_balance

        # Test reorg with same length chain but one different block
        print("Disconnect from the first node...")
        self.bitcoin_cli_2("disconnectnode", "localhost:18445")

        print("Invalidate the last block on the first node...")
        best_block_hash = self.bitcoin_cli("getbestblockhash").strip()
        self.bitcoin_cli("invalidateblock", best_block_hash)

        self.mine_blocks(1)
        retry = 0
        while (
            f"Current block is not in the blockchain ({last_block + 1})."
            not in self.server_out.getvalue()
        ):
            time.sleep(1)
            retry += 1
            print("Waiting for reorg...")
            assert retry < 100

        # Test reorg with a same length chain but three different blocks
        print("Invalidate block ", last_block - 3)
        previous_block_hash = self.bitcoin_cli("getblockhash", last_block - 3).strip()
        self.bitcoin_cli("invalidateblock", previous_block_hash)
        self.mine_blocks(3)
        retry = 0
        while len(self.server_out.getvalue().split(f"Hashes don't match ({last_block - 3})")) < 3:
            time.sleep(1)
            retry += 1
            print("Waiting for reorg...")
            assert retry < 100

        self.wait_for_counterparty_server(last_block)

        # other tests expect the second node to be connected if running
        print("Re-connect to the first node...")
        self.bitcoin_cli_2(
            "addnode",
            "localhost:18445",
            "onetry",
            _out=sys.stdout,
            _err=sys.stdout,
        )
        # fix block count for other tests
        self.block_count -= 1

        print("Wait for the two nodes to sync...")
        last_block = self.wait_for_node_to_sync()

        print("Reorg test successful")

    def test_electrs(self):
        self.start_and_wait_second_node()

        # create a new address on the Bitcoin node not connected to Counterparty server
        self.bitcoin_cli_2("createwallet", WALLET_NAME)
        new_address = self.bitcoin_wallet_2("getnewaddress", WALLET_NAME, "bech32").strip()
        # send 0.1 BTC to the new address
        self.bitcoin_wallet("sendtoaddress", new_address, 0.1)
        self.mine_blocks(1)
        self.wait_for_counterparty_server()

        # try to compose a transaction with the new address
        transaction = self.compose(
            new_address,
            "send",
            {
                "destination": self.addresses[0],
                "quantity": 1000,
                "asset": "BTC",
            },
        )
        assert "Electrs error" in transaction["error"]
        assert "Failed to establish a new connection" in transaction["error"]

        # start electrs
        self.start_electrs()
        self.wait_for_electrs()

        # retry to compose a transaction with the new address
        transaction = self.compose(
            new_address,
            "send",
            {
                "destination": self.addresses[0],
                "quantity": 1000,
                "asset": "BTC",
            },
        )
        assert "error" not in transaction
        assert transaction["result"]["rawtransaction"].startswith("02")

        print("Electrs test successful")

    def test_invalid_detach(self):
        print("Test invalid detach...")

        balances = self.api_call("assets/UTXOASSET/balances")["result"]
        utxoasset_balances = []
        utxoasset_addresses = []
        print(balances)
        utxo = None
        test_address = None
        for balance in balances:
            if balance["utxo"] and balance["quantity"] > 0:
                if not utxo:
                    utxo = balance["utxo"]
                    test_address = balance["utxo_address"]
                utxoasset_balances.append(balance["utxo"])
                utxoasset_addresses.append(balance["utxo_address"])
        assert utxo
        txid, vout = utxo.split(":")

        data = self.send_transaction(
            utxo,
            "detach",
            {
                "destination": test_address,
                "exact_fee": 1,
                "inputs_set": self.get_inputs_set(test_address),
            },
            return_only_data=True,
        )

        # select an input without balance
        list_unspent = json.loads(
            self.bitcoin_cli("listunspent", 0, 9999999, json.dumps([test_address])).strip()
        )
        for utxo in list_unspent:
            if (
                utxo["txid"] != txid
                or utxo["vout"] != int(vout)
                and f"{txid}:{vout}" not in utxoasset_balances
            ):
                selected_utxo = utxo
                break

        data = binascii.unhexlify(data)
        key = binascii.unhexlify(selected_utxo["txid"])
        data = ARC4(key).encrypt(data)
        data = binascii.hexlify(data).decode("utf-8")

        # correct input should be:
        # inputs = json.dumps([{"txid": txid, "vout": int(vout)}])
        # but we use the wrong input to test the invalid detach
        inputs = json.dumps([selected_utxo])
        outputs = json.dumps({test_address: 200 / 10e8, "data": data})

        raw_transaction = self.bitcoin_cli("createrawtransaction", inputs, outputs).strip()
        signed_transaction_json = self.bitcoin_wallet(
            "signrawtransactionwithwallet", raw_transaction
        ).strip()
        signed_transaction = json.loads(signed_transaction_json)["hex"]

        retry = 0
        while True:
            try:
                tx_hash, _block_hash, _block_time = self.broadcast_transaction(signed_transaction)
                break
            except sh.ErrorReturnCode_25:
                retry += 1
                assert retry < 6
                # print(str(e))
                print("Sleeping for 5 seconds and retrying...")
                time.sleep(5)

        # utxo balance should be greater than 0
        balances = self.api_call(f"addresses/{test_address}/balances/UTXOASSET")["result"]
        for balance in balances:
            if balance["utxo"]:
                assert balance["quantity"] > 0
                break

        # we should not have a new event
        events = self.api_call(f"transactions/{tx_hash}/events?event_name=DETACH_FROM_UTXO")[
            "result"
        ]
        print(events)
        assert len(events) == 0

        print("Invalid detach test successful")

        # let's try to detach assets with an UTXO move to a single OP_RETURN output
        utxo = utxoasset_balances[0]
        utxo_address = utxoasset_addresses[0]
        txid, vout = utxo.split(":")

        inputs = json.dumps([{"txid": txid, "vout": int(vout)}])
        outputs = json.dumps({"data": 50 * "00"})

        raw_transaction = self.bitcoin_cli("createrawtransaction", inputs, outputs).strip()
        signed_transaction_json = self.bitcoin_wallet(
            "signrawtransactionwithwallet", raw_transaction
        ).strip()
        signed_transaction = json.loads(signed_transaction_json)["hex"]

        retry = 0
        while True:
            try:
                tx_hash, _block_hash, _block_time = self.broadcast_transaction(signed_transaction)
                break
            except sh.ErrorReturnCode_25:
                retry += 1
                assert retry < 6
                # print(str(e))
                print("Sleeping for 5 seconds and retrying...")
                time.sleep(5)

        events = self.api_call(f"transactions/{tx_hash}/events?event_name=DETACH_FROM_UTXO")[
            "result"
        ]
        assert len(events) == 1
        assert events[0]["params"]["source"] == utxo
        assert events[0]["params"]["destination"] == utxo_address

        print("Detach with a single OP_RETURN output transaction test successful")

    def test_transaction_chaining(self):
        print("Test transaction chaining...")
        # source address
        source_address = self.addresses[0]
        address_info = json.loads(self.bitcoin_wallet("getaddressinfo", source_address).strip())
        pubkey_source = address_info["scriptPubKey"]

        # new empty address
        new_address = self.bitcoin_wallet("getnewaddress", WALLET_NAME, "bech32").strip()
        address_info = json.loads(self.bitcoin_wallet("getaddressinfo", new_address).strip())
        pubkey_new_address = address_info["scriptPubKey"]

        #####   Send XCP to new address #####

        # prepare transaction
        # send 100 sats XCP to a new empty address
        api_call_url = f"addresses/{source_address}/compose/send?destination={new_address}&quantity=100&asset=XCP"
        api_call_url += "&inputs_set=" + self.get_inputs_set(source_address)
        result = self.api_call(api_call_url)
        raw_transaction_1 = result["result"]["rawtransaction"]

        # sign transaction
        signed_transaction_1 = json.loads(
            self.bitcoin_wallet("signrawtransactionwithwallet", raw_transaction_1).strip()
        )["hex"]

        # get utxo info from the transaction
        decoded_transaction_1 = json.loads(
            self.bitcoin_cli("decoderawtransaction", signed_transaction_1).strip()
        )
        txid_1 = decoded_transaction_1["txid"]
        vout_1 = len(decoded_transaction_1["vout"]) - 1  # last vout is the change
        value_1 = int(decoded_transaction_1["vout"][vout_1]["value"] * 1e8)

        #####   Send BTC to new address using the change from the previous transaction #####

        # prepare transaction
        # send 10000 sats to the new address
        # we are using the last output of the previous transaction as input
        # this output is the change from the previous transaction
        api_call_url = f"addresses/{source_address}/compose/send?destination={new_address}&quantity=10000&asset=BTC"
        api_call_url += f"&inputs_set={txid_1}:{vout_1}:{value_1}:{pubkey_source}"
        api_call_url += "&disable_utxo_locks=true"
        api_call_url += "&validate=false"
        api_call_url += "&exact_fee=1000"
        result = self.api_call(api_call_url)
        raw_transaction_2 = result["result"]["rawtransaction"]

        # sign transaction
        prevtx = [
            {"txid": txid_1, "vout": vout_1, "scriptPubKey": pubkey_source, "amount": value_1 / 1e8}
        ]
        prevtx = json.dumps(prevtx)
        signed_transaction_2_json = json.loads(
            self.bitcoin_wallet("signrawtransactionwithwallet", raw_transaction_2, prevtx).strip()
        )
        signed_transaction_2 = signed_transaction_2_json["hex"]

        # get utxo info from the second transaction
        decoded_transaction_2 = json.loads(
            self.bitcoin_cli("decoderawtransaction", signed_transaction_2).strip()
        )
        txid_2 = decoded_transaction_2["txid"]
        vout_2 = 0  # first vout is the 10000 sats from the previous transaction
        value_2 = int(decoded_transaction_2["vout"][vout_2]["value"] * 1e8)
        assert value_2 == 10000

        #####   Create a dispenser using the BTC received from the second transactions #####

        # prepare transaction
        # we are using the first output of the previous transaction as input
        # this output must contain the 10000 sats
        api_call_url = f"addresses/{new_address}/compose/dispenser?"
        api_call_url += "asset=XCP&give_quantity=1&escrow_quantity=2&mainchainrate=1&status=0"
        api_call_url += f"&inputs_set={txid_2}:0:{value_2}:{pubkey_new_address}"
        api_call_url += "&exact_fee=1000"
        api_call_url += "&disable_utxo_locks=true"
        api_call_url += "&validate=false"
        result = self.api_call(api_call_url)
        raw_transaction_3 = result["result"]["rawtransaction"]

        # sign transaction
        prevtx = [
            {"txid": txid_2, "vout": 0, "scriptPubKey": pubkey_new_address, "amount": value_2 / 1e8}
        ]
        prevtx = json.dumps(prevtx)
        signed_transaction_3 = json.loads(
            self.bitcoin_wallet("signrawtransactionwithwallet", raw_transaction_3, prevtx).strip()
        )["hex"]

        # broadcast the three transactions
        tx_hash, block_hash, block_time = self.broadcast_transaction(
            signed_transaction_1, no_confirmation=True, dont_wait_mempool=True
        )
        print(f"Transaction 1 sent: {tx_hash}")
        tx_hash, block_hash, block_time = self.broadcast_transaction(
            signed_transaction_2, no_confirmation=True, dont_wait_mempool=True
        )
        print(f"Transaction 2 sent: {tx_hash}")
        tx_hash, block_hash, block_time = self.broadcast_transaction(
            signed_transaction_3, no_confirmation=True, dont_wait_mempool=True
        )
        print(f"Transaction 3 sent: {tx_hash}")

        # mine a block
        self.mine_blocks(1)
        self.wait_for_counterparty_server()
        # wait for event to be parsed
        # TODO:find a way to check the event is parsed
        time.sleep(2)

        # check the dispenser is created
        dispensers = self.api_call(f"addresses/{new_address}/dispensers")["result"]
        assert len(dispensers) == 1
        assert dispensers[0]["give_quantity"] == 1
        assert dispensers[0]["escrow_quantity"] == 2
        assert dispensers[0]["status"] == 0
        assert dispensers[0]["asset"] == "XCP"

        print("Dispenser created")

    def test_asset_conservation(self):
        self.test_command("check-db")

    def test_fee_calculation(self):
        unsigned_tx = self.compose(
            self.addresses[0],
            "send",
            {
                "destination": self.addresses[1],
                "quantity": 10,
                "asset": "XCP",
                "sat_per_vbyte": 1,
                "verbose": True,
                "validate": False,
            },
        )["result"]
        print("Unsigned transaction 1: ", unsigned_tx)

        signed_tx = json.loads(
            self.bitcoin_wallet(
                "signrawtransactionwithwallet", unsigned_tx["rawtransaction"]
            ).strip()
        )["hex"]
        transaction2 = Transaction.from_raw(signed_tx)

        print("Fees: ", unsigned_tx["btc_fee"])
        print("VSize After signing: ", transaction2.get_vsize())
        assert unsigned_tx["btc_fee"] == transaction2.get_vsize()

        unsigned_tx = self.compose(
            self.addresses[0],
            "send",
            {
                "destination": self.addresses[1],
                "quantity": 10,
                "asset": "XCP",
                "sat_per_vbyte": 2.31,
                "verbose": True,
                "encoding": "multisig",
                "validate": False,
            },
        )["result"]
        print("Unsigned transaction 2: ", unsigned_tx)

        signed_tx = json.loads(
            self.bitcoin_wallet(
                "signrawtransactionwithwallet", unsigned_tx["rawtransaction"]
            ).strip()
        )["hex"]
        transaction3 = Transaction.from_raw(signed_tx)

        print("Fees: ", unsigned_tx["btc_fee"])
        print("VSize After signing: ", transaction3.get_vsize())
        print("Estimate Size After signing: ", unsigned_tx["signed_tx_estimated_size"])
        size = max(
            unsigned_tx["signed_tx_estimated_size"]["vsize"],
            unsigned_tx["signed_tx_estimated_size"]["adjusted_vsize"],
        )
        assert unsigned_tx["btc_fee"] == int(size * 2.31)

        legacy_address = self.bitcoin_wallet("getnewaddress", WALLET_NAME, "legacy").strip()
        self.send_transaction(
            self.addresses[0],
            "send",
            {
                "destination": legacy_address,
                "quantity": 10,
                "asset": "XCP",
                "validate": False,
            },
        )
        self.bitcoin_wallet("sendtoaddress", legacy_address, 0.1)
        self.mine_blocks(1)

        unsigned_tx = self.compose(
            legacy_address,
            "send",
            {
                "destination": self.addresses[1],
                "quantity": 5,
                "asset": "XCP",
                "fee_per_kb": 3 * 1024,  # try deprecated parameter
                "verbose": True,
                "validate": False,
            },
        )["result"]
        print("Unsigned transaction 3: ", unsigned_tx)

        signed_tx = json.loads(
            self.bitcoin_wallet(
                "signrawtransactionwithwallet", unsigned_tx["rawtransaction"]
            ).strip()
        )["hex"]
        print("signed_tx: ", signed_tx)
        transaction4 = Transaction.from_raw(signed_tx)

        print("Fees: ", unsigned_tx["btc_fee"])
        print("VSize After signing: ", transaction4.get_vsize())
        print("Estimate Size After signing: ", unsigned_tx["signed_tx_estimated_size"])
        size = max(
            unsigned_tx["signed_tx_estimated_size"]["vsize"],
            unsigned_tx["signed_tx_estimated_size"]["adjusted_vsize"],
        )
        assert size * 3 - 3 <= unsigned_tx["btc_fee"] <= size * 3 + 3

    def test_rbf(self):
        self.start_and_wait_second_node()

        unsigned_tx = self.compose(
            self.addresses[0],
            "send",
            {
                "destination": self.addresses[1],
                "quantity": 1,
                "asset": "XCP",
                "exact_fee": 1,
                "verbose": True,
                "validate": False,
            },
        )["result"]
        transaction = Transaction.from_raw(unsigned_tx["rawtransaction"])
        raw_hexs = []
        # create 10 transactions with increasing fees
        for _i in range(10):
            transaction.outputs[1].amount -= 170
            new_raw_transaction = transaction.to_hex()
            signed_tx = json.loads(
                self.bitcoin_wallet("signrawtransactionwithwallet", new_raw_transaction).strip()
            )["hex"]
            raw_hexs.append(signed_tx)

        # check that no transaction is in the mempool
        mempool_event_count_before = self.api_call("mempool/events?event_name=TRANSACTION_PARSED")[
            "result_count"
        ]
        assert mempool_event_count_before == 0

        # broadcast the transactions to the two nodes
        tx_hahses = []
        for i, raw_hex in enumerate(raw_hexs):
            tx_hash = self.bitcoin_wallet("sendrawtransaction", raw_hex, 0).strip()
            tx_hahses.append(tx_hash)
            print(f"Transaction {i} sent: {tx_hash}")

        # check that all transactions are in the mempool
        mempool_event_count_after = self.api_call("mempool/events?event_name=TRANSACTION_PARSED")[
            "result_count"
        ]
        while mempool_event_count_after == 0:
            time.sleep(1)
            mempool_event_count_after = self.api_call(
                "mempool/events?event_name=TRANSACTION_PARSED"
            )["result_count"]
        time.sleep(10)

        print("Mempool event count: ", mempool_event_count_after)

        # only one event should be in the mempool
        assert mempool_event_count_after == 1
        # check that RBFed transactions are removed from the mempool
        for tx_hash in tx_hahses[:-1]:
            assert f"Removing transaction from mempool: {tx_hash}" in self.server_out.getvalue()
        event = self.api_call("mempool/events?event_name=TRANSACTION_PARSED")["result"][0]
        # check that the last transaction is the one in the mempool
        assert event["tx_hash"] == tx_hahses[-1]

        print("RBF test successful")


class RegtestNodeThread(threading.Thread):
    def __init__(self, wsgi_server="waitress", burn_in_one_block=True):
        threading.Thread.__init__(self)
        self.wsgi_server = wsgi_server
        self.burn_in_one_block = burn_in_one_block
        self.daemon = True
        self.node = None

    def run(self):
        self.node = RegtestNode(
            wsgi_server=self.wsgi_server, burn_in_one_block=self.burn_in_one_block
        )
        self.node.start()

    def stop(self):
        if self.node:
            self.node.stop()

    def ready(self):
        if self.node:
            return self.node.ready
        return False


def print_server_output(node, printed_line_count):
    unprinted_lines = node.server_out.getvalue().splitlines()[printed_line_count:]
    for line in unprinted_lines:
        print(line)
        printed_line_count += 1
    return printed_line_count


if __name__ == "__main__":
    try:
        node = RegtestNode(show_output=True)
        node.start()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
