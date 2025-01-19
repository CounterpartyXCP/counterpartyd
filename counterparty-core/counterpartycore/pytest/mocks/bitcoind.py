import time

from counterpartycore.lib import config
from counterpartycore.lib.api import composer
from counterpartycore.lib.ledger.currentstate import CurrentState
from counterpartycore.lib.parser import blocks, check, deserialize
from counterpartycore.lib.utils import multisig

from ..fixtures.params import DEFAULT_PARAMS


def list_unspent(source, allow_unconfirmed_inputs):
    print("list_unspent")

    construct_params = {}
    if multisig.is_multisig(source):
        signatures_required, addresses, signatures_possible = multisig.extract_array(source)
        pubkeys = [DEFAULT_PARAMS["pubkey"][addr] for addr in addresses]
        construct_params["pubkeys"] = ",".join(pubkeys)

    script_pub_key = composer.address_to_script_pub_key(source, network="testnet").to_hex()
    # deterministic txid from the source
    txid = check.dhash_string(source)

    return [
        {
            "txid": txid,
            "vout": 0,
            "amount": int(10 * config.UNIT),
            "value": int(10 * config.UNIT),
            "script_pub_key": script_pub_key,
        }
    ]


def satoshis_per_vbyte():
    return 2


def sendrawtransaction(db, rawtransaction):
    print("sendrawtransaction", rawtransaction)
    decoded_tx = deserialize.deserialize_tx(rawtransaction)
    decoded_block = {
        "block_index": CurrentState().current_block_index() + 1,
        "block_time": time.time(),
        "block_hash": "",
        "hash_prev": "",
        "bits": "",
        "transactions": [decoded_tx],
    }
    blocks.parse_new_block(db, decoded_block)
