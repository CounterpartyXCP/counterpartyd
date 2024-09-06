#!/usr/bin/env python3

import difflib
import json
import time

from regtestnode import ComposeError, RegtestNodeThread
from scenarios import (
    scenario_1_fairminter,
    scenario_2_fairminter,
    scenario_3_dispenser,
    scenario_4_utxo,
    scenario_5_chaining,
    scenario_6_presigned,
)
from termcolor import colored

SCENARIOS = []
SCENARIOS += scenario_1_fairminter.SCENARIO
SCENARIOS += scenario_2_fairminter.SCENARIO
SCENARIOS += scenario_3_dispenser.SCENARIO
SCENARIOS += scenario_4_utxo.SCENARIO
SCENARIOS += scenario_5_chaining.SCENARIO
# SCENARIOS += scenario_6_presigned.SCENARIO
SCENARIOS = scenario_6_presigned.SCENARIO


def compare_strings(string1, string2):
    """Compare strings diff-style."""
    diff = list(difflib.unified_diff(string1.splitlines(1), string2.splitlines(1), n=0))
    if len(diff):
        print("\nDifferences:")
        print("\n".join(diff))
    return len(diff)


def prepare_item(item, node, context):
    for i, address in enumerate(node.addresses):
        item["source"] = item["source"].replace(f"$ADDRESS_{i+1}", address)
        for key in item["params"]:
            if isinstance(item["params"][key], str):
                item["params"][key] = item["params"][key].replace(f"$ADDRESS_{i+1}", address)
    for name, value in context.items():
        item["source"] = item["source"].replace(f"${name}", value)
        for key in item["params"]:
            if isinstance(item["params"][key], str):
                item["params"][key] = item["params"][key].replace(f"${name}", value)
    return item


def run_item(node, item, context):
    print(f"Running: {item['title']}")
    if item["transaction"] == "mine_blocks":
        block_hash, block_time = node.mine_blocks(item["params"]["blocks"])
        tx_hash = "null"
        node.wait_for_counterparty_server()
    elif item["transaction"].startswith("presigned"):
        item["transaction"] = item["transaction"].replace("presigned_", "")
        item = prepare_item(item, node, context)
        data = node.send_transaction(
            item["source"], item["transaction"], item["params"], return_only_data=True
        )
        print(data)
    else:
        item = prepare_item(item, node, context)
        try:
            tx_hash, block_hash, block_time = node.send_transaction(
                item["source"], item["transaction"], item["params"]
            )
        except ComposeError as e:
            if "expected_error" in item:
                try:
                    assert (str(item["expected_error"]),) == e.args
                    print(f"{item['title']}: " + colored("Success", "green"))
                except AssertionError:
                    print(colored(f"Failed: {item['title']}", "red"))
                    print(f"Expected: {item['expected_error']}")
                    print(f"Got: {str(e)}")
                    # raise e
            else:
                raise e

    if "controls" in item:
        for control in item["controls"]:
            control_url = control["url"].replace("$TX_HASH", tx_hash)
            for i, address in enumerate(node.addresses):
                control_url = control_url.replace(f"$ADDRESS_{i+1}", address)
            result = node.api_call(control_url)
            try:
                expected_result = control["result"]
                expected_result = (
                    json.dumps(expected_result)
                    .replace("$TX_HASH", tx_hash)
                    .replace("$BLOCK_HASH", block_hash)
                    .replace('"$BLOCK_TIME"', str(block_time))
                )
                for i, address in enumerate(node.addresses):
                    expected_result = expected_result.replace(f"$ADDRESS_{i+1}", address)
                for name, value in context.items():
                    expected_result = expected_result.replace(f"${name}", value)
                expected_result = json.loads(expected_result)

                assert result["result"] == expected_result

                print(f"{item['title']}: " + colored("Success", "green"))
            except AssertionError:
                print(colored(f"Failed: {item['title']}", "red"))
                expected_result_str = json.dumps(expected_result, indent=4, sort_keys=True)
                got_result_str = json.dumps(result["result"], indent=4, sort_keys=True)
                print(f"Expected: {expected_result_str}")
                print(f"Got: {got_result_str}")
                compare_strings(expected_result_str, got_result_str)
                # raise e

    for name, value in item.get("set_variables", {}).items():
        context[name] = value.replace("$TX_HASH", tx_hash).replace("$BLOCK_HASH", block_hash)

    return context


def run_scenarios():
    try:
        regtest_node_thread = RegtestNodeThread()
        regtest_node_thread.start()

        while not regtest_node_thread.ready():
            time.sleep(1)

        context = {}

        for item in SCENARIOS:
            context = run_item(regtest_node_thread.node, item, context)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(regtest_node_thread.node.server_out.getvalue())
        raise e
    finally:
        print(regtest_node_thread.node.server_out.getvalue())
        regtest_node_thread.stop()


if __name__ == "__main__":
    run_scenarios()
