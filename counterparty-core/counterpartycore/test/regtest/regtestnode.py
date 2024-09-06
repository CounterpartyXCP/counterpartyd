#!/usr/bin/env python3

import json
import os
import sys
import threading
import time
import urllib.parse
from io import StringIO

import sh

WALLET_NAME = "xcpwallet"


class ServerNotReady(Exception):
    pass


class ComposeError(Exception):
    pass


class RegtestNode:
    def __init__(self, datadir="regtestnode"):
        self.datadir = datadir
        self.bitcoin_cli = sh.bitcoin_cli.bake(
            "-regtest",
            "-rpcuser=rpc",
            "-rpcpassword=rpc",
            "-rpcconnect=localhost",
            f"-datadir={self.datadir}",
        )
        self.bitcoin_wallet = self.bitcoin_cli.bake(f"-rpcwallet={WALLET_NAME}")
        self.bitcoind_process = None
        self.addresses = []
        self.block_count = 0
        self.ready = False

    def api_call(self, url):
        return json.loads(sh.curl(f"http://localhost:24000/v2/{url}").strip())

    def wait_for_bitcoind(self):
        while True:
            try:
                self.bitcoin_cli("getblockchaininfo")
                break
            except sh.ErrorReturnCode:
                print("Waiting for bitcoind to start...")
                time.sleep(1)

    def send_transaction(self, source, tx_name, params, retry=0, return_only_data=False):
        self.wait_for_counterparty_server()
        if return_only_data:
            params["return_only_data"] = 1
        query_string = urllib.parse.urlencode(params)
        if tx_name in ["detach", "movetoutxo"]:
            compose_url = f"utxos/{source}/compose/{tx_name}?{query_string}"
        elif tx_name == "multiple":
            compose_url = f"compose?{query_string}"
        else:
            compose_url = f"addresses/{source}/compose/{tx_name}?{query_string}"
        result = self.api_call(compose_url)
        # print(result)
        if "error" in result:
            raise ComposeError(result["error"])
        raw_transaction = result["result"]["rawtransaction"]
        if return_only_data:
            return raw_transaction
        # print(f"Raw transaction: {tx_name} {params} ({raw_transaction})")
        signed_transaction_json = self.bitcoin_wallet(
            "signrawtransactionwithwallet", raw_transaction
        ).strip()
        signed_transaction = json.loads(signed_transaction_json)["hex"]
        try:
            tx_hash = self.bitcoin_wallet("sendrawtransaction", signed_transaction).strip()
        except sh.ErrorReturnCode_25 as e:
            if retry >= 2:
                raise e
            print("Error: bad-txns-inputs-missingorspent")
            print("Sleeping for 5 seconds and retrying...")
            time.sleep(5)
            return self.send_transaction(source, tx_name, params, retry=retry + 1)
        block_hash, block_time = self.mine_blocks(1)
        self.wait_for_counterparty_server()
        print(f"Transaction sent: {tx_name} {params} ({tx_hash})")
        return tx_hash, block_hash, block_time

    def wait_for_counterparty_server(self, block=None):
        while True:
            try:
                result = self.api_call("")
                if result and "result" in result and result["result"]["server_ready"]:
                    current_block = result["result"]["counterparty_height"]
                    target_block = block or self.block_count
                    if current_block < target_block:
                        print(f"Waiting for block {current_block} < {target_block}")
                        raise ServerNotReady
                    else:
                        print("Server ready")
                        return
                elif result and "result" in result:
                    print(
                        f"Server not ready: {result['result']['counterparty_height']} < {result['result']['backend_height']}"
                    )
                    raise ServerNotReady
                raise json.JSONDecodeError("Invalid response", "", 0)
            except (sh.ErrorReturnCode, ServerNotReady, json.JSONDecodeError) as e:
                if not isinstance(e, ServerNotReady):
                    print("Waiting for counterparty...")
                time.sleep(1)

    def wait_for_counterparty_follower(self):
        while True:
            if "Starting blockchain watcher..." in self.server_out.getvalue():
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
            address = self.bitcoin_wallet("getnewaddress", "", "bech32").strip()
            print(f"Address {i}: {address}")
            self.addresses.append(address)
            self.mine_blocks(1, address)
        self.addresses.sort()
        self.mine_blocks(101)

    def generate_xcp(self):
        print("Generating XCP...")
        for address in self.addresses:
            self.send_transaction(address, "burn", {"quantity": 50000000})

    def start(self):
        if os.path.exists(self.datadir):
            sh.rm("-rf", self.datadir)
        sh.mkdir(self.datadir)

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
            f"-datadir={self.datadir}",
            _bg=True,
            _out=sys.stdout,
        )

        self.wait_for_bitcoind()

        self.bitcoin_cli(
            "createwallet",
            WALLET_NAME,
        )
        print("Wallet created")

        self.generate_addresses_with_btc()

        # print(self.bitcoin_cli("listreceivedbyaddress"))

        self.addrindexrs_process = sh.addrindexrs(
            "--network=regtest",
            "-vvvv",
            "--cookie=rpc:rpc",
            f"--db-dir={self.datadir}",
            f"--daemon-dir={self.datadir}",
            "--daemon-rpc-port=18443",
            "--jsonrpc-import",
            _bg=True,
            # _out=sys.stdout,
            # _err=sys.stdout,
        )

        self.server_out = StringIO()
        self.counterparty_server_process = sh.counterparty_server(
            "--regtest",
            f"--database-file={self.datadir}/counterparty.db",
            "-vv",
            "start",
            _bg=True,
            _out=self.server_out,
            _err_to_out=True,
        )
        self.wait_for_counterparty_follower()

        self.generate_xcp()

        balances = self.api_call("assets/XCP/balances")["result"]
        for balance in balances:
            print(f"{balance['address']}: {balance['quantity'] / 1e8} XCP")

        print("Regtest node ready")
        self.ready = True

        self.counterparty_server_process.wait()

    def stop(self):
        print("Stopping...")
        try:
            self.bitcoin_cli("stop", _out=sys.stdout)
        except sh.ErrorReturnCode:
            pass
        try:
            self.addrindexrs_process.terminate()  # noqa
        except Exception as e:
            print(e)
            pass
        try:
            self.counterparty_server_process.terminate()  # noqa
        except Exception as e:
            print(e)
            pass


class RegtestNodeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.node = None

    def run(self):
        self.node = RegtestNode()
        self.node.start()

    def stop(self):
        if self.node:
            self.node.stop()

    def ready(self):
        if self.node:
            return self.node.ready
        return False


if __name__ == "__main__":
    try:
        node = RegtestNode()
        node.start()
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
