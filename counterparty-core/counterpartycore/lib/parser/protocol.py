import json
import logging
import os

from counterpartycore.lib import config, util

logger = logging.getLogger(config.LOGGER_NAME)

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
with open(CURR_DIR + "/../../protocol_changes.json") as f:
    PROTOCOL_CHANGES = json.load(f)


def enabled(change_name, block_index=None):
    """Return True if protocol change is enabled."""
    if config.REGTEST:
        regtest_protocole_file = os.path.join(
            os.path.dirname(config.DATABASE), "regtest_disabled_changes.json"
        )
        if os.path.exists(regtest_protocole_file):
            with open(regtest_protocole_file) as f:
                regtest_disabled_changes = json.load(f)
            if change_name in regtest_disabled_changes:
                return False
        return True  # All changes are always enabled on REGTEST

    if config.TESTNET:
        index_name = "testnet_block_index"
    elif config.TESTNET4:
        index_name = "testnet4_block_index"
    else:
        index_name = "block_index"

    enable_block_index = PROTOCOL_CHANGES[change_name][index_name]

    if not block_index:
        block_index = util.CURRENT_BLOCK_INDEX

    if block_index >= enable_block_index:
        return True
    else:
        return False


def get_change_block_index(change_name):
    if config.REGTEST:
        return 0

    if config.TESTNET:
        index_name = "testnet_block_index"
    else:
        index_name = "block_index"

    return PROTOCOL_CHANGES[change_name][index_name]


def get_value_by_block_index(change_name, block_index=None):
    if not block_index:
        block_index = util.CURRENT_BLOCK_INDEX
    if block_index is None or block_index == 0:
        block_index = 9999999  # Set to a high number to get the highest value

    max_block_index = -1

    if config.REGTEST:
        for key in PROTOCOL_CHANGES[change_name]["testnet"]:
            if int(key) > int(max_block_index):
                max_block_index = key
        return PROTOCOL_CHANGES[change_name]["testnet"][max_block_index]["value"]

    if config.TESTNET:
        index_name = "testnet"
    elif config.TESTNET4:
        index_name = "testnet4"
    else:
        index_name = "mainnet"

    for key in PROTOCOL_CHANGES[change_name][index_name]:
        if int(key) > int(max_block_index) and block_index >= int(key):
            max_block_index = key

    return PROTOCOL_CHANGES[change_name][index_name][max_block_index]["value"]


def is_test_network():
    return config.TESTNET or config.TESTNET4 or config.REGTEST


def after_block_or_test_network(tx_block_index, target_block_index):
    return tx_block_index >= target_block_index or is_test_network()
