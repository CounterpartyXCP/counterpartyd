"""
This structure holds the unit test vectors. They are used to generate test cases in conftest.py.
The results are computed using check_outputs in util_test.py.
The function supports three types of output checks:
- Return values - 'out'
- Errors raised - 'error'
- Database changes - 'records'
- PRAGMA changes - 'pragma'
"""

import binascii

import bitcoin as bitcoinlib

from counterpartycore.lib import config, exceptions, script  # noqa: F401
from counterpartycore.lib.api.api_v1 import APIError
from counterpartycore.lib.messages import issuance
from counterpartycore.lib.util import RPCError

from .contract_vectors.attach import ATTACH_VECTOR
from .contract_vectors.composer import COMPOSER_VECTOR
from .contract_vectors.detach import DETACH_VECTOR
from .contract_vectors.dispenser import DISPENSER_VECTOR
from .contract_vectors.fairmint import FAIRMINT_VECTOR
from .contract_vectors.fairminter import FAIRMINTER_VECTOR
from .contract_vectors.gas import GAS_VECTOR
from .contract_vectors.gettxinfo import GETTXINFO_VECTOR
from .contract_vectors.ledger import LEDGER_VECTOR
from .contract_vectors.move import MOVE_VECTOR
from .contract_vectors.send import SEND_VECTOR
from .contract_vectors.utxo import UTXO_VECTOR
from .params import (
    ADDR,
    MULTISIGADDR,
    P2SH_ADDR,
    P2WPKH_ADDR,
    SHORT_ADDR_BYTES,
)
from .params import (
    DEFAULT_PARAMS as DP,
)

# UNITTEST_VECTOR = COMPOSER_VECTOR

UNITTEST_VECTOR = (
    FAIRMINTER_VECTOR
    | FAIRMINT_VECTOR
    | LEDGER_VECTOR
    | UTXO_VECTOR
    | SEND_VECTOR
    | DISPENSER_VECTOR
    | GAS_VECTOR
    | COMPOSER_VECTOR
    | GETTXINFO_VECTOR
    | MOVE_VECTOR
    | ATTACH_VECTOR
    | DETACH_VECTOR
    | {
        "bet": {
            "validate": [
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        0,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": ([], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        0,
                        1488000100,
                        2**32,
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": ([], 15120),
                },
                {
                    "in": (
                        ADDR[0],
                        ADDR[1],
                        3,
                        1388001000,
                        DP["small"],
                        DP["small"],
                        0.0,
                        5040,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["feed doesn’t exist"], 5040),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        -1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["unknown bet type"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        2,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["leverage used with Equal or NotEqual"], 15120),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        ADDR[0],
                        0,
                        1488000100,
                        2**32,
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": ([], 15120),
                },
                {
                    "in": (
                        ADDR[0],
                        P2SH_ADDR[0],
                        0,
                        1488000100,
                        2**32,
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": ([], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        3,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        5000,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (
                        ["leverage used with Equal or NotEqual", "leverage level too low"],
                        5000,
                    ),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        312350,
                    ),
                    "out": (["CFDs temporarily disabled"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        1.1 * DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["wager_quantity must be in satoshis"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        1.1 * DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["counterwager_quantity must be in satoshis"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        1.1 * DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["expiration must be expressed as an integer block delta"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        -1 * DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["non‐positive wager"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        -1 * DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["non‐positive counterwager"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[2],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["feed is locked"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        -1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["deadline in that feed’s past", "negative deadline"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        -1 * DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["negative expiration"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        1.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["CFDs have no target value"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        2,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        -1.0,
                        5040,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["negative target value"], 5040),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        8095,
                        DP["default_block_index"],
                    ),
                    "out": (["expiration overflow"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        2**63,
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        2**63,
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        2**63,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow", "unknown bet type"], 15120),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        2**63,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow"], 2**63),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        1,
                        2**63,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow"], 15120),
                },
            ],
            "compose": [
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        0,
                        1488000100,
                        2**32,
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                    ),
                    "error": (exceptions.ComposeError, "insufficient funds"),
                },
                {
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        0,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                    ),
                    "out": (
                        ADDR[1],
                        [(ADDR[0], None)],
                        b"\x00\x00\x00(\x00\x00X\xb1\x14d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    ),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        ADDR[0],
                        0,
                        1488000100,
                        DP["small"],
                        DP["small"],
                        0.0,
                        15120,
                        DP["expiration"],
                    ),
                    "out": (
                        P2SH_ADDR[0],
                        [(ADDR[0], None)],
                        b"\x00\x00\x00(\x00\x00X\xb1\x14d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    ),
                },
            ],
            "parse": [
                {
                    "in": (
                        {
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "block_time": 310501000,
                            "data": b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "btc_amount": 5430,
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "a0ed83b170344b996bdd71799dd774ab10f5410f8572079a292f681d36ebc42c",
                            "fee": 10000,
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        },
                    ),
                    "out": None,
                },
                {
                    "comment": "1",
                    "in": (
                        {
                            "fee": 10000,
                            "tx_hash": "72a62abedd38d5f667150929c24dc1d7465dd81ab1502974814d20c1f65d871f",
                            "data": b"\x00\x00\x00(\x00\x00X\xb1\x14\x00\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\xb0\x00\x00\x00\n",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_index": DP["default_block_index"],
                            "btc_amount": 5430,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_time": 310501000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                        },
                    ),
                    "records": [
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 0,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 0,
                                "counterwager_remaining": 0,
                                "deadline": 1488000000,
                                "expiration": 10,
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: non‐positive counterwager",
                                "target_value": 0.0,
                                "tx_hash": "72a62abedd38d5f667150929c24dc1d7465dd81ab1502974814d20c1f65d871f",
                                "tx_index": DP["default_tx_index"],
                                "wager_quantity": 100000000,
                                "wager_remaining": 100000000,
                            },
                        }
                    ],
                },
                {
                    "comment": "P2SH",
                    "in": (
                        {
                            "fee": 10000,
                            "tx_hash": "72a62abedd38d5f667150929c24dc1d7465dd81ab1502974814d20c1f65d871f",
                            "data": b"\x00\x00\x00(\x00\x00X\xb1\x14\x00\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\xb0\x00\x00\x00\n",
                            "source": P2SH_ADDR[0],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 5430,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "destination": P2SH_ADDR[0],
                            "block_time": 310501000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                        },
                    ),
                    "records": [
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 0,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 0,
                                "counterwager_remaining": 0,
                                "deadline": 1488000000,
                                "expiration": 10,
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_fraction_int": 5000000,
                                "feed_address": P2SH_ADDR[0],
                                "leverage": 5040,
                                "source": P2SH_ADDR[0],
                                "status": "invalid: non‐positive counterwager",
                                "target_value": 0.0,
                                "tx_hash": "72a62abedd38d5f667150929c24dc1d7465dd81ab1502974814d20c1f65d871f",
                                "tx_index": DP["default_tx_index"],
                                "wager_quantity": 100000000,
                                "wager_remaining": 100000000,
                            },
                        }
                    ],
                },
                {
                    "in": (
                        {
                            "supported": 1,
                            "data": b"\x00\x00\x00(\x00\x02R\xbb3\xc8\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\xb0\x00\x00\x03\xe8",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "btc_amount": 5430,
                            "block_index": DP["default_block_index"],
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "30b9ca8488a931dffa1d8d3ac8f1c51360a29cedb7c703840becc8a95f81188c",
                            "block_time": 310501000,
                            "fee": 10000,
                        },
                    ),
                    "records": [
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 2,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 10,
                                "counterwager_remaining": 0,
                                "deadline": 1388000200,
                                "expiration": 1000,
                                "expire_index": DP["default_block_index"] + 1000,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "filled",
                                "target_value": 0.0,
                                "tx_hash": "30b9ca8488a931dffa1d8d3ac8f1c51360a29cedb7c703840becc8a95f81188c",
                                "tx_index": DP["default_tx_index"],
                                "wager_quantity": 10,
                                "wager_remaining": 0,
                            },
                        },
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 3,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 10,
                                "counterwager_remaining": 0,
                                "deadline": 1388000200,
                                "expiration": 1000,
                                "expire_index": 311101,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "filled",
                                "target_value": 0.0,
                                "tx_hash": "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                                "tx_index": 102,
                                "wager_quantity": 10,
                                "wager_remaining": 0,
                            },
                        },
                    ],
                },
            ],
            "get_fee_fraction": [
                {"in": (ADDR[1],), "out": (0)},
                {"in": (P2SH_ADDR[0],), "out": (0.05)},
                {"in": (ADDR[0],), "out": (0.05)},
                {"in": (ADDR[2],), "out": (0)},
            ],
            # TODO: Test match by calling parse. Add all skipping modes
            "match": [
                {"in": ({"tx_index": 99999999, "tx_hash": "fakehash"},), "out": None},
                {
                    "in": (
                        {
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "block_time": 310501000,
                            "data": b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "btc_amount": 5430,
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "fee": 10000,
                            "tx_hash": "a0ed83b170344b996bdd71799dd774ab10f5410f8572079a292f681d36ebc42c",
                            "tx_index": DP["default_tx_index"],
                        },
                    ),
                    "out": None,
                },
            ],
            # Testing expiration of normal bets is impossible - either the bet is expired automatically with expiry < DP['default_block_index'] - 1 or
            # with expire > DP['default_block_index'] - 1 insert fails with FOREIGN KEY error on block_index (which doesn't exist). With expiry DP['default_block_index'] - 1 nothing happens.
            # Testing bet_match expirations is impossible too, since if you add a bet_match with 'pending' status to the fixtures, it raises a ConsensusError in blocks.parse_block.
            # 'expire': [{
            #     'in': (DP['default_block_index'] - 1, 5388000200,),
            #     'records': [
            #         {'table': 'bet_match_expirations', 'values': {
            #             'bet_match_id': '94c900515ecf53680e98d51216c520ccb6b91a72d5aff7f62665d6328d4db832_ee5ea2ce1a423157bbb1edbabcadf2dc3adcd328d17c52c44f63dbda835f9125',
            #             'block_index': DP['default_block_index'] - 1,
            #             'tx0_address': 'mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc',
            #             'tx1_address': 'mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns',
            #         }}
            #     ]
            # }],
            "cancel_bet": [
                {
                    "in": (
                        {
                            "bet_type": 0,
                            "block_index": 310703,
                            "counterwager_quantity": 9,
                            "counterwager_remaining": 0,
                            "deadline": 1388000001,
                            "expiration": 100,
                            "expire_index": 310120,
                            "fee_fraction_int": 5000000,
                            "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "leverage": 5040,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "status": "filled",
                            "target_value": 0.0,
                            "tx_hash": "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                            "tx_index": 21,
                            "wager_quantity": 9,
                            "wager_remaining": 0,
                        },
                        "filled",
                        DP["default_block_index"],
                        0,
                    ),
                    "records": [
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 0,
                                "block_index": 310703,
                                "counterwager_quantity": 9,
                                "counterwager_remaining": 0,
                                "deadline": 1388000001,
                                "expiration": 100,
                                "expire_index": 310120,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "filled",
                                "target_value": 0.0,
                                "tx_hash": "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                                "tx_index": 21,
                                "wager_quantity": 9,
                                "wager_remaining": 0,
                            },
                        }
                    ],
                }
            ],
            "cancel_bet_match": [
                {
                    "in": (
                        {
                            "tx0_block_index": 310019,
                            "backward_quantity": 9,
                            "initial_value": 1,
                            "tx1_expiration": 100,
                            "id": "4a37e1f643b66093c802add87498ca3b322b422ac85a461bf2eb9a5a899dde4e_6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                            "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "status": "settled",
                            "leverage": 5040,
                            "target_value": 0.0,
                            "fee_fraction_int": 5000000,
                            "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "deadline": 1388000001,
                            "tx1_bet_type": 0,
                            "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx0_index": 20,
                            "tx1_hash": "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                            "tx0_hash": "4a37e1f643b66093c802add87498ca3b322b422ac85a461bf2eb9a5a899dde4e",
                            "block_index": 310020,
                            "forward_quantity": 9,
                            "match_expire_index": 310119,
                            "tx1_block_index": 310020,
                            "tx0_expiration": 100,
                            "tx1_index": 21,
                            "tx0_bet_type": 1,
                        },
                        "filled",
                        DP["default_block_index"],
                        0,
                    ),
                    "records": [
                        {
                            "table": "bet_matches",
                            "values": {
                                "backward_quantity": 9,
                                "block_index": DP["default_block_index"] - 1,
                                "deadline": 1388000001,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "forward_quantity": 9,
                                "id": "4a37e1f643b66093c802add87498ca3b322b422ac85a461bf2eb9a5a899dde4e_6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                                "initial_value": 1,
                                "leverage": 5040,
                                "match_expire_index": 310119,
                                "status": "filled",
                                "target_value": 0.0,
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_bet_type": 1,
                                "tx0_block_index": 310019,
                                "tx0_expiration": 100,
                                "tx0_hash": "4a37e1f643b66093c802add87498ca3b322b422ac85a461bf2eb9a5a899dde4e",
                                "tx0_index": 20,
                                "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "tx1_bet_type": 0,
                                "tx1_block_index": 310020,
                                "tx1_expiration": 100,
                                "tx1_hash": "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                                "tx1_index": 21,
                            },
                        }
                    ],
                }
            ],
        },
        "blocks": {
            "parse_tx": [
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc-mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00",
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "out": None,
                },
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00",
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns-mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                        },
                    ),
                    "out": None,
                },
            ],
            "get_next_tx_index": [{"in": (), "out": 512}],
        },
        "cancel": {
            "compose": [
                {
                    "in": (
                        ADDR[1],
                        "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                    ),
                    "out": (
                        "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        [],
                        b"\x00\x00\x00Fz*\xb3\nN\x99`xc(\x06\xce\xbcV\xe6,\xc6\xb0L\xe4Z\x02s\x94\xfa\xa6\xe3\xde\xe7\x1b\xf8\x86",
                    ),
                },
                {
                    "in": (ADDR[1], "foobar"),
                    "error": (exceptions.ComposeError, ["no open offer with that hash"]),
                },
                {
                    "in": (
                        "foobar",
                        "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                    ),
                    "error": (exceptions.ComposeError, ["incorrect source address"]),
                },
                {
                    "in": (
                        ADDR[1],
                        "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5",
                    ),
                    "error": (exceptions.ComposeError, ["offer not open"]),
                },
            ],
            "parse": [
                {
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "data": b"\x00\x00\x00F\xdbN\xa0\x92\xbe\xa6\x03n=\x1e_n\xc8c\xdb\x9b\x90\x02R\xb4\xf4\xd6\xd9\xfa\xa6\x16S#\xf43\xc5\x1e",
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "fee": 10000,
                            "block_time": 310501000,
                            "tx_hash": "fb645106e276bfa1abd587f4a251b26f491a2a9ae61ca46a669794109728b122",
                            "destination": "",
                            "supported": 1,
                        },
                    ),
                    "out": None,
                },
                {
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "data": b"\x00\x00\x00Fz*\xb3\nN\x99`xc(\x06\xce\xbcV\xe6,\xc6\xb0L\xe4Z\x02s\x94\xfa\xa6\xe3\xde\xe7\x1b\xf8\x86",
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "fee": 10000,
                            "block_time": 310501000,
                            "tx_hash": "fb645106e276bfa1abd587f4a251b26f491a2a9ae61ca46a669794109728b122",
                            "destination": "",
                            "supported": 1,
                        },
                    ),
                    "records": [
                        {
                            "table": "cancels",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "offer_hash": "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "tx_hash": "fb645106e276bfa1abd587f4a251b26f491a2a9ae61ca46a669794109728b122",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 3,
                                "expiration": 1000,
                                "expire_index": 311101,
                                "block_index": DP["default_block_index"],
                                "deadline": 1388000200,
                                "counterwager_quantity": 10,
                                "wager_remaining": 10,
                                "counterwager_remaining": 10,
                                "tx_index": 102,
                                "fee_fraction_int": 5000000,
                                "status": "cancelled",
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "wager_quantity": 10,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "target_value": 0.0,
                                "tx_hash": "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                            },
                        },
                    ],
                },
            ],
        },
        "broadcast": {
            "validate": [
                {
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        ADDR[2],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": (["locked feed"]),
                },
                {
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        4294967296,
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": (["fee fraction greater than or equal to 1"]),
                },
                {
                    "in": (
                        ADDR[0],
                        -1388000000,
                        1,
                        DP["fee_multiplier"],
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": (["negative timestamp", "feed timestamps not monotonically increasing"]),
                },
                {
                    "in": (
                        None,
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "Unit Test",
                        DP["default_block_index"],
                    ),
                    "out": (["null source address"]),
                },
                {
                    "comment": "test changing options to ADDRESS_OPTION_MAX_VALUE + 1 on a specific address",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        ADDR[5],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "OPTIONS %i" % (config.ADDRESS_OPTION_MAX_VALUE + 1),
                        DP["default_block_index"],
                    ),
                    "out": (["options out of range"]),
                },
                {
                    "comment": "test changing options to -1 on a specific address",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        ADDR[5],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "OPTIONS -1",
                        DP["default_block_index"],
                    ),
                    "out": (["options integer overflow"]),
                },
                {
                    "comment": "test changing options to non-int on a specific address",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        ADDR[5],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "OPTIONS XCP",
                        DP["default_block_index"],
                    ),
                    "out": (["options not an integer"]),
                },
            ],
            "compose": [
                {
                    "comment": "test old text packing for short text",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (ADDR[0], 1588000000, 1, DP["fee_multiplier"], "Unit Test"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                    ),
                },
                {
                    "in": (P2SH_ADDR[0], 1588000000, 1, DP["fee_multiplier"], "Unit Test"),
                    "out": (
                        P2SH_ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                    ),
                },
                {
                    "comment": "test old text packing for 51 chars",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 51 characters test test test test test tes.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x003Exactly 51 characters test test test test test tes.",
                    ),
                },
                {
                    "comment": "test old text packing for 52 chars",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 52 characters test test test test test test.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004Exactly 52 characters test test test test test test.",
                    ),
                },
                {
                    "comment": "test old text packing for 53 chars",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 53 characters test test test test test testt.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Exactly 53 characters test test test test test testt.",
                    ),
                },
                {
                    "comment": "test old text packing for string with utf-8 char, "
                    "THIS IS A BUG! but for consensus reasons we want to keep it in tact! the length byte should be 1 higher",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (ADDR[0], 1588000000, 1, 0, "This is an e with an: è."),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18This is an e with an: \xc3\xa8",
                    ),
                },
                {
                    "comment": "test old text packing for LOCK",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (ADDR[0], 1388000100, 50000000, 0, "LOCK"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x04LOCK",
                    ),
                },
                {
                    "comment": "test current text packing for short text",
                    "in": (ADDR[0], 1588000000, 1, DP["fee_multiplier"], "Unit Test"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                    ),
                },
                {
                    "comment": "test current text packing for 51 chars",
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 51 characters test test test test test tes.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x003Exactly 51 characters test test test test test tes.",
                    ),
                },
                {
                    "comment": "test current text packing for 52 chars",
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 52 characters test test test test test test.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004Exactly 52 characters test test test test test test.",
                    ),
                },
                {
                    "comment": "test current text packing for 53 chars",
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        0,
                        "Exactly 53 characters test test test test test testt.",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x005Exactly 53 characters test test test test test testt.",
                    ),
                },
                {
                    "comment": "test current text packing for string with utf-8 char",
                    "in": (ADDR[0], 1588000000, 1, 0, "This is an e with an: è."),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19This is an e with an: \xc3\xa8.",
                    ),
                },
                {
                    "comment": "test current text packing for LOCK",
                    "in": (ADDR[0], 1388000100, 50000000, 0, "LOCK"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x04LOCK",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        1588000000,
                        1,
                        DP["fee_multiplier"],
                        "Over 80 characters test test test test test test test test test test test test test test test test test test",
                    ),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00LK@lOver 80 characters test test test test test test test test test test test test test test test test test test",
                    ),
                },
                {
                    "comment": "test current text packing for 'OPTIONS 1'",
                    "in": (ADDR[0], 1388000100, 50000000, 0, "OPTIONS 1"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\tOPTIONS 1",
                    ),
                },
                {
                    "comment": "test current text packing for 'OPTIONS 0'",
                    "in": (ADDR[0], 1388000100, 50000000, 0, "OPTIONS 0"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\tOPTIONS 0",
                    ),
                },
            ],
            "parse": [
                {
                    "comment": "test old text unpacking for short text",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x06BARFOO",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "BARFOO",
                                "timestamp": 1388000100,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 50000000.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text unpacking for 51 chars",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x003Exactly 51 characters test test test test test tes.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "Exactly 51 characters test test test test test tes.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text unpacking for 52 chars, "
                    "THIS IS A BUG! but for consensus reasons we want to keep it in tact! the '4' from the length byte is added to the stored text",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004Exactly 52 characters test test test test test test.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "4Exactly 52 characters test test test test test test.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text unpacking for 53 chars",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Exactly 53 characters test test test test test testt.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "Exactly 53 characters test test test test test testt.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text packing for string with utf-8 char, "
                    "THIS IS A BUG! but for consensus reasons we want to keep it in tact! the . is trimmed off because of a bad length byte",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x18This is an e with an: \xc3\xa8.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "This is an e with an: è",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text unpacking for bet",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "fee": 10000,
                            "btc_amount": 0,
                            "supported": 1,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "block_time": 310501000,
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                            "data": b"\x00\x00\x00\x1eR\xbb4,\xc0\x00\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 5000000,
                                "locked": 0,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "text": "Unit Test",
                                "timestamp": 1388000300,
                                "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                                "tx_index": DP["default_tx_index"],
                                "value": -2.0,
                            },
                        },
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 3,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 10,
                                "counterwager_remaining": 10,
                                "deadline": 1388000200,
                                "expiration": 1000,
                                "expire_index": 311101,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "dropped",
                                "target_value": 0.0,
                                "tx_hash": "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                                "tx_index": 102,
                                "wager_quantity": 10,
                                "wager_remaining": 10,
                            },
                        },
                    ],
                },
                {
                    "comment": "test old text unpacking for LOCK",
                    "mock_protocol_changes": {"broadcast_pack_text": False},
                    "in": (
                        {
                            "btc_amount": 0,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "supported": 1,
                            "block_time": 310501000,
                            "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x04LOCK",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": None,
                                "locked": 1,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": None,
                                "timestamp": 0,
                                "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                                "tx_index": DP["default_tx_index"],
                                "value": None,
                            },
                        }
                    ],
                },
                {
                    "comment": "test current text unpacking for short text",
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x06BARFOO",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "BARFOO",
                                "timestamp": 1388000100,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 50000000.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text unpacking for 51 chars",
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x003Exactly 51 characters test test test test test tes.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "Exactly 51 characters test test test test test tes.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text unpacking for 52 chars",
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x004Exactly 52 characters test test test test test test.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "Exactly 52 characters test test test test test test.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text unpacking for 53 chars, ",
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x005Exactly 53 characters test test test test test testt.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "Exactly 53 characters test test test test test testt.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text packing for string with utf-8 char, ",
                    "in": (
                        {
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "supported": 1,
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19This is an e with an: \xc3\xa8.",
                            "fee": 10000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 310501000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": "This is an e with an: è.",
                                "timestamp": 1588000000,
                                "tx_hash": "dd48da950fd7d000224b79ebe3495fa594ca6d6698f16c4e2dc93b4f116006ea",
                                "tx_index": DP["default_tx_index"],
                                "value": 1.0,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text unpacking for bet",
                    "in": (
                        {
                            "fee": 10000,
                            "btc_amount": 0,
                            "supported": 1,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "block_time": 310501000,
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                            "data": b"\x00\x00\x00\x1eR\xbb4,\xc0\x00\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 5000000,
                                "locked": 0,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "text": "Unit Test",
                                "timestamp": 1388000300,
                                "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                                "tx_index": DP["default_tx_index"],
                                "value": -2.0,
                            },
                        },
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 3,
                                "block_index": DP["default_block_index"],
                                "counterwager_quantity": 10,
                                "counterwager_remaining": 10,
                                "deadline": 1388000200,
                                "expiration": 1000,
                                "expire_index": 311101,
                                "fee_fraction_int": 5000000,
                                "feed_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "leverage": 5040,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "dropped",
                                "target_value": 0.0,
                                "tx_hash": "7a2ab30a4e996078632806cebc56e62cc6b04ce45a027394faa6e3dee71bf886",
                                "tx_index": 102,
                                "wager_quantity": 10,
                                "wager_remaining": 10,
                            },
                        },
                    ],
                },
                {
                    "comment": "attempt to cancel bet on LOCKED feed, should keep bet open",
                    "in": (
                        {
                            "fee": 10000,
                            "btc_amount": 0,
                            "supported": 1,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_index": DP["default_tx_index"],
                            "block_time": 310501000,
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "source": ADDR[4],
                            "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                            "data": b"\x00\x00\x00\x1eR\xbb4,\xc0\x00\x00\x00\x00\x00\x00\x00\x00LK@\tUnit Test",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 5000000,
                                "locked": 0,
                                "source": ADDR[4],
                                "status": "invalid: locked feed",
                                "text": "Unit Test",
                                "timestamp": 1388000300,
                                "tx_hash": "c9e8db96d520b0611218504801e74796ae4f476578512d21d3f99367ab8e356f",
                                "tx_index": DP["default_tx_index"],
                                "value": -2.0,
                            },
                        },
                        {
                            "table": "bets",
                            "values": {
                                "bet_type": 1,
                                "block_index": 310487,
                                "counterwager_quantity": 9,
                                "counterwager_remaining": 9,
                                "deadline": 1388000001,
                                "expiration": 100,
                                "expire_index": 310587,
                                "fee_fraction_int": 5000000,
                                "feed_address": ADDR[4],
                                "leverage": 5040,
                                "source": ADDR[4],
                                "status": "open",
                                "target_value": 0.0,
                                "tx_hash": "d25fbc4a7396c0ce2e13b49a652b4804c991d1a7bbeb265a5139b9510aa8c9b6",
                                "tx_index": 488,
                                "wager_quantity": 9,
                                "wager_remaining": 9,
                            },
                        },
                    ],
                },
                {
                    "comment": "test current text unpacking for LOCK",
                    "in": (
                        {
                            "btc_amount": 0,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "supported": 1,
                            "block_time": 310501000,
                            "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\x04LOCK",
                        },
                    ),
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": None,
                                "locked": 1,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "text": None,
                                "timestamp": 0,
                                "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                                "tx_index": DP["default_tx_index"],
                                "value": None,
                            },
                        }
                    ],
                },
                {
                    "comment": "test changing options to 1 on a specific address",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        {
                            "btc_amount": 0,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "source": ADDR[5],
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "supported": 1,
                            "block_time": 310501000,
                            "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\tOPTIONS 1",
                        },
                    ),
                    "records": [
                        {"table": "addresses", "values": {"options": 1, "address": ADDR[5]}}
                    ],
                },
                {
                    "comment": "test changing options to 1 on an address with LOCKED feed",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        {
                            "btc_amount": 1,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "source": ADDR[4],
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "supported": 1,
                            "block_time": 310501000,
                            "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\x1eR\xbb3dA\x87\xd7\x84\x00\x00\x00\x00\x00\x00\x00\x00\tOPTIONS 1",
                        },
                    ),
                    "out": None,
                    "records": [
                        {"table": "addresses", "values": {"options": 0, "address": ADDR[4]}}
                    ],
                },
                {
                    "comment": "test malformed message with incorrect length",
                    "mock_protocol_changes": {"broadcast_pack_text": True},
                    "in": (
                        {
                            "btc_amount": 1,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "source": ADDR[4],
                            "destination": "",
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "supported": 1,
                            "block_time": 310501000,
                            "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\x1e^\xa6\xf5\x00?\xf0\x00\x00\x00\x00\x00\x00\x00LK@#A 28 CHARACTERS LONG TEXT",
                        },
                    ),
                    "out": None,
                    "records": [
                        {
                            "table": "broadcasts",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "fee_fraction_int": 0,
                                "locked": 0,
                                "source": ADDR[4],
                                "status": "invalid: could not unpack text",
                                "text": None,
                                "timestamp": 0,
                                "tx_hash": "6b4a62b80f35b0e66df4591c8a445d453d995609e2df12afe93e742bea10dd86",
                                "tx_index": DP["default_tx_index"],
                                "value": None,
                            },
                        }
                    ],
                },
            ],
        },
        "burn": {
            "validate": [
                {
                    "in": (ADDR[0], DP["unspendable"], DP["burn_quantity"], DP["burn_start"]),
                    "out": ([]),
                },
                {
                    "in": (ADDR[0], DP["unspendable"], 1.1 * DP["burn_quantity"], DP["burn_start"]),
                    "out": (["quantity must be in satoshis"]),
                },
                {
                    "in": (ADDR[0], ADDR[1], DP["burn_quantity"], DP["burn_start"]),
                    "out": (["wrong destination address"]),
                },
                {
                    "in": (ADDR[0], DP["unspendable"], -1 * DP["burn_quantity"], DP["burn_start"]),
                    "out": (["negative quantity"]),
                },
                {
                    "in": (ADDR[0], DP["unspendable"], DP["burn_quantity"], DP["burn_start"] - 2),
                    "out": (["too early"]),
                },
                {
                    "in": (ADDR[0], DP["unspendable"], DP["burn_quantity"], DP["burn_end"] + 1),
                    "out": (["too late"]),
                },
                {
                    "in": (ADDR[0], ADDR[1], 1.1 * DP["burn_quantity"], DP["burn_start"] - 2),
                    "out": (["wrong destination address", "quantity must be in satoshis"]),
                },
                {
                    "in": (ADDR[0], ADDR[1], DP["burn_quantity"], DP["burn_start"] - 2),
                    "out": (["wrong destination address", "too early"]),
                },
                {
                    "in": (
                        MULTISIGADDR[0],
                        DP["unspendable"],
                        DP["burn_quantity"],
                        DP["burn_start"],
                    ),
                    "out": ([]),
                },
                {
                    "comment": "p2sh",
                    "in": (P2SH_ADDR[0], DP["unspendable"], DP["burn_quantity"], DP["burn_start"]),
                    "out": ([]),
                },
            ],
            "compose": [
                {
                    "in": (ADDR[1], DP["burn_quantity"]),
                    "out": (
                        "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        [("mvCounterpartyXXXXXXXXXXXXXXW24Hef", 62000000)],
                        None,
                    ),
                },
                {
                    "in": (ADDR[0], DP["burn_quantity"]),
                    "error": (exceptions.ComposeError, "1 BTC may be burned per address"),
                },
                {
                    "in": (MULTISIGADDR[0], int(DP["quantity"] / 2)),
                    "out": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        [("mvCounterpartyXXXXXXXXXXXXXXW24Hef", 50000000)],
                        None,
                    ),
                },
                {
                    "comment": "p2sh",
                    "in": (P2SH_ADDR[0], int(DP["burn_quantity"] / 2)),
                    "out": (P2SH_ADDR[0], [("mvCounterpartyXXXXXXXXXXXXXXW24Hef", 31000000)], None),
                },
            ],
            "parse": [
                {
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "destination": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "fee": 10000,
                            "block_time": 155409000,
                            "supported": 1,
                            "btc_amount": 62000000,
                            "data": b"",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_hash": DP["default_block_hash"],
                        },
                    ),
                    "records": [
                        {
                            "table": "burns",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "burned": 62000000,
                                "earned": 92994113884,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "burn",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 92994113884,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "supported": 1,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "btc_amount": 50000000,
                            "block_index": DP["default_block_index"],
                            "block_hash": DP["default_block_hash"],
                            "fee": 10000,
                            "data": b"",
                            "block_time": 155409000,
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "tx_index": DP["default_tx_index"],
                            "destination": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        },
                    ),
                    "records": [
                        {
                            "table": "burns",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "burned": 50000000,
                                "earned": 74995253132,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "burn",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 74995253132,
                            },
                        },
                    ],
                },
            ],
        },
        "destroy": {
            "validate": [
                {"in": (ADDR[0], None, "XCP", 1), "out": None},
                {"in": (P2SH_ADDR[0], None, "XCP", 1), "out": None},
                {
                    "in": (ADDR[0], None, "foobar", 1),
                    "error": (exceptions.ValidateError, "asset invalid"),
                },
                {
                    "in": (ADDR[0], ADDR[1], "XCP", 1),
                    "error": (exceptions.ValidateError, "destination exists"),
                },
                {
                    "in": (ADDR[0], None, "BTC", 1),
                    "error": (exceptions.ValidateError, "cannot destroy BTC"),
                },
                {
                    "in": (ADDR[0], None, "XCP", 1.1),
                    "error": (exceptions.ValidateError, "quantity not integer"),
                },
                {
                    "in": (ADDR[0], None, "XCP", 2**63),
                    "error": (exceptions.ValidateError, "integer overflow, quantity too large"),
                },
                {
                    "in": (ADDR[0], None, "XCP", -1),
                    "error": (exceptions.ValidateError, "quantity negative"),
                },
                {
                    "in": (ADDR[0], None, "XCP", 2**62),
                    "error": (exceptions.BalanceError, "balance insufficient"),
                },
            ],
            "pack": [
                {
                    "in": ("XCP", 1, bytes(9999999)),
                    "out": b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                }
            ],
            #'unpack': [{
            #    'in': (b'\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00',),
            #    'error': (exceptions.UnpackError, 'could not unpack')
            # }],
            "compose": [
                {
                    "in": (ADDR[0], "XCP", 1, bytes(9999999)),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (ADDR[0], "XCP", 1, b"WASTE"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01WASTE",
                    ),
                },
                {
                    "in": (ADDR[0], "XCP", 1, b"WASTEEEEE"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01WASTEEEEE",
                    ),
                },
                {
                    "in": (ADDR[0], "PARENT.already.issued", 1, b"WASTEEEEE"),
                    "out": (
                        ADDR[0],
                        [],
                        b"\x00\x00\x00n\x01S\x08!g\x1b\x10e\x00\x00\x00\x00\x00\x00\x00\x01WASTEEEEE",
                    ),
                },
            ],
            "parse": [
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "destination": None,
                            "data": b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01WASTE\x00\x00\x00",
                            "tx_index": DP["default_tx_index"],
                        },
                    ),
                    "records": [
                        {
                            "table": "destructions",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "quantity": 1,
                                "source": ADDR[0],
                                "status": "valid",
                                "tag": b"WASTE\x00\x00\x00",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "destination": ADDR[1],
                            "data": b"\x00\x00\x00n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01WASTE\x00\x00\x00",
                            "tx_index": DP["default_tx_index"],
                        },
                    ),
                    "records": [
                        {
                            "table": "destructions",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "quantity": 1,
                                "source": ADDR[0],
                                "status": "invalid: destination exists",
                                "tag": b"WASTE\x00\x00\x00",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
            ],
        },
        "issuance": {
            # validate (db, source, destination, asset, quantity, divisible, lock, reset, callable_, call_date, call_price, description, subasset_parent, subasset_longname=None, block_index=None):
            # validate (db, source, destination, asset, quantity, divisible,             ,callable_, call_date, call_price, description, block_index)
            "validate": [
                {
                    "in": (
                        ADDR[0],
                        None,
                        "ASSET",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 50000000, "", True, False, False, False, None),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        None,
                        "ASSET",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 50000000, "", True, False, False, False, None),
                },
                {
                    "in": (
                        ADDR[2],
                        None,
                        "DIVIDEND",
                        1000,
                        False,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["cannot change divisibility"],
                        0,
                        "",
                        False,
                        False,
                        False,
                        True,
                        None,
                    ),
                },
                {
                    # disabled for now because conftest.ALWAYS_LATEST_PROTOCOL_CHANGES = True
                    #
                    #    'in': (ADDR[2], None, 'DIVIDEND', 1000, True, None, None, True, None, None, '', None, None, DP['default_block_index']),
                    #    'out': (0, 0.0, ['cannot change callability'], 0, '', True, True, False, False, None)
                    # }, {
                    "in": (
                        ADDR[0],
                        None,
                        "BTC",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["cannot issue BTC or XCP"],
                        50000000,
                        "",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "XCP",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["cannot issue BTC or XCP"],
                        50000000,
                        "",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "NOSATOSHI",
                        1000.5,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, ["quantity must be in satoshis"], 0, "", True, None, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLPRICEFLOAT",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        100.0,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 0, "", True, False, False, False, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLPRICEINT",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        100,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 50000000, "", True, False, False, False, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLPRICESTR",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        "abc",
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, "abc", ["call_price must be a float"], 0, "", True, None, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLDATEINT",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        1409401723,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 50000000, "", True, False, False, False, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLDATEFLOAT",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        0.9 * 1409401723,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        1268461550.7,
                        0.0,
                        ["call_date must be epoch integer"],
                        0,
                        "",
                        True,
                        None,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "CALLDATESTR",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        "abc",
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        "abc",
                        0.0,
                        ["call_date must be epoch integer"],
                        0,
                        "",
                        True,
                        None,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "NEGVALUES",
                        -1000,
                        True,
                        None,
                        None,
                        True,
                        -1409401723,
                        -DP["quantity"],
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        -1409401723,
                        -100000000.0,
                        ["negative quantity", "negative call price", "negative call date"],
                        50000000,
                        "",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[2],
                        None,
                        "DIVISIBLE",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Divisible asset",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["issued by another address"],
                        0,
                        "Divisible asset",
                        True,
                        False,
                        False,
                        True,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "LOCKED",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Locked asset",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["locked asset and non‐zero quantity"],
                        0,
                        "Locked asset",
                        True,
                        False,
                        False,
                        True,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "BSSET",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "LOCK",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["cannot lock a non‐existent asset"],
                        50000000,
                        "LOCK",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    # Now it's possible to issue and transfer simultaneously
                    "in": (
                        ADDR[0],
                        ADDR[1],
                        "BSSET",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 50000000, "", True, False, False, False, None),
                },
                {
                    "in": (
                        ADDR[2],
                        None,
                        "BSSET",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["insufficient funds"],
                        50000000,
                        "",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "BSSET",
                        2**63,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["total quantity overflow", "integer overflow"],
                        50000000,
                        "",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    # Now it's possible to issue and transfer simultaneously
                    "in": (
                        ADDR[0],
                        ADDR[1],
                        "DIVISIBLE",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Divisible asset",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 0, "Divisible asset", True, False, False, True, None),
                },
                {
                    "in": (
                        ADDR[0],
                        None,
                        "MAXIMUM",
                        2**63 - 1,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Maximum quantity",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        [],
                        50000000,
                        "Maximum quantity",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "comment": "total + quantity has to be lower than MAX_INT",
                    "in": (
                        ADDR[0],
                        None,
                        "DIVISIBLE",
                        2**63 - 1,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Maximum quantity",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["total quantity overflow"],
                        0,
                        "Maximum quantity",
                        True,
                        False,
                        False,
                        True,
                        None,
                    ),
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "in": (
                        ADDR[0],
                        None,
                        f"A{26 ** 12 + 1}",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "NOTFOUND",
                        "NOTFOUND.child1",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["parent asset not found"],
                        25000000,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "in": (
                        ADDR[1],
                        None,
                        f"A{26 ** 12 + 1}",
                        100000000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "PARENT",
                        "PARENT.child1",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["parent asset owned by another address"],
                        25000000,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "in": (
                        ADDR[0],
                        None,
                        f"A{26 ** 12 + 1}",
                        100000000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "NOTFOUND",
                        "NOTFOUND.child1",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["parent asset not found"],
                        25000000,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "comment": "A subasset name must be unique",
                    "in": (
                        ADDR[0],
                        None,
                        f"A{26 ** 12 + 1}",
                        100000000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "PARENT",
                        "PARENT.already.issued",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["subasset already exists"],
                        25000000,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "comment": "cannot change subasset name through a reissuance description modification",
                    "in": (
                        ADDR[0],
                        None,
                        f"A{26 ** 12 + 101}",
                        200000000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "PARENT",
                        "PARENT.changed.name",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        [],
                        0,
                        "description",
                        True,
                        False,
                        False,
                        True,
                        "PARENT.already.issued",
                    ),
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "in": (
                        ADDR[0],
                        None,
                        "UNRELATED",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "PARENT",
                        "PARENT.child1",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["a subasset must be a numeric asset"],
                        25000000,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    "comment": "subassets are free after protocol change",
                    "in": (
                        ADDR[0],
                        None,
                        "UNRELATED",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "description",
                        "PARENT",
                        "PARENT.child1",
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["a subasset must be a numeric asset"],
                        0,
                        "description",
                        True,
                        False,
                        False,
                        False,
                        None,
                    ),
                },
                {
                    # before protocol change, reissuing a quantity of a locked asset was allowed if the description was changed
                    "comment": "allow reissuance of locked asset before fix",
                    "mock_protocol_changes": {"issuance_lock_fix": False},
                    "in": (
                        ADDR[6],
                        None,
                        "LOCKEDPREV",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Locked prev",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (0, 0.0, [], 0, "Locked prev", True, False, False, True, None),
                },
                {
                    # after protocol change, reissuing quantities for a locked asset is never allowed
                    "comment": "disallow reissuance of locked asset after fix",
                    "mock_protocol_changes": {"issuance_lock_fix": True},
                    "in": (
                        ADDR[6],
                        None,
                        "LOCKEDPREV",
                        1000,
                        True,
                        None,
                        None,
                        False,
                        None,
                        None,
                        "Locked prev",
                        None,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": (
                        0,
                        0.0,
                        ["locked asset and non‐zero quantity"],
                        0,
                        "Locked prev",
                        True,
                        False,
                        False,
                        True,
                        None,
                    ),
                },
            ],
            # compose (db, source, transfer_destination, asset, quantity, divisible, lock, reset=None, description=None)
            "compose": [
                {
                    "in": (ADDR[0], "ASSET", 1000, None, True, False, None, ""),
                    "error": (exceptions.AssetNameError, "non‐numeric asset name starts with ‘A’"),
                },
                {
                    "in": (ADDR[0], "BSSET1", 1000, None, True, False, None, ""),
                    "error": (exceptions.AssetNameError, "invalid character:"),
                },
                {
                    "in": (ADDR[0], "SET", 1000, None, True, False, None, ""),
                    "error": (exceptions.AssetNameError, "too short"),
                },
                {
                    "comment": "disallow subassets on numerics",
                    "mock_protocol_changes": {"allow_subassets_on_numerics": False},
                    "in": (
                        ADDR[0],
                        "A9542895.subasset",
                        1000,
                        None,
                        True,
                        False,
                        None,
                        "",
                    ),
                    "error": (exceptions.AssetNameError, "parent asset name starts with 'A'"),
                },
                {
                    "comment": "allow subassets on numerics",
                    "in": (
                        ADDR[0],
                        "A95428956661682177.subasset",
                        1000,
                        None,
                        True,
                        False,
                        None,
                        "",
                    ),
                    "error": (exceptions.ComposeError, ["parent asset not found"]),
                },
                {
                    "in": (ADDR[0], "BSSET", 1000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x0b\xfc\xe3\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (ADDR[0], "BASSET", 1000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\xbaOs\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (P2SH_ADDR[0], "BSSET", 1000, None, True, False, None, ""),
                    "out": (
                        P2SH_ADDR[0],
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x0b\xfc\xe3\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "BSSET",
                        1000,
                        None,
                        True,
                        False,
                        None,
                        "description much much much longer than 42 letters",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x0b\xfc\xe3\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00description much much much longer than 42 letters",
                    ),
                },
                {
                    "in": (ADDR[0], "DIVISIBLE", 0, ADDR[1], True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [("mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns", None)],
                        b"\x00\x00\x00\x16\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (MULTISIGADDR[0], "BSSET", 1000, None, True, False, None, ""),
                    "out": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x0b\xfc\xe3\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (ADDR[0], "DIVISIBLE", 0, MULTISIGADDR[0], True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [
                            (
                                "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                None,
                            )
                        ],
                        b"\x00\x00\x00\x16\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "MAXIMUM",
                        2**63 - 1,
                        None,
                        True,
                        False,
                        None,
                        "Maximum quantity",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x00\x00\xdd\x96\xd2t\x7f\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00Maximum quantity",
                    ),
                },
                {
                    "in": (ADDR[0], f"A{2 ** 64 - 1}", 1000, None, None, False, None, None),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0NULL",
                    ),
                },
                {
                    "in": (ADDR[0], f"A{2 ** 64}", 1000, None, True, False, None, ""),
                    "error": (exceptions.AssetNameError, "numeric asset name not in range"),
                },
                {
                    "in": (ADDR[0], f"A{26 ** 12}", 1000, None, True, False, None, ""),
                    "error": (exceptions.AssetNameError, "numeric asset name not in range"),
                },
                {
                    "comment": "basic child asset",
                    "in": (ADDR[0], "PARENT.child1", 100000000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000001701530821671b10010000000005f5e100010a57c6f36de23a1f5f4c46"
                        ),
                    ),
                    # 00000017|01530821671b1001|0000000005f5e100|01|0a|57c6f36de23a1f5f4c46
                    # 00000015|01530821671b1001|0000000005f5e100|01|0a|57c6f36de23a1f5f4c46
                },
                {
                    "comment": "basic child asset with description",
                    "in": (
                        ADDR[0],
                        "PARENT.child1",
                        100000000,
                        None,
                        True,
                        False,
                        None,
                        "hello world",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000001701530821671b10010000000005f5e100010a57c6f36de23a1f5f4c4668656c6c6f20776f726c64"
                        ),
                    ),
                    # 00000017|01530821671b1001|0000000005f5e100|01|0a|57c6f36de23a1f5f4c46|68656c6c6f20776f726c64
                    # 00000015|01530821671b1001|0000000005f5e100|01|0a|57c6f36de23a1f5f4c46|68656c6c6f20776f726c64
                    #     |           |               |           |  |   |                   |
                    #     |           |               |           |  |   |                   └─── Description - "hello world"
                    #     |           |               |           |  |   └─── Subasset (compacted) - "PARENT.child1"
                    #     |           |               |           |  └─── Length of the subasset data (up to 255) - 10
                    #     |           |               |           └─── divisible (1 byte)
                    #     |           |               └───── quantity (8 bytes) - 100000000
                    #     |           └────────────────── asset name (8 bytes) - Numeric asset A95428956661682177 (26**12 + 1)
                    #     └────────────────── Type ID (4 bytes) - type 21/subasset
                },
                {
                    "in": (ADDR[0], "PARENT.a.b.c", 1000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000001701530821671b100100000000000003e8010a014a74856171ca3c559f"
                        ),
                    ),
                    # 00000017|01530821671b1001|00000000000003e8|01|0a|014a74856171ca3c559f
                    # 00000015|01530821671b1001|00000000000003e8|01|0a|014a74856171ca3c559f
                },
                {
                    "in": (ADDR[0], "PARENT.a-zA-Z0-9.-_@!", 1000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000001701530821671b100100000000000003e801108e90a57dba99d3a77b0a2470b1816edb"
                        ),
                    ),
                    # 00000017|01530821671b1001|00000000000003e8|01|10|8e90a57dba99d3a77b0a2470b1816edb
                },
                {
                    "comment": "make sure compose catches asset name syntax errors",
                    "in": (ADDR[0], "BADASSETx.child1", 1000, None, True, False, None, ""),
                    "error": (
                        exceptions.AssetNameError,
                        "parent asset name contains invalid character:",
                    ),
                },
                {
                    "comment": "make sure compose catches validation errors",
                    "in": (ADDR[1], "PARENT.child1", 1000, None, True, False, None, ""),
                    "error": (exceptions.ComposeError, ["parent asset owned by another address"]),
                },
                {
                    "comment": "referencing parent asset by name composes a reissuance",
                    "in": (ADDR[0], "PARENT.already.issued", 1000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x01S\x08!g\x1b\x10e\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "comment": "basic child asset with compact message type id",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (ADDR[0], "PARENT.child1", 100000000, None, True, False, None, ""),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "1701530821671b10010000000005f5e100010a57c6f36de23a1f5f4c46"
                        ),
                    ),
                    # 17|01530821671b1001|0000000005f5e100|01|0a|57c6f36de23a1f5f4c46
                },
                {
                    "in": (
                        ADDR[0],
                        f"A{26 ** 12 + 101}",
                        200000000,
                        None,
                        True,
                        None,
                        None,
                        "description",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x01S\x08!g\x1b\x10e\x00\x00\x00\x00\x0b\xeb\xc2\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00description",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLEB",
                        0,
                        ADDR[1],
                        True,
                        False,
                        None,
                        "second divisible asset",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [("mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns", None)],
                        b"\x00\x00\x00\x16\x00\x00\x10}U\x15\xa8]\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00second divisible asset",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLEC",
                        0,
                        None,
                        True,
                        True,
                        None,
                        "third divisible asset",
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\x16\x00\x00\x10}U\x15\xa8^\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00third divisible asset",
                    ),
                },
            ],
            "parse": [
                {
                    "comment": "first",
                    "in": (
                        {
                            "supported": 1,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "data": b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\xbaOs\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                            "btc_amount": None,
                            "destination": None,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "block_hash": DP["default_block_hash"],
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "BASSET",
                                "block_index": DP["default_block_index"],
                                "description": "",
                                "divisible": 1,
                                "fee_paid": 50000000,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 1000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "asset_longname": None,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "BASSET",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 1000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 50000000,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_time": 155409000,
                            "btc_amount": 7800,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "block_index": DP["default_block_index"],
                            "data": b"\x00\x00\x00\x16\x00\x00\x10}U\x15\xa8]\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00second divisible asset",
                            "block_hash": DP["default_block_hash"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "fee": 10000,
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "DIVISIBLEB",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "second divisible asset",
                                "divisible": 1,
                                "fee_paid": 50000000,
                                "issuer": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "locked": 0,
                                "quantity": 0,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "in": (
                        {
                            "tx_index": DP["default_tx_index"],
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "data": b"\x00\x00\x00\x16\x00\x00\x10}U\x15\xa8^\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00third divisible asset",
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "fee": 10000,
                            "destination": None,
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "btc_amount": None,
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "DIVISIBLEC",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "third divisible asset",
                                "divisible": 1,
                                "fee_paid": 50000000,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,  # lock arg ignored
                                "quantity": 0,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "in": (
                        {
                            "data": b"\x00\x00\x00\x16\x00\x00\x00\x00\x00\x0b\xfc\xe3\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0NULL",
                            "supported": 1,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_index": DP["default_block_index"],
                            "destination": "",
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "btc_amount": 0,
                            "tx_index": DP["default_tx_index"],
                            "block_hash": DP["default_block_hash"],
                            "block_time": 155409000,
                            "fee": 10000,
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "BSSET",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "",
                                "divisible": 1,
                                "fee_paid": 50000000,
                                "issuer": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "locked": 0,
                                "quantity": 1000,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "valid",
                                "transfer": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "BSSET",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 1000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 50000000,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "fee": 10000,
                            "block_time": 155409000,
                            "data": b"\x00\x00\x00\x16\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                            "block_index": DP["default_block_index"],
                            "block_hash": DP["default_block_hash"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "btc_amount": 7800,
                            "tx_index": DP["default_tx_index"],
                            "destination": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "supported": 1,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "DIVISIBLE",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "",
                                "divisible": 1,
                                "fee_paid": 0,
                                "issuer": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "locked": 0,
                                "quantity": 0,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 0,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "data": b"\x00\x00\x00\x16\x00\x00\x00\x00\xdd\x96\xd2t\x7f\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00Maximum quantity",
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "MAXIMUM",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "Maximum quantity",
                                "fee_paid": 50000000,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 9223372036854775807,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "divisible": 1,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "MAXIMUM",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 9223372036854775807,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 50000000,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "data": b"\x00\x00\x00\x16\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x03\xe8\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0NULL",
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "4188c1f7aaae56ce3097ef256cdbcb644dd43c84e237b4add4f24fd4848cb2c7",
                            "destination": "",
                            "fee": 10000,
                            "btc_amount": 0,
                            "block_time": 2815010000000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "block_hash": "8e80b430efbe3e1b7cc13d7ec51c1e47a16b0fa23d6dd3c939fb6c4d4cfa311e1f25072500f5f9872373b54c72424b3557fccd68915d00c0afb6523702e11b6a",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": "A18446744073709551615",
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": "",
                                "divisible": 1,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 1000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "tx_hash": "4188c1f7aaae56ce3097ef256cdbcb644dd43c84e237b4add4f24fd4848cb2c7",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "A18446744073709551615",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "4188c1f7aaae56ce3097ef256cdbcb644dd43c84e237b4add4f24fd4848cb2c7",
                                "quantity": 1000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "4188c1f7aaae56ce3097ef256cdbcb644dd43c84e237b4add4f24fd4848cb2c7",
                                "quantity": 0,
                            },
                        },
                    ],
                },
                {
                    "comment": "too short asset length",
                    # 00000014|00000000000002bf|0000000005f5e100|01
                    #     |           |               |           |
                    #     |           |               |           └─── divisible (1 byte)
                    #     |           |               └───── quantity (8 bytes) - 100000000
                    #     |           └────────────────── asset name (8 bytes) - BBB (invalid)
                    #     └────────────────── Type ID (4 bytes) - type 20/issuance
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001400000000000002bf0000000005f5e10001"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: bad asset name",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "comment": "first time issuance of subasset",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010a57c6f36de23a1f5f4c46"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": f"A{26 ** 12 + 1}",
                                "asset_longname": "PARENT.child1",
                                "block_index": DP["default_block_index"],
                                "description": "",
                                "fee_paid": 25000000,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 100000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "divisible": 1,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": f"A{26 ** 12 + 1}",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 25000000,
                            },
                        },
                        {
                            "table": "assets",
                            "values": {
                                "asset_id": int(26**12 + 1),
                                "asset_name": f"A{26 ** 12 + 1}",
                                "block_index": DP["default_block_index"],
                                "asset_longname": "PARENT.child1",
                            },
                        },
                    ],
                },
                {
                    "mock_protocol_changes": {"free_subassets": False},
                    "comment": "first time issuance of subasset with description",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010a57c6f36de23a1f5f4c4668656c6c6f20776f726c64"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": f"A{26 ** 12 + 1}",
                                "asset_longname": "PARENT.child1",
                                "block_index": DP["default_block_index"],
                                "description": "hello world",
                                "fee_paid": 25000000,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 100000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "divisible": 1,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": f"A{26 ** 12 + 1}",
                                "block_index": DP["default_block_index"],
                                "calling_function": "issuance",
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "issuance fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "quantity": 25000000,
                            },
                        },
                        {
                            "table": "assets",
                            "values": {
                                "asset_id": int(26**12 + 1),
                                "asset_name": f"A{26 ** 12 + 1}",
                                "block_index": DP["default_block_index"],
                                "asset_longname": "PARENT.child1",
                            },
                        },
                    ],
                },
                {
                    "comment": "subassets not enabled yet",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010a57c6f36de23a1f5f4c46"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "mock_protocol_changes": {"subassets": False},
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: could not unpack",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "invalid subasset length",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e10001f057c6f36de23a1f5f4c46"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: could not unpack",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "first time issuance of subasset with description",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010c0631798cf0c65f1507f66fdf"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: bad subasset name",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "missing subasset name",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010c"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: could not unpack",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "subasset length of zero",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e1000100"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: bad subasset name",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "bad subasset B.bad",
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "0000001501530821671b10010000000005f5e100010509cad71adf"
                            ),
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.SUBASSET_ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": None,
                                "asset_longname": None,
                                "block_index": DP["default_block_index"],
                                "description": None,
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: bad subasset name",
                                "transfer": 0,
                                "divisible": None,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "reissuance of subasset adds asset_longname to issuances table",
                    "in": (
                        {
                            "data": b"\x00\x00\x00\x16\x01S\x08!g\x1b\x10e\x00\x00\x00\x00\x0b\xeb\xc2\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00description",
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "destination": "",
                            "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                        },
                        issuance.ID,
                    ),
                    "records": [
                        {
                            "table": "issuances",
                            "values": {
                                "asset": f"A{26 ** 12 + 101}",
                                "asset_longname": "PARENT.already.issued",
                                "block_index": DP["default_block_index"],
                                "description": "description",
                                "fee_paid": 0,
                                "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "locked": 0,
                                "quantity": 200000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "transfer": 0,
                                "divisible": 1,
                                "tx_hash": "71da4fac29d6442ef3ff13f291860f512a888161ae9e574f313562851912aace",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
            ],
        },
        "dividend": {
            "validate": [
                {
                    "in": (
                        ADDR[0],
                        DP["quantity"] * 1000,
                        "DIVISIBLE",
                        "XCP",
                        DP["default_block_index"],
                    ),
                    "out": (None, None, ["insufficient funds (XCP)"], 0),
                },
                {
                    "in": (
                        ADDR[0],
                        DP["quantity"] * -1000,
                        "DIVISIBLE",
                        "XCP",
                        DP["default_block_index"],
                    ),
                    "out": (None, None, ["non‐positive quantity per unit"], 0),
                },
                {
                    "comment": "cannot pay dividends to holders of BTC",
                    "in": (ADDR[0], DP["quantity"], "BTC", "XCP", DP["default_block_index"]),
                    "out": (
                        None,
                        None,
                        ["cannot pay dividends to holders of BTC", "only issuer can pay dividends"],
                        0,
                    ),
                },
                {
                    "comment": "cannot pay dividends to holders of XCP",
                    "in": (ADDR[0], DP["quantity"], "XCP", "XCP", DP["default_block_index"]),
                    "out": (
                        None,
                        None,
                        [
                            "cannot pay dividends to holders of XCP",
                            "only issuer can pay dividends",
                            "insufficient funds (XCP)",
                        ],
                        0,
                    ),
                },
                {
                    "comment": "no such asset, NOASSET",
                    "in": (ADDR[0], DP["quantity"], "NOASSET", "XCP", DP["default_block_index"]),
                    "out": (None, None, ["no such asset, NOASSET."], 0),
                },
                {
                    "comment": "non‐positive quantity per unit",
                    "in": (ADDR[0], 0, "DIVISIBLE", "XCP", DP["default_block_index"]),
                    "out": (None, None, ["non‐positive quantity per unit", "zero dividend"], 0),
                },
                {
                    "in": (ADDR[1], DP["quantity"], "DIVISIBLE", "XCP", DP["default_block_index"]),
                    "out": (
                        None,
                        None,
                        ["only issuer can pay dividends", "insufficient funds (XCP)"],
                        0,
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        DP["quantity"],
                        "DIVISIBLE",
                        "NOASSET",
                        DP["default_block_index"],
                    ),
                    "out": (None, None, ["no such dividend asset, NOASSET."], 0),
                },
                {
                    "in": (ADDR[0], 8359090909, "DIVISIBLE", "XCP", DP["default_block_index"]),
                    "out": (None, None, ["insufficient funds (XCP)"], 0),
                },
                {
                    "in": (ADDR[2], 100000000, "DIVIDEND", "DIVIDEND", DP["default_block_index"]),
                    "out": (None, None, ["insufficient funds (XCP)"], 0),
                },
                {
                    "in": (ADDR[2], 2**63, "DIVIDEND", "DIVIDEND", DP["default_block_index"]),
                    "out": (None, None, ["integer overflow", "insufficient funds (DIVIDEND)"], 0),
                },
            ],
            "compose": [
                {
                    "in": (ADDR[0], DP["quantity"], "DIVISIBLE", "XCP"),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x002\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x00\x00\x00\x01",
                    ),
                },
                {
                    "in": (ADDR[0], 1, "DIVISIBLE", "PARENT.already.issued"),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "000000320000000000000001000000a25be34b6601530821671b1065"
                        ),
                    ),
                },
            ],
            "parse": [
                {
                    "comment": "dividend 1",
                    "in": (
                        {
                            "tx_hash": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                            "supported": 1,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "data": b"\x00\x00\x002\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x00\x00\x00\x01",
                            "tx_index": DP["default_tx_index"],
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "block_index": DP["default_block_index"],
                            "btc_amount": 0,
                            "fee": 10000,
                            "destination": "",
                            "block_time": 155409000,
                        },
                    ),
                    "records": [
                        {
                            "table": "dividends",
                            "values": {
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "dividend_asset": "XCP",
                                "fee_paid": 80000,
                                "quantity_per_unit": 100000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "dividend",
                                "event": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "dividend",
                                "event": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "quantity": 1000000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "dividend",
                                "event": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "dividend",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "quantity": 1200000001,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "dividend fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "450c4ced564fa52a84746ecd79d64db6f124bddee19ff2c3cd926adea673ce4c",
                                "quantity": 80000,
                            },
                        },
                    ],
                },
                {
                    "comment": "dividend 2",
                    "in": (
                        {
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 0,
                            "block_time": 155409000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "tx_hash": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                            "fee": 10000,
                            "block_index": DP["default_block_index"],
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "supported": 1,
                            "destination": "",
                            "data": b"\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x01\x00\x06\xca\xd8\xdc\x7f\x0bf\x00\x00\x00\x00\x00\x00\x00\x01",
                        },
                    ),
                    "records": [
                        {
                            "table": "dividends",
                            "values": {
                                "asset": "NODIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "dividend_asset": "XCP",
                                "fee_paid": 40000,
                                "quantity_per_unit": 1,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "dividend",
                                "event": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                                "quantity": 5,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "dividend",
                                "event": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                                "quantity": 10,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "dividend",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                                "quantity": 15,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "dividend fee",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "5a36e9d939e70917695065b11b728f7ccbc7b828ae3baca1115885d8889e67c7",
                                "quantity": 40000,
                            },
                        },
                    ],
                },
            ],
        },
        "order": {
            "validate": [
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"],
                        "XCP",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"],
                        "XCP",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"],
                        "XCP",
                        DP["quantity"],
                        2000,
                        0.5,
                        DP["default_block_index"],
                    ),
                    "out": (["fee_required must be in satoshis"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "BTC",
                        DP["quantity"],
                        "BTC",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["cannot trade BTC for itself"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"] / 3,
                        "XCP",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["give_quantity must be in satoshis"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"],
                        "XCP",
                        DP["quantity"] / 3,
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["get_quantity must be in satoshis"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        DP["quantity"],
                        "XCP",
                        DP["quantity"],
                        1.5,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["expiration must be expressed as an integer block delta"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        -DP["quantity"],
                        "XCP",
                        -DP["quantity"],
                        -2000,
                        -10000,
                        DP["default_block_index"],
                    ),
                    "out": (
                        [
                            "non‐positive give quantity",
                            "non‐positive get quantity",
                            "negative fee_required",
                            "negative expiration",
                        ]
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        0,
                        "XCP",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["non‐positive give quantity", "zero give or zero get"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "NOASSETA",
                        DP["quantity"],
                        "NOASSETB",
                        DP["quantity"],
                        2000,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (
                        ["no such asset to give (NOASSETA)", "no such asset to get (NOASSETB)"]
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "DIVISIBLE",
                        2**63 + 10,
                        "XCP",
                        DP["quantity"],
                        4 * 2016 + 10,
                        0,
                        DP["default_block_index"],
                    ),
                    "out": (["integer overflow", "expiration overflow"]),
                },
            ],
            "compose": [
                {
                    "in": (
                        ADDR[0],
                        "BTC",
                        DP["small"],
                        "XCP",
                        DP["small"] * 2,
                        DP["expiration"],
                        0,
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (
                        P2SH_ADDR[0],
                        "BTC",
                        DP["small"],
                        "XCP",
                        DP["small"] * 2,
                        DP["expiration"],
                        0,
                    ),
                    "out": (
                        P2SH_ADDR[0],
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "XCP",
                        round(DP["small"] * 2.1),
                        "BTC",
                        DP["small"],
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x06B,@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\n\x00\x00\x00\x00\x00\r\xbb\xa0",
                    ),
                },
                {
                    "in": (
                        MULTISIGADDR[0],
                        "BTC",
                        DP["small"],
                        "XCP",
                        DP["small"] * 2,
                        DP["expiration"],
                        0,
                    ),
                    "out": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00",
                    ),
                },
                {
                    "in": (
                        MULTISIGADDR[0],
                        "XCP",
                        round(DP["small"] * 2.1),
                        "BTC",
                        DP["small"],
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "out": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x06B,@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\n\x00\x00\x00\x00\x00\r\xbb\xa0",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "MAXI",
                        2**63 - 1,
                        "XCP",
                        DP["quantity"],
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x03:>\x7f\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\r\xbb\xa0",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        "MAXI",
                        2**63 - 1,
                        "XCP",
                        DP["quantity"],
                        DP["expiration"],
                        2**63,
                    ),
                    "error": (exceptions.ComposeError, ["integer overflow"]),
                },
                {
                    "in": (
                        ADDR[0],
                        "MAXI",
                        2**63,
                        "XCP",
                        DP["quantity"],
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "error": (exceptions.ComposeError, "insufficient funds"),
                },
                {
                    "comment": "give subasset",
                    "in": (
                        ADDR[0],
                        "PARENT.already.issued",
                        100000000,
                        "XCP",
                        DP["small"],
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000000a01530821671b10650000000005f5e10000000000000000010000000002faf080000a00000000000dbba0"
                        ),
                    ),
                },
                {
                    "comment": "get subasset",
                    "in": (
                        ADDR[0],
                        "XCP",
                        DP["small"],
                        "PARENT.already.issued",
                        100000000,
                        DP["expiration"],
                        DP["fee_required"],
                    ),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "0000000a00000000000000010000000002faf08001530821671b10650000000005f5e100000a00000000000dbba0"
                        ),
                    ),
                },
            ],
            "parse": [
                {
                    "comment": "order 1",
                    "in": (
                        {
                            "destination": None,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "fee": 10000,
                            "btc_amount": None,
                            "supported": 1,
                            "block_hash": DP["default_block_hash"],
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 0,
                                "give_asset": "DIVISIBLE",
                                "give_quantity": 100000000,
                                "give_remaining": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "filled",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "DIVISIBLE",
                                "backward_quantity": 100000000,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 0,
                                "forward_asset": "XCP",
                                "forward_quantity": 100000000,
                                "id": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "completed",
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_block_index": 310006,
                                "tx0_expiration": 2000,
                                "tx0_hash": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf",
                                "tx0_index": 7,
                                "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 2000,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "order match",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "order match",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "filled",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 0,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "filled",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf",
                                "quantity": 0,
                            },
                        },
                    ],
                },
                {
                    "comment": "P2SH order",
                    "in": (
                        {
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "block_index": DP["default_block_index"],
                            "block_time": 155409000,
                            "btc_amount": None,
                            "data": b"\x00\x00\x00\n\x00\x00\x00\xa2[\xe3Kf\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "destination": None,
                            "fee": 10000,
                            "source": P2SH_ADDR[0],
                            "supported": 1,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "tx_index": DP["default_tx_index"],
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 0,
                                "give_asset": "DIVISIBLE",
                                "give_quantity": 100000000,
                                "give_remaining": 0,
                                "source": P2SH_ADDR[0],
                                "status": "filled",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "DIVISIBLE",
                                "backward_quantity": 100000000,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 0,
                                "forward_asset": "XCP",
                                "forward_quantity": 100000000,
                                "id": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "completed",
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_block_index": 310006,
                                "tx0_expiration": 2000,
                                "tx0_hash": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf",
                                "tx0_index": 7,
                                "tx1_address": P2SH_ADDR[0],
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 2000,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": P2SH_ADDR[0],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "order match",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": P2SH_ADDR[0],
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "order match",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "filled",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 0,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": P2SH_ADDR[0],
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "filled",
                                "event": "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf",
                                "quantity": 0,
                            },
                        },
                    ],
                },
                {
                    "comment": "order 2",
                    "in": (
                        {
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "btc_amount": None,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0fB@\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "destination": None,
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 1000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": -20000000,
                                "give_asset": "BTC",
                                "give_quantity": 1000000,
                                "give_remaining": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "BTC",
                                "backward_quantity": 200000,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 1800,
                                "forward_asset": "XCP",
                                "forward_quantity": 20000000,
                                "id": "b6c0ce5991e1ab4b46cdd25f612cda202d123872c6250831bc0f510a90c1238e_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "pending",
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_block_index": 310010,
                                "tx0_expiration": 2000,
                                "tx0_hash": "b6c0ce5991e1ab4b46cdd25f612cda202d123872c6250831bc0f510a90c1238e",
                                "tx0_index": 11,
                                "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 2000,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
                {
                    "comment": "order 2bis",
                    "in": (
                        {
                            "fee": 10000,
                            "block_time": 155409000,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "destination": None,
                            "supported": 1,
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n,+\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": None,
                            "block_index": DP["default_block_index"],
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "BTC",
                                "get_quantity": 666666,
                                "get_remaining": -133333,
                                "give_asset": "XCP",
                                "give_quantity": 99999990,
                                "give_remaining": 115,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "XCP",
                                "backward_quantity": 99999875,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 0,
                                "forward_asset": "BTC",
                                "forward_quantity": 799999,
                                "id": "05bcc7b25130206aca1f3b695e4d9ed392c9f16c0294ab292c0a029c1bb5e4ca_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "pending",
                                "tx0_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "tx0_block_index": 310513,
                                "tx0_expiration": 2000,
                                "tx0_hash": "05bcc7b25130206aca1f3b695e4d9ed392c9f16c0294ab292c0a029c1bb5e4ca",
                                "tx0_index": 493,
                                "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 2000,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 99999990,
                            },
                        },
                    ],
                },
                {
                    "comment": "order 3",
                    "in": (
                        {
                            "block_time": 155409000,
                            "destination": None,
                            "btc_amount": None,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x84\x80\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "supported": 1,
                            "fee": 10000,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "tx_index": DP["default_tx_index"],
                            "block_index": DP["default_block_index"],
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "BTC",
                                "get_quantity": 1999999,
                                "get_remaining": 1999999,
                                "give_asset": "XCP",
                                "give_quantity": 99999990,
                                "give_remaining": 99999990,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 99999990,
                            },
                        },
                    ],
                },
                {
                    "comment": "5",
                    "in": (
                        {
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\xa1 \x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "tx_index": DP["default_tx_index"],
                            "destination": None,
                            "block_index": DP["default_block_index"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "btc_amount": None,
                            "block_time": 155409000,
                            "supported": 1,
                            "fee": 1000000,
                            "block_hash": DP["default_block_hash"],
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 1000000,
                                "fee_provided_remaining": 1000000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 100000000,
                                "give_asset": "BTC",
                                "give_quantity": 500000,
                                "give_remaining": 500000,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "comment": "order 4",
                    "in": (
                        {
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "btc_amount": None,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00 foo\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "destination": None,
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 0,
                                "expire_index": DP["default_block_index"],
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "0",
                                "get_quantity": 0,
                                "get_remaining": 0,
                                "give_asset": "0",
                                "give_quantity": 0,
                                "give_remaining": 0,
                                "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "status": "invalid: could not unpack",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
                {
                    "comment": "7",
                    "in": (
                        {
                            "btc_amount": None,
                            "block_time": 155409000,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "block_hash": DP["default_block_hash"],
                            "destination": None,
                            "block_index": DP["default_block_index"],
                            "data": b"\x00\x00\x00\n\x00\x06\xca\xd8\xdc\x7f\x0bf\x00\x00\x00\x00\x00\x00\x01\xf4\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x07\xd0\x00\x00\x00\x00\x00\x00\x00\x00",
                            "fee": 10000,
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 2000,
                                "expire_index": DP["default_block_index"] + 2000,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 100000000,
                                "give_asset": "NODIVISIBLE",
                                "give_quantity": 500,
                                "give_remaining": 500,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "NODIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 500,
                            },
                        },
                    ],
                },
                {
                    "comment": "order 5",
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00",
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "destination": "",
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "block_time": 155409000,
                            "btc_amount": 0,
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 10,
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 2800,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 0,
                                "give_asset": "BTC",
                                "give_quantity": 50000000,
                                "give_remaining": 49200000,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "BTC",
                                "backward_quantity": 800000,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 7200,
                                "forward_asset": "XCP",
                                "forward_quantity": 100000000,
                                "id": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "pending",
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_block_index": 310513,
                                "tx0_expiration": 2000,
                                "tx0_hash": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5",
                                "tx0_index": 492,
                                "tx1_address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 10,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
                {
                    "comment": "order 6",
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00",
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "destination": "",
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "block_time": 155409000,
                            "btc_amount": 0,
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 10,
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 2800,
                                "fee_required": 0,
                                "fee_required_remaining": 0,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 0,
                                "give_asset": "BTC",
                                "give_quantity": 50000000,
                                "give_remaining": 49200000,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "order_matches",
                            "values": {
                                "backward_asset": "BTC",
                                "backward_quantity": 800000,
                                "block_index": DP["default_block_index"],
                                "fee_paid": 7200,
                                "forward_asset": "XCP",
                                "forward_quantity": 100000000,
                                "id": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5_db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "match_expire_index": DP["default_block_index"] + 20,
                                "status": "pending",
                                "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "tx0_block_index": 310513,
                                "tx0_expiration": 2000,
                                "tx0_hash": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5",
                                "tx0_index": 492,
                                "tx1_address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "tx1_block_index": DP["default_block_index"],
                                "tx1_expiration": 10,
                                "tx1_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx1_index": DP["default_tx_index"],
                            },
                        },
                    ],
                },
                {
                    "comment": "order 7",
                    "in": (
                        {
                            "fee": 10000,
                            "btc_amount": 0,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "tx_index": DP["default_tx_index"],
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "supported": 1,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x06B,@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\n\x00\x00\x00\x00\x00\r\xbb\xa0",
                            "destination": "",
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 900000,
                                "fee_required_remaining": 900000,
                                "get_asset": "BTC",
                                "get_quantity": 50000000,
                                "get_remaining": 50000000,
                                "give_asset": "XCP",
                                "give_quantity": 105000000,
                                "give_remaining": 105000000,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "open",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "expiration": 10,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "quantity": 105000000,
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            },
                        },
                    ],
                },
                {
                    "comment": "order 8",
                    "in": (
                        {
                            "btc_amount": 0,
                            "fee": 10000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "",
                            "tx_hash": "0ec7da68a67e165693afd6c97566f8f509d302bceec8d1be0100335718a40fe5",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x03:>\x7f\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x00\x00\x00\x00\x00\r\xbb\xa0",
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "supported": 1,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                        },
                    ),
                    "records": [
                        {
                            "table": "orders",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "expiration": 10,
                                "expire_index": DP["default_block_index"] + 10,
                                "fee_provided": 10000,
                                "fee_provided_remaining": 10000,
                                "fee_required": 900000,
                                "fee_required_remaining": 900000,
                                "get_asset": "XCP",
                                "get_quantity": 100000000,
                                "get_remaining": 100000000,
                                "give_asset": "MAXI",
                                "give_quantity": 9223372036854775807,
                                "give_remaining": 9223372036854775807,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "open",
                                "tx_hash": "0ec7da68a67e165693afd6c97566f8f509d302bceec8d1be0100335718a40fe5",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "open order",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "MAXI",
                                "block_index": DP["default_block_index"],
                                "event": "0ec7da68a67e165693afd6c97566f8f509d302bceec8d1be0100335718a40fe5",
                                "quantity": 9223372036854775807,
                            },
                        },
                    ],
                },
                {
                    "comment": "order shouldn't be inserted because fee_required is > MAX_INT",
                    "in": (
                        {
                            "btc_amount": 0,
                            "fee": 10000,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "",
                            "tx_hash": "0ec7da68a67e165693afd6c97566f8f509d302bceec8d1be0100335718a40fe5",
                            "tx_index": DP["default_tx_index"],
                            "data": b"\x00\x00\x00\n\x00\x00\x00\x00\x00\x03:>\x7f\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x05\xf5\xe1\x00\x00\n\x80\x00\x00\x00\x00\x00\x00\x00",
                            "block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
                            "supported": 1,
                            "block_time": 155409000,
                            "block_index": DP["default_block_index"],
                        },
                    ),
                    "records": [
                        {
                            "not": True,  # NOT
                            "table": "orders",
                            "values": {
                                "tx_hash": "0ec7da68a67e165693afd6c97566f8f509d302bceec8d1be0100335718a40fe5"
                            },
                        },
                    ],
                },
            ],
            "expire": [{"in": (DP["default_block_index"] - 1,), "out": None}],
        },
        "sweep": {
            "validate": [
                {"in": (ADDR[6], ADDR[5], 1, None, DP["burn_start"]), "out": ([], 50000000.0)},
                {"in": (ADDR[6], ADDR[5], 2, None, DP["burn_start"]), "out": ([], 50000000.0)},
                {"in": (ADDR[6], ADDR[5], 3, None, DP["burn_start"]), "out": ([], 50000000.0)},
                {"in": (ADDR[6], ADDR[5], 1, "test", DP["burn_start"]), "out": ([], 50000000.0)},
                {"in": (ADDR[6], ADDR[5], 1, b"test", DP["burn_start"]), "out": ([], 50000000.0)},
                {
                    "in": (ADDR[6], ADDR[5], 0, None, DP["burn_start"]),
                    "out": (["must specify which kind of transfer in flags"], 50000000.0),
                },
                {
                    "in": (ADDR[6], ADDR[6], 1, None, DP["burn_start"]),
                    "out": (["destination cannot be the same as source"], 50000000.0),
                },
                {
                    "in": (ADDR[6], ADDR[5], 8, None, DP["burn_start"]),
                    "out": (["invalid flags 8"], 50000000.0),
                },
                {
                    "in": (
                        ADDR[6],
                        ADDR[5],
                        1,
                        "012345678900123456789001234567890012345",
                        DP["burn_start"],
                    ),
                    "out": (["memo too long"], 50000000.0),
                },
                {
                    "in": (ADDR[7], ADDR[5], 1, None, DP["burn_start"]),
                    "out": (
                        ["insufficient XCP balance for sweep. Need 0.5 XCP for antispam fee"],
                        50000000.0,
                    ),
                },
                {
                    "in": (ADDR[8], ADDR[5], 1, None, DP["burn_start"]),
                    "out": (
                        ["insufficient XCP balance for sweep. Need 0.5 XCP for antispam fee"],
                        50000000.0,
                    ),
                },
            ],
            "compose": [
                {
                    "in": (ADDR[6], ADDR[5], 1, None),
                    "out": (
                        "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        [],
                        b"\x00\x00\x00\x04o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x01",
                    ),
                },
                {
                    "in": (ADDR[6], ADDR[5], 2, None),
                    "out": (
                        "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        [],
                        b"\x00\x00\x00\x04o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x02",
                    ),
                },
                {
                    "in": (ADDR[6], ADDR[5], 3, None),
                    "out": (
                        "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        [],
                        b"\x00\x00\x00\x04o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x03",
                    ),
                },
                {
                    "in": (ADDR[6], ADDR[5], 3, "test"),
                    "out": (
                        "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        [],
                        b"\x00\x00\x00\x04o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x03test",
                    ),
                },
                {
                    "in": (ADDR[6], ADDR[5], 7, "cafebabe"),
                    "out": (
                        "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        [],
                        b"\x00\x00\x00\x04o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x07\xca\xfe\xba\xbe",
                    ),
                },
                {
                    "in": (ADDR[8], ADDR[5], 1, None),
                    "error": (
                        exceptions.ComposeError,
                        ["insufficient XCP balance for sweep. Need 0.5 XCP for antispam fee"],
                    ),
                },
            ],
            "unpack": [
                {
                    "in": (
                        b"o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x01",
                    ),
                    "out": {"destination": ADDR[5], "flags": 1, "memo": None},
                },
                {
                    "in": (
                        b"o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x02",
                    ),
                    "out": {"destination": ADDR[5], "flags": 2, "memo": None},
                },
                {
                    "in": (
                        b"o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x03test",
                    ),
                    "out": {"destination": ADDR[5], "flags": 3, "memo": "test"},
                },
                {
                    "in": (
                        b"o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x07\xca\xfe\xba\xbe",
                    ),
                    "out": {"destination": ADDR[5], "flags": 7, "memo": b"\xca\xfe\xba\xbe"},
                },
            ],
            "parse": [
                {
                    "mock_protocol_changes": {"sweep_send": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": ADDR[6],
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 17630,
                            "tx_index": DP["default_tx_index"],
                            "destination": ADDR[5],
                            "data": b"\x00\x00\x00\x03o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x01",
                        },
                    ),
                    "records": [
                        {
                            "table": "sweeps",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[5],
                                "source": ADDR[6],
                                "status": "valid",
                                "flags": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[5],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "sweep",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 92899122099,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "sweep",
                                "address": ADDR[6],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 92899122099,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[5],
                                "asset": "LOCKEDPREV",
                                "block_index": DP["default_block_index"],
                                "calling_function": "sweep",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 1000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "sweep",
                                "address": ADDR[6],
                                "asset": "LOCKEDPREV",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 1000,
                            },
                        },
                    ],
                },
                {
                    "mock_protocol_changes": {"sweep_send": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": ADDR[6],
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 17630,
                            "tx_index": DP["default_tx_index"],
                            "destination": ADDR[5],
                            "data": b"\x00\x00\x00\x03o\x9c\x8d\x1fT\x05E\x1d\xe6\x07\x0b\xf1\xdb\x86\xabj\xcc\xb4\x95\xb6%\x02",
                        },
                    ),
                    "records": [
                        {
                            "table": "sweeps",
                            "values": {
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[5],
                                "source": ADDR[6],
                                "status": "valid",
                                "flags": 2,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "issuances",
                            "values": {
                                "quantity": 0,
                                "asset_longname": None,
                                "issuer": ADDR[5],
                                "status": "valid",
                                "locked": 0,
                                "asset": "LOCKEDPREV",
                                "fee_paid": 0,
                                "callable": 0,
                                "call_date": 0,
                                "call_price": 0.0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "description": "changed",
                                "divisible": 1,
                                "source": ADDR[6],
                                "block_index": DP["default_block_index"],
                                "tx_index": DP["default_tx_index"],
                                "transfer": True,
                            },
                        },
                    ],
                },
            ],
        },
        "api_v1": {
            "get_rows": [
                {
                    "in": ("balances", None, "AND", None, None, None, None, None, 1000, 0, True),
                    "out": None,
                },
                {
                    "in": ("balances", None, "barfoo", None, None, None, None, None, 1000, 0, True),
                    "error": (APIError, "Invalid filter operator (OR, AND)"),
                },
                {
                    "in": (None, None, "AND", None, None, None, None, None, 1000, 0, True),
                    "error": (APIError, "Unknown table"),
                },
                {
                    "in": (
                        "balances",
                        None,
                        "AND",
                        None,
                        "barfoo",
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "Invalid order direction (ASC, DESC)"),
                },
                {
                    "in": ("balances", None, "AND", None, None, None, None, None, 1000.0, 0, True),
                    "error": (APIError, "Invalid limit"),
                },
                {
                    "in": ("balances", None, "AND", None, None, None, None, None, 1001, 0, True),
                    "error": (APIError, "Limit should be lower or equal to 1000"),
                },
                {
                    "in": ("balances", None, "AND", None, None, None, None, None, 1000, 0.0, True),
                    "error": (APIError, "Invalid offset"),
                },
                {
                    "in": ("balances", None, "AND", "*", None, None, None, None, 1000, 0, True),
                    "error": (APIError, "Invalid order_by, must be a field name"),
                },
                {
                    "in": ("balances", [0], "AND", None, None, None, None, None, 1000, 0, True),
                    "error": (APIError, "Unknown filter type"),
                },
                {
                    "in": (
                        "balances",
                        {"field": "bar", "op": "="},
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "A specified filter is missing the 'value' field"),
                },
                {
                    "in": (
                        "balances",
                        {"field": "bar", "op": "=", "value": {}},
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "Invalid value for the field 'bar'"),
                },
                {
                    "in": (
                        "balances",
                        {"field": "bar", "op": "=", "value": [0, 2]},
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "Invalid value for the field 'bar'"),
                },
                {
                    "in": (
                        "balances",
                        {"field": "bar", "op": "AND", "value": 0},
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "Invalid operator for the field 'bar'"),
                },
                {
                    "in": (
                        "balances",
                        {"field": "bar", "op": "=", "value": 0, "case_sensitive": 0},
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "case_sensitive must be a boolean"),
                },
                {
                    "comment": "standard send with no memo",
                    "in": (
                        "sends",
                        [{"field": "block_index", "op": "=", "value": "310496"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 497,
                            "tx_hash": "84b4bd0c150568ee571bf8ed214bea317df588eaebea3daa91bea38103fedf11",
                            "block_index": 310496,
                            "source": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                            "destination": "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 92945878046,
                            "status": "valid",
                            "memo": None,
                            "memo_hex": None,
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "with memo",
                    "in": (
                        "sends",
                        [{"field": "block_index", "op": "=", "value": "310481"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 482,
                            "tx_hash": "7821095a0f835691e8c3989d90542a16b326d77323408082e9d0ac4c3d04e121",
                            "block_index": 310481,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "hello",
                            "memo_hex": "68656c6c6f",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "search by memo (text)",
                    "in": (
                        "sends",
                        [{"field": "memo", "op": "=", "value": "hello"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 482,
                            "tx_hash": "7821095a0f835691e8c3989d90542a16b326d77323408082e9d0ac4c3d04e121",
                            "block_index": 310481,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "hello",
                            "memo_hex": "68656c6c6f",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "search by memo (LIKE text)",
                    "in": (
                        "sends",
                        [{"field": "memo", "op": "LIKE", "value": "%ell%"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 482,
                            "tx_hash": "7821095a0f835691e8c3989d90542a16b326d77323408082e9d0ac4c3d04e121",
                            "block_index": 310481,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "hello",
                            "memo_hex": "68656c6c6f",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "search by memo hex",
                    "in": (
                        "sends",
                        [{"field": "memo_hex", "op": "=", "value": "68656C6C6F"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 482,
                            "tx_hash": "7821095a0f835691e8c3989d90542a16b326d77323408082e9d0ac4c3d04e121",
                            "block_index": 310481,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "hello",
                            "memo_hex": "68656c6c6f",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "search by memo hex",
                    "in": (
                        "sends",
                        [{"field": "memo_hex", "op": "=", "value": "68656c6c6f"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 482,
                            "tx_hash": "7821095a0f835691e8c3989d90542a16b326d77323408082e9d0ac4c3d04e121",
                            "block_index": 310481,
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "hello",
                            "memo_hex": "68656c6c6f",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
                {
                    "comment": "search with invalid memo hex",
                    "in": (
                        "sends",
                        [{"field": "memo_hex", "op": "=", "value": "badx"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "error": (APIError, "Invalid memo_hex value"),
                },
                {
                    "comment": "search by memo hex",
                    "in": (
                        "sends",
                        [{"field": "memo_hex", "op": "=", "value": "fade0001"}],
                        "AND",
                        None,
                        None,
                        None,
                        None,
                        None,
                        1000,
                        0,
                        True,
                    ),
                    "out": [
                        {
                            "tx_index": 483,
                            "tx_hash": "df7c7591bbfffc8c7e172e90effdff069c9742c13ae7b1066214bcbb9c2f6883",
                            "block_index": 310482,
                            "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "source_address": None,
                            "destination_address": None,
                            "asset": "XCP",
                            "quantity": 100000000,
                            "status": "valid",
                            "memo": "",
                            "memo_hex": "fade0001",
                            "msg_index": 0,
                            "fee_paid": 0,
                            "send_type": "send",
                        }
                    ],
                },
            ],
        },
        "script": {
            "validate": [
                {
                    "comment": "valid bitcoin address",
                    "in": ("mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6",),
                    "out": None,
                },
                {"comment": "valid bitcoin P2SH address", "in": (P2SH_ADDR[0],), "out": None},
                {
                    "comment": "invalid bitcoin address: bad checksum",
                    "in": ("mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP7",),
                    "error": (script.Base58Error, "invalid base58 string"),
                },
                {
                    "comment": "valid multi‐sig",
                    "in": (
                        "1_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                    ),
                    "out": None,
                },
                {
                    "comment": "invalid multi‐sig with P2SH addres",
                    "in": ("1_" + P2SH_ADDR[0] + "_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",),
                    "error": (
                        script.MultiSigAddressError,
                        "Invalid PubKeyHashes. Multi‐signature address must use PubKeyHashes, not public keys.",
                    ),
                },
            ],
            "scriptpubkey_to_address": [
                # "OP_DUP OP_HASH160 4838d8b3588c4c7ba7c1d06f866e9b3739c63037 OP_EQUALVERIFY OP_CHECKSIG"
                {
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x("76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac")
                        ),
                    ),
                    "out": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                },
                # "OP_DUP OP_HASH160 8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec OP_EQUALVERIFY OP_CHECKSIG"
                {
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x("76a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac")
                        ),
                    ),
                    "out": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                },
                # "1 035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe35 02309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17 0319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b977 3 OP_CHECKMULTISIG"
                {
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x(
                                "5121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae"
                            )
                        ),
                    ),
                    "out": "1_mjH9amw2tJrsrw76PVvCkCQ18V4pZCVtm5_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_mvgph5nejRWUVvbzyq7TU9ENpJyV97ua37_3",
                },
                {
                    "in": ("mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",),
                    "error": (exceptions.DecodeError, "invalid script"),
                },
                {
                    "in": (
                        [
                            "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                            "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                        ],
                    ),
                    "error": (exceptions.DecodeError, "invalid script"),
                },
                {
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x("6a53657466697665207361797320686921")
                        ),
                    ),
                    "error": (exceptions.DecodeError, "invalid script"),
                },
                {
                    "comment": "p2pkh",
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x("76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac")
                        ),
                    ),
                    "out": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                },
                {
                    "comment": "p2sh",
                    "in": (
                        bitcoinlib.core.CScript(
                            bitcoinlib.core.x("a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87")
                        ),
                    ),
                    "out": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                },
            ],
            "get_asm": [{"in": (b"",), "error": (exceptions.DecodeError, "empty output")}],
            "base58_encode": [
                {
                    "comment": "random bytes",
                    "in": (b"\x82\xe3\x069\x16\x17I\x12S\x81\xeaQC\xa6J\xac",),
                    "out": "HARXEpbq7gJQGcSVUtubYo",
                },
                {
                    "in": (b"\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee",),
                    "out": "qb3y62fmEEVTPySXPQ77WXok6H",
                },
            ],
            "base58_check_encode": [
                {
                    "comment": "valid mainnet bitcoin address",
                    "in": ("010966776006953d5567439e5e39f86a0d273bee", b"\x00"),
                    "out": "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",
                },
                {
                    "comment": "valid mainnet bitcoin P2SH address",
                    "in": ("010966776006953d5567439e5e39f86a0d273bee", b"\x05"),
                    "out": "31nVrspaydBz8aMpxH9WkS2DuhgqS1fCuG",
                    # TODO }, {
                    #    'invalid mainnet bitcoin address: leading zero byte,
                    #    'in': ('SOMETHING', b'\x00'),
                    #    'error': (script.AddressError, 'encoded address does not decode properly')
                },
            ],
            "base58_check_decode": [
                {
                    "comment": "valid mainnet bitcoin address",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM", b"\x00"),
                    "out": b"\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee",
                },
                {
                    "comment": "valid mainnet bitcoin address that contains a padding byte",
                    "in": ("13PGb7v3nmTDugLDStRJWXw6TzsNLUKJKC", b"\x00"),
                    "out": b"\x1a&jGxV\xea\xd2\x9e\xcb\xe6\xaeQ\xad:,\x8dG<\xf4",
                },
                {
                    "comment": "valid mainnet bitcoin P2SH address",
                    "in": ("31nVrspaydBz8aMpxH9WkS2DuhgqS1fCuG", b"\x05"),
                    "out": b"\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee",
                },
                {
                    "comment": "valid mainnet bitcoin address that contains a padding byte, checked against incorrect version byte",
                    "in": ("13PGb7v3nmTDugLDStRJWXw6TzsNLUKJKC", b"\x05"),
                    "error": (script.VersionByteError, "incorrect version byte"),
                },
                {
                    "comment": "valid mainnet bitcoin P2SH address, checked against incorrect version byte",
                    "in": ("31nVrspaydBz8aMpxH9WkS2DuhgqS1fCuG", b"\x00"),
                    "error": (script.VersionByteError, "incorrect version byte"),
                },
                {
                    "comment": "wrong version byte",
                    "in": ("26UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM", b"\x00"),
                    "error": (script.Base58Error, "invalid base58 string"),
                },
                {
                    "comment": "invalid mainnet bitcoin address: bad checksum",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvN", b"\x00"),
                    "error": (script.Base58Error, "invalid base58 string"),
                },
                {
                    "comment": "valid testnet bitcoin address that we use in many tests",
                    "in": (ADDR[0], b"\x6f"),
                    "out": b"H8\xd8\xb3X\x8cL{\xa7\xc1\xd0o\x86n\x9b79\xc607",
                },
                {
                    "comment": "invalid mainnet bitcoin address: invalid character",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjv0", b"\x00"),
                    "error": (script.Base58Error, "invalid base58 string"),
                },
            ],
            # base58_decode is the raw decoding, we use the test cases from base58_check_decode
            "base58_decode": [
                {
                    "comment": "valid mainnet bitcoin address",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",),
                    "out": b"\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf6",
                },
                {
                    "comment": "valid mainnet bitcoin address that contains a padding byte",
                    "in": ("13PGb7v3nmTDugLDStRJWXw6TzsNLUKJKC",),
                    "out": b"\x00\x1a&jGxV\xea\xd2\x9e\xcb\xe6\xaeQ\xad:,\x8dG<\xf4\x07eG#",
                },
                {
                    "comment": "wrong version byte",
                    "in": ("26UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",),
                    "out": b"\x0c\x01\x86\xaa\xbd\xa1\xd2\xdaJ\xf2\xd4\xbb\xe5=N\xe2\x08\xa6\x8eo\xd6\x19g\xf6",
                },
                {
                    "comment": "invalid mainnet bitcoin address: bad checksum",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvN",),
                    "out": b"\x00\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee\xd6\x19g\xf7",
                },
                {
                    "comment": "valid testnet bitcoin address that we use in many tests",
                    "in": (ADDR[0],),
                    "out": b"oH8\xd8\xb3X\x8cL{\xa7\xc1\xd0o\x86n\x9b79\xc607\x98!\xc4U",
                },
                {
                    "comment": "invalid mainnet bitcoin address: invalid character",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjv0",),
                    "error": (script.Base58Error, "Not a valid Base58 character: ‘0’"),
                },
            ],
            # base58_check_decode_parts is the raw decoding and splitting, we use the test cases from base58_check_decode
            "base58_check_decode_parts": [
                {
                    "comment": "valid mainnet bitcoin address",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",),
                    "out": (b"\x00", b"\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee", b"\xd6\x19g\xf6"),
                },
                {
                    "comment": "valid mainnet bitcoin address that contains a padding byte",
                    "in": ("13PGb7v3nmTDugLDStRJWXw6TzsNLUKJKC",),
                    "out": (
                        b"\x00",
                        b"\x1a&jGxV\xea\xd2\x9e\xcb\xe6\xaeQ\xad:,\x8dG<\xf4",
                        b"\x07eG#",
                    ),
                },
                {
                    "comment": "wrong version byte",
                    "in": ("26UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",),
                    "out": (
                        b"\x0c",
                        b"\x01\x86\xaa\xbd\xa1\xd2\xdaJ\xf2\xd4\xbb\xe5=N\xe2\x08\xa6\x8eo",
                        b"\xd6\x19g\xf6",
                    ),
                },
                {
                    "comment": "invalid mainnet bitcoin address: bad checksum",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvN",),
                    "out": (b"\x00", b"\x01\tfw`\x06\x95=UgC\x9e^9\xf8j\r';\xee", b"\xd6\x19g\xf7"),
                },
                {
                    "comment": "valid testnet bitcoin address that we use in many tests",
                    "in": (ADDR[0],),
                    "out": (
                        b"o",
                        b"H8\xd8\xb3X\x8cL{\xa7\xc1\xd0o\x86n\x9b79\xc607",
                        b"\x98!\xc4U",
                    ),
                },
                {
                    "comment": "invalid mainnet bitcoin address: invalid character",
                    "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjv0",),
                    "error": (script.Base58Error, "Not a valid Base58 character: ‘0’"),
                },
            ],
            "is_multisig": [
                {"comment": "mono‐sig", "in": ("16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",), "out": False},
                {
                    "comment": "multi‐sig",
                    "in": (
                        "1_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                    ),
                    "out": True,
                },
            ],
            "is_fully_valid": [
                {
                    "comment": "fully valid compressed public key",
                    "in": (
                        b"\x03T\xdaT\x0f\xb2g;u\xe6\xc3\xc9\x94\xf8\n\xd0\xc8C\x16C\xba\xb2\x8c\xedx<\xd9@y\xbb\xe7$E",
                    ),
                    "out": True,
                },
                {
                    "comment": "not fully valid compressed public key: last byte decremented; not on curve",
                    "in": (
                        b"\x03T\xdaT\x0f\xb2g;u\xe6\xc3\xc9\x94\xf8\n\xd0\xc8C\x16C\xba\xb2\x8c\xedx<\xd9@y\xbb\xe7$D",
                    ),
                    "out": False,
                },
                {
                    "comment": "invalid compressed public key: first byte not `\x02` or `\x03`",
                    "in": (
                        b"\x01T\xdaT\x0f\xb2g;u\xe6\xc3\xc9\x94\xf8\n\xd0\xc8C\x16C\xba\xb2\x8c\xedx<\xd9@y\xbb\xe7$E",
                    ),
                    "out": False,
                },
            ],
            "make_canonical": [
                {
                    "in": (
                        "1_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_2",
                    ),  # TODO: Pubkeys out of order
                    "out": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                },
                {
                    "in": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                    ),  # TODO: Pubkeys out of order
                    "out": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                },
                {
                    "comment": "mono‐sig",
                    "in": ("mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",),
                    "out": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                },
                {"comment": "mono‐sig P2SH", "in": (P2SH_ADDR[0],), "out": P2SH_ADDR[0]},
                {
                    "in": (
                        "1_02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                    ),
                    "error": (
                        script.MultiSigAddressError,
                        "Multi‐signature address must use PubKeyHashes, not public keys.",
                    ),
                },
            ],
            "test_array": [
                {
                    "in": (
                        "1",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        2,
                    ),
                    "out": None,
                },
                {
                    "in": (
                        "Q",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        2,
                    ),
                    "error": (script.MultiSigAddressError, "Signature values not integers."),
                },
                {
                    "in": (
                        "1",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        None,
                    ),
                    "error": (script.MultiSigAddressError, "Signature values not integers."),
                },
                {
                    "in": (
                        "0",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        2,
                    ),
                    "error": (script.MultiSigAddressError, "Invalid signatures_required."),
                },
                {
                    "in": (
                        "4",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        2,
                    ),
                    "error": (script.MultiSigAddressError, "Invalid signatures_required."),
                },
                {
                    "in": (
                        "1",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        1,
                    ),
                    "error": (script.MultiSigAddressError, "Invalid signatures_possible."),
                },
                {
                    "in": (
                        "2",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        4,
                    ),
                    "error": (script.MultiSigAddressError, "Invalid signatures_possible."),
                },
                {
                    "in": (
                        "1",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_2",
                        ],
                        2,
                    ),
                    "error": (
                        script.MultiSigAddressError,
                        "Invalid characters in pubkeys/pubkeyhashes.",
                    ),
                },
                {
                    "in": (
                        "3",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        3,
                    ),
                    "error": (
                        script.InputError,
                        "Incorrect number of pubkeys/pubkeyhashes in multi‐signature address.",
                    ),
                },
            ],
            "construct_array": [
                {
                    "in": (
                        "1",
                        [
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        ],
                        2,
                    ),
                    "out": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                }
            ],
            "extract_array": [
                {
                    "in": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                    ),
                    "out": (
                        1,
                        [
                            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        ],
                        2,
                    ),
                }
            ],
            "pubkeyhash_array": [
                {
                    "in": (
                        "1_xxxxxxxxxxxWRONGxxxxxxxxxxxxxxxxxx_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                    ),
                    "error": (
                        script.MultiSigAddressError,
                        "Invalid PubKeyHashes. Multi‐signature address must use PubKeyHashes, not public keys.",
                    ),
                },
                {
                    "in": (
                        "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                    ),
                    "out": [
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    ],
                },
            ],
            "is_pubkeyhash": [
                {
                    "comment": "valid bitcoin address",
                    "in": ("mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6",),
                    "out": True,
                },
                {
                    "comment": "valid P2SH bitcoin address, but is_pubkeyhash specifically checks for valid P2PKH address",
                    "in": (P2SH_ADDR[0],),
                    "out": False,
                },
                {
                    "comment": "invalid checksum",
                    "in": ("mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP7",),
                    "out": False,
                },
                {
                    "comment": "invalid version byte",
                    "in": ("LnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6",),
                    "out": False,
                },
            ],
            "make_pubkeyhash": [
                {
                    "comment": "mono‐sig",
                    "in": ("02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558",),
                    "out": "mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6",
                },
                {
                    "comment": "multi‐sig, with pubkey in first position and pubkeyhash in second",
                    "in": (
                        "1_02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                    ),
                    "out": "1_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                },
            ],
            "extract_pubkeys": [
                {"comment": "pubkeyhash", "in": ("mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6",), "out": []},
                {"comment": "p2sh", "in": (P2SH_ADDR[0],), "out": []},
                {
                    "comment": "mono‐sig",
                    "in": ("02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558",),
                    "out": ["02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558"],
                },
                {
                    "comment": "multi‐sig, with pubkey in first position and pubkeyhash in second",
                    "in": (
                        "1_02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558_mnMrocns5kBjPZxRxXb5A1gx7gAoRZWPP6_2",
                    ),
                    "out": ["02513522cbf07b0bd553b0d8f8414c476c9275334fd3edfa368386412e3a193558"],
                },
            ],
        },
        "util": {
            "api": [
                {
                    "comment": "burn 1",
                    "in": (
                        "create_burn",
                        {
                            "source": ADDR[1],
                            "quantity": DP["burn_quantity"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce40000000000ffffffff02800bb203000000001976a914a11b66a67b3ff69671c8f82254099faf374b800e88acdad24302000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                },
                {
                    "comment": "send 1",
                    "in": (
                        "create_send",
                        {
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0322020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ace8030000000000006951210262415bf04af834423d3dd7ada4dc727a030865759f9fba5aee78c9ea71e58798210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aee253ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "send 2",
                    "in": (
                        "create_send",
                        {
                            "source": P2SH_ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                            "encoding": "multisig",
                            "dust_return_pubkey": False,
                            "regular_dust_size": DP["regular_dust_size"],
                        },
                    ),
                    "out": "02000000015001af2c4c3bc2c43b6233261394910d10fb157a082d9b3038c65f2d01e4ff200000000000ffffffff0336150000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ace8030000000000006951210397b51de78b0f3a171f5ed27fff56d17dcba739c8b00035c8bbb9c380fdc4ed1321036932bcbeac2a4d8846b7feb4bf93b2b88efd02f2d8dc1fc0067bcc972257e391210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aef6c2f5050000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e8700000000",
                },
                {
                    "comment": "issuance 1",
                    "in": (
                        "create_issuance",
                        {
                            "source": ADDR[0],
                            "transfer_destination": None,
                            "asset": "BSSET",
                            "quantity": 1000,
                            "divisible": True,
                            "description": "",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210358415bf04af834423d3dd7adb2dc727a03086e897d9fba5aee7a331919e487d6210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "issuance 2",
                    "in": (
                        "create_issuance",
                        {
                            "source": ADDR[0],
                            "transfer_destination": ADDR[1],
                            "asset": "DIVISIBLE",
                            "quantity": 0,
                            "divisible": True,
                            "description": "",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0322020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ace8030000000000006951210258415bf04af834423d3dd7adb2dc727aa153863ef89fba5aee7a331af1e4874b210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aee253ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "order 1",
                    "in": (
                        "create_order",
                        {
                            "source": ADDR[0],
                            "give_asset": "BTC",
                            "give_quantity": DP["small"],
                            "get_asset": "XCP",
                            "get_quantity": DP["small"] * 2,
                            "expiration": DP["expiration"],
                            "fee_required": 0,
                            "fee_provided": DP["fee_provided"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210348415bf04af834423d3dd7adaedc727a030865759e9fba5aee78c9ea71e5870f210354da540fb2673b75e6c3c994f80ad0c8431643bab28ced783cd94079bbe72445210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "order 2",
                    "in": (
                        "create_order",
                        {
                            "source": ADDR[0],
                            "give_asset": "XCP",
                            "give_quantity": round(DP["small"] * 2.1),
                            "get_asset": "BTC",
                            "get_quantity": DP["small"],
                            "expiration": DP["expiration"],
                            "fee_required": DP["fee_required"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210248415bf04af834423d3dd7adaedc727a030865759f9fba5aee7c7136b1e58715210354da540fb2663b75e6c3ce9be98ad0c8431643bab28156d83cd94079bbe72460210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "burn 2",
                    "in": (
                        "create_burn",
                        {
                            "source": MULTISIGADDR[0],
                            "quantity": int(DP["quantity"] / 2),
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff0280f0fa02000000001976a914a11b66a67b3ff69671c8f82254099faf374b800e88ac94ebfa02000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "send 3",
                    "in": (
                        "create_send",
                        {
                            "source": ADDR[0],
                            "destination": MULTISIGADDR[0],
                            "asset": "XCP",
                            "quantity": DP["quantity"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff03e8030000000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752aee8030000000000006951210362415bf04af834423d3dd7ada4dc727a030865759f9fba5aee7fc6fbf1e5875a210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aea84dea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "send 4",
                    "in": (
                        "create_send",
                        {
                            "source": MULTISIGADDR[0],
                            "destination": ADDR[0],
                            "asset": "XCP",
                            "quantity": DP["quantity"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff0322020000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ace8030000000000006951210334caf7ca87f0fd78a01d9a0d68221e55beef3722da8be72d254dd351c26108892102bc14528340c27d005aa9e2913fd8c032ffa94625307a450077125d580099b57d210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae5ad1f505000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "send 5",
                    "in": (
                        "create_send",
                        {
                            "source": MULTISIGADDR[0],
                            "destination": MULTISIGADDR[1],
                            "asset": "XCP",
                            "quantity": DP["quantity"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff03e8030000000000004751210378ee11c3fb97054877a809ce083db292b16d971bcdc6aa4c8f92087133729d8b210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752aee8030000000000006951210334caf7ca87f0fd78a01d9a0d68221e55beef3722da8be72d254dd351c26108892102bc14528340c27d005aa9e2913fd8c032ffa94625307a450077125d580099b57d210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae20cbf505000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "issuance 3",
                    "in": (
                        "create_issuance",
                        {
                            "source": MULTISIGADDR[0],
                            "transfer_destination": None,
                            "asset": "BSSET",
                            "quantity": 1000,
                            "divisible": True,
                            "description": "",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff02e803000000000000695121020ecaf7ca87f0fd78a01d9a0d7e221e55beef3cde388be72d254826b32a6008382102bc14528340c27d005aa9e2913fd8c032ffa94625307a450077125d580099b57d210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aeb8d3f505000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "issuance 4",
                    "in": (
                        "create_issuance",
                        {
                            "source": ADDR[0],
                            "transfer_destination": MULTISIGADDR[0],
                            "asset": "DIVISIBLE",
                            "quantity": 0,
                            "divisible": True,
                            "description": "",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff03e8030000000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752aee8030000000000006951210258415bf04af834423d3dd7adb2dc727aa153863ef89fba5aee7a331af1e4874b210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aea84dea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "issuance 5",
                    "in": (
                        "create_issuance",
                        {
                            "source": ADDR[0],
                            "asset": f"A{2 ** 64 - 1}",
                            "quantity": 1000,
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210255415bf04af834423d3dd7adb2238d85fcf79a8a619fba5aee7a331919e4870d210254da540fb2663b75268d992d550ad0c2431643bab28ced783cd94079bbe7244d210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "order 3",
                    "in": (
                        "create_order",
                        {
                            "source": MULTISIGADDR[0],
                            "give_asset": "BTC",
                            "give_quantity": DP["small"],
                            "get_asset": "XCP",
                            "get_quantity": DP["small"] * 2,
                            "expiration": DP["expiration"],
                            "fee_required": 0,
                            "fee_provided": DP["fee_provided"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff02e803000000000000695121021ecaf7ca87f0fd78a01d9a0d62221e55beef3722db8be72d254adc40426108d02103bc14528340c37d005aa9e764ded8c038ffa94625307a450077125d580099b53b210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aeb8d3f505000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "order 4",
                    "in": (
                        "create_order",
                        {
                            "source": MULTISIGADDR[0],
                            "give_asset": "XCP",
                            "give_quantity": round(DP["small"] * 2.1),
                            "get_asset": "BTC",
                            "get_quantity": DP["small"],
                            "expiration": DP["expiration"],
                            "fee_required": DP["fee_required"],
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001051511b66ba309e3dbff1fde22aefaff4190675235a010a5c6acb1e43da8005f0000000000ffffffff02e803000000000000695121031ecaf7ca87f0fd78a01d9a0d62221e55beef3722da8be72d254e649c8261083d2102bc14528340c27d005aa9e06bcf58c038ffa946253077fea077125d580099b5bb210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053aeb8d3f505000000004751210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97752ae00000000",
                },
                {
                    "comment": "dividend 1",
                    "in": (
                        "create_dividend",
                        {
                            "source": ADDR[0],
                            "quantity_per_unit": DP["quantity"],
                            "asset": "DIVISIBLE",
                            "dividend_asset": "XCP",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e803000000000000695121035a415bf04af834423d3dd7ad96dc727a030d90949e9fba5a4c21d05197e58735210254da540fb2673b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe7246f210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "dividend 2",
                    "in": (
                        "create_dividend",
                        {
                            "source": ADDR[0],
                            "quantity_per_unit": 1,
                            "asset": "NODIVISIBLE",
                            "dividend_asset": "XCP",
                            "encoding": "multisig",
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e803000000000000695121025a415bf04af834423d3dd7ad96dc727a030865759f9fbc9036a64c1197e587c8210254da540fb2673b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe7246f210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    # CIP 9 enhanced_send tests
                },
                {
                    "comment": "standard op return send",
                    "mock_protocol_changes": {"enhanced_sends": False},
                    "in": (
                        "create_send",
                        {
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0322020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000000000001e6a1c2a504df746f83442653dd7ada4dc727a030865749e9fba5aec80c39ad759ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "standard op return send (with API parameter)",
                    "mock_protocol_changes": {"enhanced_sends": True},
                    "in": (
                        "create_send",
                        {
                            "use_enhanced_send": False,
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0322020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000000000001e6a1c2a504df746f83442653dd7ada4dc727a030865749e9fba5aec80c39ad759ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "CIP 9 enhanced_send (op_return)",
                    "mock_protocol_changes": {"enhanced_sends": True},
                    "in": (
                        "create_send",
                        {
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff020000000000000000336a312a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e68edbc79e78ed45723c1072c38aededa458f95fa205cea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "CIP 9 enhanced_send with memo",
                    "mock_protocol_changes": {"enhanced_sends": True},
                    "in": (
                        "create_send",
                        {
                            "memo": "hello",
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff020000000000000000386a362a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e68edbc79e78ed45723c1072c38aededa458f95fa2bdfdee082115cea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "CIP 9 enhanced_send with memo as hex",
                    "mock_protocol_changes": {"enhanced_sends": True},
                    "in": (
                        "create_send",
                        {
                            "memo": "0102030405",
                            "memo_is_hex": True,
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff020000000000000000386a362a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e68edbc79e78ed45723c1072c38aededa458f95fa42b8b188e8115cea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                },
                {
                    "comment": "CIP 9 enhanced_send before enabled",
                    "mock_protocol_changes": {"enhanced_sends": False},
                    "in": (
                        "create_send",
                        {
                            "memo": "0102030405",
                            "memo_is_hex": True,
                            "source": ADDR[0],
                            "destination": ADDR[1],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "error": (
                        RPCError,
                        "Error composing send transaction via API: enhanced sends are not enabled (-32001)",
                    ),
                },
                {
                    "comment": "CIP 9 enhanced send to a REQUIRE_MEMO address without memo",
                    "mock_protocol_changes": {
                        "enhanced_sends": True,
                        "options_require_memo": True,
                    },
                    "in": (
                        "create_send",
                        {
                            "source": ADDR[0],
                            "destination": ADDR[6],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "error": (
                        RPCError,
                        "Error composing send transaction via API: ['destination requires memo'] (-32001)",
                    ),
                },
                {
                    "comment": "CIP 9 enhanced send to a REQUIRE_MEMO address with memo",
                    "mock_protocol_changes": {
                        "enhanced_sends": True,
                        "options_require_memo": True,
                    },
                    "in": (
                        "create_send",
                        {
                            "memo": "0102030405",
                            "memo_is_hex": True,
                            "source": ADDR[0],
                            "destination": ADDR[6],
                            "asset": "XCP",
                            "quantity": DP["small"],
                        },
                    ),
                    "out": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff020000000000000000386a362a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e56174ca4a68af644972baced7a9ef02e467cb63542b8b188e8115cea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    # get_tx_info API method
                },
                {
                    "comment": "get_tx_info for a legacy send",
                    "in": (
                        "get_tx_info",
                        {
                            "tx_hex": "01000000"
                            + "01"
                            + "c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae"
                            + "00000000"
                            + "19"
                            + "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"
                            + "ffffffff"
                            + "03"
                            + "2202000000000000"
                            + "19"
                            + "76a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac"
                            + "0000000000000000"
                            + "1e"
                            + "6a1c2a504df746f83442653dd7ada4dc727a030865749e9fba5aec80c39a"
                            + "4343ea0b00000000"
                            + "19"
                            + "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"
                            + "00000000"
                        },
                    ),
                    "out": [
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        546,
                        6575,
                        "0000000000000000000000010000000002faf080",
                    ],
                },
                {
                    "comment": "get_tx_info for an enhanced send",
                    "mock_protocol_changes": {
                        "enhanced_sends": True,
                    },
                    "in": (
                        "get_tx_info",
                        {
                            "tx_hex": "01000000"
                            + "01"
                            + "c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae"
                            + "00000000"
                            + "19"
                            + "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"
                            + "ffffffff"
                            + "02"
                            + "0000000000000000"
                            + "33"
                            + "6a312a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e68edbc79e78ed45723c1072c38aededa458f95fa"
                            + "aa46ea0b00000000"
                            + "19"
                            + "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"
                            + "00000000"
                        },
                    ),
                    "out": [
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "",
                        0,
                        6250,
                        "0000000200000000000000010000000002faf0806f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec",
                    ],
                    # unpack API method
                },
                {
                    "comment": "Unpack a data hex for a legacy send",
                    "in": ("unpack", {"data_hex": "0000000000000000000000010000000002faf080"}),
                    "out": [0, {"asset": "XCP", "quantity": 50000000}],
                },
                {
                    "comment": "Unpack a data hex for an enahcned send",
                    "mock_protocol_changes": {"enhanced_sends": True, "options_require_memo": True},
                    "in": (
                        "unpack",
                        {
                            "data_hex": "0000000200000000000000010000000002faf0806f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec"
                        },
                    ),
                    "out": [
                        2,
                        {
                            "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "asset": "XCP",
                            "memo": None,
                            "quantity": 50000000,
                        },
                    ],
                },
            ],
            "dhash_string": [
                {
                    "in": ("foobar",),
                    "out": "3f2c7ccae98af81e44c0ec419659f50d8b7d48c681e5d57fc747d0461e42dda1",
                }
            ],
            "hexlify": [
                {
                    "in": (b"\x00\x00\x00\x14\x00\x00\x00\x00\x00\x0b\xfc\xe3",),
                    "out": "0000001400000000000bfce3",
                }
            ],
            "date_passed": [
                {
                    "comment": "date in the past, mock function overrides this one and always returns `False` in the test suite",
                    "in": ("1020720007",),
                    "out": False,
                },
                {
                    "comment": "date far in the future, mock function overrides this one and always returns `False` in the test suite",
                    "in": ("5520720007",),
                    "out": False,
                },
            ],
            "parse_subasset_from_asset_name": [
                {
                    "in": ("BADASSETx.child1",),
                    "error": (
                        exceptions.AssetNameError,
                        "parent asset name contains invalid character:",
                    ),
                },
                {
                    "in": ("TOOLONGASSETNAME.child1",),
                    "error": (exceptions.AssetNameError, "parent asset name too long"),
                },
                {
                    "in": ("BAD.child1",),
                    "error": (exceptions.AssetNameError, "parent asset name too short"),
                },
                {
                    "in": ("ABADPARENT.child1",),
                    "error": (exceptions.AssetNameError, "parent asset name starts with 'A'"),
                },
                {
                    "in": ("BTC.child1",),
                    "error": (exceptions.AssetNameError, "parent asset cannot be BTC"),
                },
                {
                    "in": ("XCP.child1",),
                    "error": (exceptions.AssetNameError, "parent asset cannot be XCP"),
                },
                {
                    "in": ("PARENT.",),
                    "error": (exceptions.AssetNameError, "subasset name too short"),
                },
                {
                    "in": ("PARENT." + ("1234567890" * 24) + "12345",),
                    "error": (exceptions.AssetNameError, "subasset name too long"),
                },
                {
                    "in": ("PARENT.child1&",),
                    "error": (
                        exceptions.AssetNameError,
                        "subasset name contains invalid character:",
                    ),
                },
                {
                    "in": ("PARENT.child1..foo",),
                    "error": (
                        exceptions.AssetNameError,
                        "subasset name contains consecutive periods",
                    ),
                },
                {
                    "comment": "numerics disallowed",
                    "in": ("A95428956661682177.subasset",),
                    "error": (
                        exceptions.AssetNameError,
                        "parent asset name too long",
                    ),
                },
                {
                    "comment": "numerics allowed",
                    "in": ("A95428956661682177.subasset", True),
                    "out": ("A95428956661682177", "A95428956661682177.subasset"),
                },
                {
                    "comment": "numerics allowed but too long",
                    "in": ("A123456789012345678901.subasset", True),
                    "error": (
                        exceptions.AssetNameError,
                        "parent asset name too long",
                    ),
                },
            ],
            "compact_subasset_longname": [
                {
                    "in": ("a.very.long.name",),
                    "out": binascii.unhexlify("132de2e856f9a630c2e2bc09"),
                },
                {"in": ("aaaa",), "out": binascii.unhexlify("04de95")},
                {"in": ("a",), "out": b"\x01"},
                {"in": ("b",), "out": b"\x02"},
            ],
            "expand_subasset_longname": [
                {
                    "in": (binascii.unhexlify("132de2e856f9a630c2e2bc09"),),
                    "out": "a.very.long.name",
                },
                {"in": (binascii.unhexlify("04de95"),), "out": "aaaa"},
                {"in": (b"\x01",), "out": "a"},
                {"in": (b"\x02",), "out": "b"},
                {
                    "in": (binascii.unhexlify("8e90a57dba99d3a77b0a2470b1816edb"),),
                    "out": "PARENT.a-zA-Z0-9.-_@!",
                },
            ],
            "enabled": [
                {"in": ("numeric_asset_names",), "out": True},
                {"in": ("foobar",), "error": (KeyError, "foobar")},
                {
                    "mock_protocol_changes": {"numeric_asset_names": False},
                    "in": ("numeric_asset_names",),
                    "out": False,
                },
            ],
        },
        "database": {
            "version": [{"in": (), "out": (config.VERSION_MAJOR, config.VERSION_MINOR)}],
            "update_version": [
                {
                    "in": (),
                    "records": [
                        {
                            "table": "pragma",
                            "field": "user_version",
                            "value": (config.VERSION_MAJOR * 1000) + config.VERSION_MINOR,
                        }
                    ],
                }
            ],
        },
        "message_type": {
            "unpack": [
                {
                    "in": (binascii.unhexlify("01deadbeef"), 310502),
                    "out": (1, binascii.unhexlify("deadbeef")),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (binascii.unhexlify("02deadbeef"), 310502),
                    "out": (2, binascii.unhexlify("deadbeef")),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (binascii.unhexlify("00000001deadbeef"), 310502),
                    "out": (1, binascii.unhexlify("deadbeef")),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (binascii.unhexlify("00000000deadbeef"), 310502),
                    "out": (0, binascii.unhexlify("deadbeef")),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (binascii.unhexlify("00"), 310502),
                    "out": (None, None),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (b"f0", 310502),
                    "out": (102, b"0"),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
            ],
            "pack": [
                {"in": (0, 300000), "out": binascii.unhexlify("00000000")},
                {"in": (1, 300000), "out": binascii.unhexlify("00000001")},
                {"in": (0, 310502), "out": binascii.unhexlify("00000000")},
                {
                    "in": (1, 310502),
                    "out": binascii.unhexlify("01"),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (2, 310502),
                    "out": binascii.unhexlify("02"),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
            ],
            "get_transaction_type": [
                {
                    "in": (b"CNTRPRTY00", "", [], 3000000),
                    "out": "unknown",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (b"[A95428957753448833|1", "", [], 3000000),
                    "out": "fairmint",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (None, "", ["txid:0"], 3000000),
                    "out": "utxomove",
                    "mock_protocol_changes": {"short_tx_type_id": True, "utxo_support": True},
                },
                {
                    "in": (None, "", [""], 3000000),
                    "out": "unknown",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (None, "", [""], 2900000),
                    "out": "dispense",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (b"eXCPMEME|25000000000|", "", [], 3000000),
                    "out": "attach",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (b"fbc1qcxlwq8x9fnhyhgywlnja35l7znt58tud9duqay", "", [], 3000000),
                    "out": "detach",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (
                        b"\x02\x00>\xc7\xd9>|n\x19\x00\x00\x00\x00\x00\x00\x00P\x00%?\x9e\x96I\xb3\xf9u\x15$\xb2\x90\xf93Pra\x0c\xcc\x01",
                        "",
                        [],
                        3000000,
                    ),
                    "out": "enhanced_send",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                },
                {
                    "in": (None, config.UNSPENDABLE_TESTNET, [""], 3000000),
                    "out": "burn",
                    "mock_protocol_changes": {"short_tx_type_id": True, "utxo_support": True},
                },
                {
                    "in": (None, config.UNSPENDABLE_TESTNET, [""], 5000000),
                    "out": "unknown",
                    "mock_protocol_changes": {"short_tx_type_id": True, "utxo_support": True},
                },
            ],
        },
        "address": {
            "pack": [
                {
                    "config_context": {"ADDRESSVERSION": config.ADDRESSVERSION_MAINNET},
                    "in": ("1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",),
                    "out": binascii.unhexlify("006474849fc9ac0f5bd6b49fe144d14db7d32e2445"),
                },
                {
                    "config_context": {"ADDRESSVERSION": config.ADDRESSVERSION_MAINNET},
                    "in": ("1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",),
                    "out": binascii.unhexlify("00647484b055e2101927e50aba74957ba134d501d7"),
                },
                {
                    "config_context": {"P2SH_ADDRESSVERSION": config.P2SH_ADDRESSVERSION_MAINNET},
                    "in": ("3AAAA1111xxxxxxxxxxxxxxxxxxy3SsDsZ",),
                    "out": binascii.unhexlify("055ce31be63403fa7b19f2614272547c15c8df86b9"),
                },
                {
                    "config_context": {"P2SH_ADDRESSVERSION": config.P2SH_ADDRESSVERSION_TESTNET},
                    "in": ("2MtAV7xpAzU69E8GxRF2Vd2xt79kDnif6F5",),
                    "out": binascii.unhexlify("C40A12AD889AECC8F6213BFD6BD47911CAB1C30E5F"),
                },
                {
                    "in": ("BADBASE58III",),
                    "error": (
                        Exception,
                        "The address BADBASE58III is not a valid bitcoin address (testnet3)",
                    ),
                },
            ],
            "unpack": [
                {
                    "in": (binascii.unhexlify("006474849fc9ac0f5bd6b49fe144d14db7d32e2445"),),
                    "out": "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                },
                {
                    "in": (binascii.unhexlify("00647484b055e2101927e50aba74957ba134d501d7"),),
                    "out": "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                },
                {
                    "in": (binascii.unhexlify("055ce31be63403fa7b19f2614272547c15c8df86b9"),),
                    "out": "3AAAA1111xxxxxxxxxxxxxxxxxxy3SsDsZ",
                },
                {
                    "in": (binascii.unhexlify("C40A12AD889AECC8F6213BFD6BD47911CAB1C30E5F"),),
                    "out": "2MtAV7xpAzU69E8GxRF2Vd2xt79kDnif6F5",
                },
            ],
        },
        "versions.enhanced_send": {
            "unpack": [
                {
                    "in": (
                        binascii.unhexlify(
                            "000000000004fadf"
                            + "000000174876e800"
                            + "006474849fc9ac0f5bd6b49fe144d14db7d32e2445"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "asset": "SOUP",
                            "quantity": 100000000000,
                            "address": "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                            "memo": None,
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "0000000000000001"
                            + "000000000000007b"
                            + "00647484b055e2101927e50aba74957ba134d501d7"
                            + "0deadbeef123"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "asset": "XCP",
                            "quantity": 123,
                            "address": "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                            "memo": binascii.unhexlify("0deadbeef123"),
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify("0000000000000001" + "000000000000007b" + "0001"),
                        DP["default_block_index"],
                    ),
                    "error": (exceptions.UnpackError, "invalid message length"),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "0000000000000001"
                            + "000000000000007b"
                            + "006474849fc9ac0f5bd6b49fe144d14db7d32e2445"
                            + "9999999999999999999999999999999999999999999999999999999999999999999999"
                        ),
                        DP["default_block_index"],
                    ),
                    "error": (exceptions.UnpackError, "memo too long"),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "0000000000000000"
                            + "000000000000007b"
                            + "006474849fc9ac0f5bd6b49fe144d14db7d32e2445"
                        ),
                        DP["default_block_index"],
                    ),
                    "error": (exceptions.UnpackError, "asset id invalid"),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "0000000000000003"
                            + "000000000000007b"
                            + "006474849fc9ac0f5bd6b49fe144d14db7d32e2445"
                        ),
                        DP["default_block_index"],
                    ),
                    "error": (exceptions.UnpackError, "asset id invalid"),
                },
                {
                    "in": (
                        b"\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x86\xa0\x80u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6segwit",
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "address": P2WPKH_ADDR[0],
                            "asset": "XCP",
                            "quantity": 100000,
                            "memo": b"segwit",
                        }
                    ),
                },
            ],
            "validate": [
                # ----- tests copied from regular send -----
                {"in": (ADDR[0], ADDR[1], "XCP", DP["quantity"], None, 1), "out": ([])},
                {"in": (ADDR[0], P2SH_ADDR[0], "XCP", DP["quantity"], None, 1), "out": ([])},
                {"in": (P2SH_ADDR[0], ADDR[1], "XCP", DP["quantity"], None, 1), "out": ([])},
                {
                    "in": (ADDR[0], ADDR[1], "BTC", DP["quantity"], None, 1),
                    "out": ([f"cannot send {config.BTC}"]),
                },
                {
                    "in": (ADDR[0], ADDR[1], "XCP", DP["quantity"] / 3, None, 1),
                    "out": (["quantity must be in satoshis"]),
                },
                {
                    "in": (ADDR[0], ADDR[1], "XCP", -1 * DP["quantity"], None, 1),
                    "out": (["negative quantity"]),
                },
                {"in": (ADDR[0], MULTISIGADDR[0], "XCP", DP["quantity"], None, 1), "out": ([])},
                {"in": (ADDR[0], ADDR[1], "MAXI", 2**63 - 1, None, 1), "out": ([])},
                {"in": (ADDR[0], ADDR[1], "MAXI", 2**63, None, 1), "out": (["integer overflow"])},
                {
                    "in": (ADDR[0], ADDR[6], "XCP", DP["quantity"], None, 1),
                    "out": (["destination requires memo"]),
                },
                {
                    # ----- tests specific to enhanced send -----
                    "in": (
                        "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                        "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                        "SOUP",
                        100000000,
                        None,
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                        "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                        "SOUP",
                        100000000,
                        binascii.unhexlify("01ff"),
                        DP["default_block_index"],
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                        "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                        "SOUP",
                        0,
                        binascii.unhexlify("01ff"),
                        DP["default_block_index"],
                    ),
                    "out": (["zero quantity"]),
                },
                {
                    "in": (
                        "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                        "",
                        "SOUP",
                        100000000,
                        binascii.unhexlify("01ff"),
                        DP["default_block_index"],
                    ),
                    "out": (["destination is required"]),
                },
                {
                    "in": (
                        "1AAAA1111xxxxxxxxxxxxxxxxxxy43CZ9j",
                        "1AAAA2222xxxxxxxxxxxxxxxxxxy4pQ3tU",
                        "SOUP",
                        100000000,
                        binascii.unhexlify(
                            "9999999999999999999999999999999999999999999999999999999999999999999999"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (["memo is too long"]),
                },
            ],
            "compose": [
                # ----- tests copied from regular send -----
                {
                    "in": (ADDR[0], ADDR[1], "XCP", DP["quantity"] * 10000000, None, False),
                    "error": (exceptions.ComposeError, "insufficient funds"),
                },
                {
                    "in": (ADDR[0], ADDR[1], "XCP", DP["quantity"] / 3, None, False),
                    "error": (exceptions.ComposeError, "quantity must be an int (in satoshi)"),
                },
                {
                    "in": (ADDR[0], ADDR[1], "MAXI", 2**63 + 1, None, False),
                    "error": (exceptions.ComposeError, "insufficient funds"),
                },
                {
                    "in": (ADDR[0], ADDR[1], "BTC", DP["quantity"], None, False),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [("mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns", 100000000)],
                        None,
                    ),
                },
                {
                    "in": (ADDR[0], P2SH_ADDR[0], "BTC", DP["quantity"], None, False),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [("2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy", 100000000)],
                        None,
                    ),
                },
                {
                    "comment": "resolve subasset to numeric asset",
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (ADDR[0], ADDR[1], "PARENT.already.issued", 100000000, None, False),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        binascii.unhexlify(
                            "02"
                            + "01530821671b1065"
                            + "0000000005f5e100"
                            + "6f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec"
                        ),
                    ),
                },
                # ----- tests specific to enhanced send -----
                {
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (ADDR[1], ADDR[0], "XCP", DP["small"], None, None),
                    "out": (
                        ADDR[1],
                        [],
                        binascii.unhexlify(
                            "02"
                            + "0000000000000001"
                            + "0000000002faf080"
                            + "6f4838d8b3588c4c7ba7c1d06f866e9b3739c63037"
                        ),
                    ),
                },
                {
                    # memo as hex
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (ADDR[1], ADDR[0], "XCP", DP["small"], "12345abcde", True),
                    "out": (
                        ADDR[1],
                        [],
                        binascii.unhexlify(
                            "02"
                            + "0000000000000001"
                            + "0000000002faf080"
                            + "6f4838d8b3588c4c7ba7c1d06f866e9b3739c63037"
                            + "12345abcde"
                        ),
                    ),
                },
                {
                    # pack a string into bytes
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (ADDR[1], ADDR[0], "XCP", DP["small"], "hello", False),
                    "out": (
                        ADDR[1],
                        [],
                        binascii.unhexlify(
                            "02"
                            + "0000000000000001"
                            + "0000000002faf080"
                            + "6f4838d8b3588c4c7ba7c1d06f866e9b3739c63037"
                            + "68656c6c6f"
                        ),
                    ),
                },
                {
                    # memo too long
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (
                        ADDR[1],
                        ADDR[0],
                        "XCP",
                        DP["small"],
                        "12345678901234567890123456789012345",
                        False,
                    ),
                    "error": (exceptions.ComposeError, ["memo is too long"]),
                },
                {
                    "comment": "enhanced_send to a REQUIRE_MEMO address, without memo",
                    "in": (ADDR[0], ADDR[6], "XCP", DP["small"], None, False),
                    "error": (exceptions.ComposeError, ["destination requires memo"]),
                },
                {
                    "comment": "enhanced_send to a REQUIRE_MEMO address, with memo text",
                    "in": (ADDR[0], ADDR[6], "XCP", DP["small"], "12345", False),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b'\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x02\xfa\xf0\x80o\xb3\x90\x18~\xf2\x85D"\xac^J.\xb6\xff\xe9$\x96\xbe\xf5#12345',
                    ),
                },
                {
                    "comment": "enhanced_send to a REQUIRE_MEMO address, with memo hex",
                    "in": (ADDR[0], ADDR[6], "XCP", DP["small"], "deadbeef", True),
                    "out": (
                        "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        [],
                        b'\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x02\xfa\xf0\x80o\xb3\x90\x18~\xf2\x85D"\xac^J.\xb6\xff\xe9$\x96\xbe\xf5#\xde\xad\xbe\xef',
                    ),
                },
                {
                    "comment": "send from a P2WPKH address to a P2PKH one",
                    "in": (P2WPKH_ADDR[0], ADDR[0], "XCP", DP["small"], None, False),
                    "out": (
                        P2WPKH_ADDR[0],
                        [],
                        b"\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x02\xfa\xf0\x80oH8\xd8\xb3X\x8cL{\xa7\xc1\xd0o\x86n\x9b79\xc607",
                    ),
                },
            ],
            "parse": [
                # ----- tests copied from regular send -----
                {
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000005f5e100"
                                + SHORT_ADDR_BYTES[1]
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "quantity": 100000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "memo": None,
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                    ],
                },
                {
                    "comment": "zero quantity send",
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "block_index": DP["default_block_index"],
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000000000000"
                                + SHORT_ADDR_BYTES[0]
                            ),
                            "block_time": 155409000,
                            "fee": 10000,
                            "source": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                            "tx_index": DP["default_tx_index"],
                            "supported": 1,
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "quantity": 0,
                                "source": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                                "status": "invalid: zero quantity",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "btc_amount": 7800,
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "block_time": 155409000,
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0006cad8dc7f0b66"
                                + "00000000000001f4"
                                + SHORT_ADDR_BYTES[1]
                            ),
                            "block_hash": DP["default_block_hash"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "NODIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "quantity": 500,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "NODIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 500,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "NODIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 500,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000005f5e100"
                                + SHORT_ADDR_BYTES[0]
                            ),
                            "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "supported": 1,
                            "block_time": 155409000,
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "btc_amount": 7800,
                            "block_hash": DP["default_block_hash"],
                            "block_index": DP["default_block_index"],
                            "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "quantity": 100000000,
                                "source": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "block_time": 155409000,
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                            "btc_amount": 7800,
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000033a3e"
                                + "7fffffffffffffff"
                                + SHORT_ADDR_BYTES[1]
                            ),
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                            "supported": 1,
                            "block_hash": DP["default_block_hash"],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "MAXI",
                                "block_index": DP["default_block_index"],
                                "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "quantity": 9223372036854775807,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "MAXI",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "quantity": 9223372036854775807,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "MAXI",
                                "block_index": DP["default_block_index"],
                                "event": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "quantity": 9223372036854775807,
                            },
                        },
                    ],
                },
                # ----- tests specific to enhanced send -----
                {
                    "comment": "instead of auto-correcting the quantity to the amount the address holds return invalid: insufficient funds",
                    "in": (
                        {
                            "tx_index": DP["default_tx_index"],
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000058b11400"
                                + SHORT_ADDR_BYTES[3]
                            ),
                            "source": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                            "block_time": 310501000,
                            "block_hash": "46ac6d09237c7961199068fdd13f1508d755483e07c57a4c8f7ff18eb33a05c93ca6a86fa2e2af82fb77a5c337146bb37e279797a3d11970aec4693c46ea5a58",
                            "tx_hash": "736ecc18f9f41b3ccf67dded1252969e4929404d6ad657b2039b937a7785cf3e",
                            "supported": 1,
                            "destination": "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                            "btc_amount": 5430,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                                "quantity": 1488000000,
                                "source": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                                "status": "invalid: insufficient funds",
                                "tx_hash": "736ecc18f9f41b3ccf67dded1252969e4929404d6ad657b2039b937a7785cf3e",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
                {
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000005f5e100"
                                + SHORT_ADDR_BYTES[1]
                                + "beefbeef"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "quantity": 100000000,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "valid",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "memo": binascii.unhexlify("beefbeef"),
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": 100000000,
                            },
                        },
                    ],
                },
                {
                    # invalid memo (too long)
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "0000000005f5e100"
                                + SHORT_ADDR_BYTES[1]
                                + "9999999999999999999999999999999999999999999999999999999999999999999999"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": None,
                                "block_index": DP["default_block_index"],
                                "destination": None,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: could not unpack (memo too long)",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "memo": None,
                            },
                        }
                    ],
                },
                {
                    # invalid: quantity (too large)
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify(
                                "00000002"
                                + "0000000000000001"
                                + "ffffffffffffffff"
                                + SHORT_ADDR_BYTES[1]
                                + "beefbeef"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": None,
                                "block_index": DP["default_block_index"],
                                "destination": None,
                                "quantity": None,
                                "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                                "status": "invalid: quantity is too large",
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                                "memo": None,
                            },
                        }
                    ],
                },
                {
                    "comment": "Send a valid enhanced_send to destination address with REQUIRE_MEMO",
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "block_time": 155409000,
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                            "btc_amount": 7800,
                            "data": b'\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x02\xfa\xf0\x80o\xb3\x90\x18~\xf2\x85D"\xac^J.\xb6\xff\xe9$\x96\xbe\xf5#12345',
                            "source": ADDR[0],
                            "destination": ADDR[6],
                            "supported": 1,
                            "block_hash": DP["default_block_hash"],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[6],
                                "quantity": DP["small"],
                                "source": ADDR[0],
                                "status": "valid",
                                "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[6],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "send",
                                "event": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "quantity": DP["small"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "send",
                                "address": ADDR[0],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "quantity": DP["small"],
                            },
                        },
                    ],
                },
                {
                    "comment": "Parse a send from a P2PKH address to a P2WPKH one",
                    "mock_protocol_changes": {"enhanced_sends": True, "segwit_support": True},
                    "in": (
                        {
                            "block_index": DP["default_block_index"],
                            "block_time": 155409000,
                            "fee": 10000,
                            "tx_index": DP["default_tx_index"],
                            "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                            "btc_amount": 7800,
                            "data": b"\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x01\x86\xa0\x80u\x1ev\xe8\x19\x91\x96\xd4T\x94\x1cE\xd1\xb3\xa3#\xf1C;\xd6segwit",
                            "source": ADDR[0],
                            "destination": P2WPKH_ADDR[0],
                            "supported": 1,
                            "block_hash": DP["default_block_hash"],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": P2WPKH_ADDR[0],
                                "quantity": 100000,
                                "source": ADDR[0],
                                "status": "valid",
                                "tx_hash": "8fc698cf1fcd51e3d685511185c67c0a73e7b72954c6abbd29fbbbe560e043a0",
                                "tx_index": DP["default_tx_index"],
                            },
                        }
                    ],
                },
            ],
        },
        "versions.mpma": {
            "unpack": [
                {
                    "comment": "Should throw on empty data",
                    "in": (binascii.unhexlify(""), DP["default_block_index"]),
                    "error": (exceptions.UnpackError, "could not unpack"),
                },
                {
                    "comment": "0 addresses in a send is an error",
                    "in": (binascii.unhexlify("0000"), DP["default_block_index"]),
                    "error": (exceptions.DecodeError, "address list can't be empty"),
                },
                {
                    "comment": "Should throw on incomplete data",
                    "in": (binascii.unhexlify("0001ffff"), DP["default_block_index"]),
                    "error": (exceptions.UnpackError, "truncated data"),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e10040000000017d78400"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": ({"XCP": [(ADDR[2], DP["quantity"]), (ADDR[1], DP["quantity"])]}),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e100c4deadbeef8000000002faf0800"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [
                                (ADDR[2], DP["quantity"], binascii.unhexlify("DEADBEEF"), True),
                                (ADDR[1], DP["quantity"]),
                            ]
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e1008844454144424545468000000002faf0800"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [
                                (ADDR[2], DP["quantity"], "DEADBEEF", False),
                                (ADDR[1], DP["quantity"]),
                            ]
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00036f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f6c39ee7c8f3a5ffa6121b0304a7a0de9d3d9a1526f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000000000000000640000000017d784000000000002faf08020000000005f5e1000"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [
                                (ADDR[3], DP["quantity"]),
                                (ADDR[2], DP["quantity"]),
                                (ADDR[1], DP["quantity"]),
                            ]
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00036f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f6c39ee7c8f3a5ffa6121b0304a7a0de9d3d9a1526f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d9800000000017d784010006cad8dc7f0b66200000000000000014000000000000000440000000017d784000"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [(ADDR[3], DP["quantity"])],
                            "NODIVISIBLE": [(ADDR[1], 1)],
                            "DIVISIBLE": [(ADDR[2], DP["quantity"])],
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ecc4deadbeef8000000000000000c000000000bebc2008000000002faf0800"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [
                                (ADDR[2], DP["quantity"], binascii.unhexlify("DEADBEEF"), True),
                                (ADDR[1], DP["quantity"], binascii.unhexlify("DEADBEEF"), True),
                            ]
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ecc4deadbeef8000000000000000c000000000bebc201897ddfbd5b0000000005f5e1000"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "XCP": [
                                (ADDR[2], DP["quantity"], binascii.unhexlify("BEEFDEAD"), True),
                                (ADDR[1], DP["quantity"], binascii.unhexlify("DEADBEEF"), True),
                            ]
                        }
                    ),
                },
                {
                    "in": (
                        binascii.unhexlify(
                            "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d990000000005f5e100400000000000000040000000005f5e100000300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d990000000005f5e100400000000000000040000000005f5e10000"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "DIVISIBLE": [(ADDR[1], DP["quantity"])],
                            "XCP": [(ADDR[2], DP["quantity"])],
                        }
                    ),
                },
                {
                    # Test derived from block 618232 on BTC mainnet
                    "in": (
                        binascii.unhexlify(
                            "0004002e9943921a473dee1e04a579c1762ff6e9ac34e4006c7beeb1af092be778a2c0b8df639f2f8e9c987600a9055398b92818794b38b15794096f752167e25f00f3a6b6e4a093e5a5b9da76977a5270fd4d62553e40000091f59f36daf0000000271d94900180000004e3b29200200000009c76524002000000138eca4800806203d0c908232420000000000000000b000000000000000140024a67f0f279952000000000000000058000000000000000a00000000000000014000000908a3200cb000000000000000058000000000000000a000000000000000120000000000000002075410426156245525daa71f2e84a40797bcf28099a2c508662a8a33324a703597b9aa2661a79a82ffb4caaa9b15f4094622fbfa85f8b9dc7381f991f5a265421391cc3ad0075740087"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "MAFIACASH": [
                                ("15FPgnpZuNyZLVLsyB6UdFicsVvWFJXNve", 42000000000),
                                ("1PDJv8u8zw4Fgqr4uCb2yim9fgTs5zfM4s", 42000000000),
                                ("1GQhaWqejcGJ4GhQar7SjcCfadxvf5DNBD", 42000000000),
                                ("1AtcSh7uxenQ6AR5xqr6agAegWRUF5N4uh", 42000000000),
                            ],
                            "PAWNTHELAMBO": [
                                ("15FPgnpZuNyZLVLsyB6UdFicsVvWFJXNve", 1),
                                ("1PDJv8u8zw4Fgqr4uCb2yim9fgTs5zfM4s", 1),
                            ],
                            "SHADILOUNGE": [
                                ("15FPgnpZuNyZLVLsyB6UdFicsVvWFJXNve", 1),
                                ("1PDJv8u8zw4Fgqr4uCb2yim9fgTs5zfM4s", 1),
                                ("1GQhaWqejcGJ4GhQar7SjcCfadxvf5DNBD", 1),
                            ],
                            "TIKIPEPE": [
                                ("15FPgnpZuNyZLVLsyB6UdFicsVvWFJXNve", 1),
                                ("1PDJv8u8zw4Fgqr4uCb2yim9fgTs5zfM4s", 1),
                                ("1GQhaWqejcGJ4GhQar7SjcCfadxvf5DNBD", 1),
                                ("1AtcSh7uxenQ6AR5xqr6agAegWRUF5N4uh", 1),
                            ],
                        }
                    ),
                },
                {
                    # Test derived from block 647547 on BTC mainnet
                    "in": (
                        binascii.unhexlify(
                            "00010042276049e5518791be2ffe2c301f5dfe9ef85dd0400001720034b0410000000000000001500000006a79811e000000000000000054000079cec1665f4800000000000000050000000ca91f2d660000000000000005402736c8de6e34d54000000000000001500c5e4c71e081ceb00000000000000054000000045dc03ec4000000000000000500004af1271cf5fc00000000000000054001e71f8464432780000000000000015000002e1e4191f0d0000000000000005400012bc4aaac2a54000000000000001500079c7e774e411c00000000000000054000000045dc0a6f00000000000000015000002e1e486f661000000000000000540001c807abe13908000000000000000475410426156245525daa71f2e84a40797bcf28099a2c508662a8a33324a703597b9aa2661a79a82ffb4caaa9b15f4094622fbfa85f8b9dc7381f991f5a265421391cc3ad0075740087"
                        ),
                        DP["default_block_index"],
                    ),
                    "out": (
                        {
                            "BELLAMAFIA": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "DONPABLO": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "GEISHAPEPE": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 1)],
                            "GUARDDOG": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "MATRYOSHKAPP": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEACIDTRIP": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEAIR": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 1)],
                            "PEPECIGARS": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEDRACULA": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEHEMAN": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEHITMAN": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEJERICHO": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEKFC": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "PEPEWYATT": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 5)],
                            "XCHAINPEPE": [("172nmZbxDR6erc5PqNqV28fnMj7g6besru", 1)],
                        }
                    ),
                },
            ],
            "validate": [
                {"in": (ADDR[0], [], 1), "out": (["send list cannot be empty"])},
                {
                    "in": (ADDR[0], [("XCP", ADDR[1], DP["quantity"])], 1),
                    "out": (["send list cannot have only one element"]),
                },
                {
                    "in": (ADDR[0], [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], 0.1)], 1),
                    "out": ([f"quantities must be an int (in satoshis) for XCP to {ADDR[1]}"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], -DP["quantity"])],
                        1,
                    ),
                    "out": ([f"negative quantity for XCP to {ADDR[1]}"]),
                },
                {
                    "in": (ADDR[0], [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], 0)], 1),
                    "out": ([f"zero quantity for XCP to {ADDR[1]}"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], config.MAX_INT + 1)],
                        1,
                    ),
                    "out": ([f"integer overflow for XCP to {ADDR[1]}"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", None, DP["quantity"])],
                        1,
                    ),
                    "out": (["destination is required for XCP"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("BTC", ADDR[1], DP["quantity"])],
                        1,
                    ),
                    "out": ([f"cannot send BTC to {ADDR[1]}"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[6], DP["quantity"])],
                        1,
                    ),
                    "out": ([f"destination {ADDR[6]} requires memo"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], DP["quantity"])],
                        1,
                    ),
                    "out": ([]),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[2], DP["quantity"] + 1)],
                        1,
                    ),
                    "out": (["cannot specify more than once a destination per asset"]),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[2], DP["quantity"]),
                            ("XCP", ADDR[6], DP["quantity"], "DEADBEEF", True),
                        ],
                        1,
                    ),
                    "out": ([]),
                },
            ],
            "compose": [
                {
                    "in": (ADDR[0], [("XCP", ADDR[1], DP["quantity"] * 1000000)], None, None),
                    "error": (exceptions.ComposeError, "insufficient funds for XCP"),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], 0.1)],
                        None,
                        None,
                    ),
                    "error": (
                        exceptions.ComposeError,
                        "quantities must be an int (in satoshis) for XCP",
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[2], DP["quantity"]),
                            ("XCP", ADDR[1], DP["quantity"] * 10000),
                        ],
                        None,
                        None,
                    ),
                    "error": (exceptions.ComposeError, "insufficient funds for XCP"),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], DP["quantity"])],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e10040000000017d78400"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[2], DP["quantity"], "DEADBEEF", True),
                            ("XCP", ADDR[1], DP["quantity"]),
                        ],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e100c4deadbeef8000000002faf0800"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[2], DP["quantity"], "DEADBEEF", False),
                            ("XCP", ADDR[1], DP["quantity"]),
                        ],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e1008844454144424545468000000002faf0800"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[3], DP["quantity"]),
                            ("XCP", ADDR[2], DP["quantity"]),
                            ("XCP", ADDR[1], DP["quantity"]),
                        ],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300036f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f6c39ee7c8f3a5ffa6121b0304a7a0de9d3d9a1526f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000000000000000640000000017d784000000000002faf08020000000005f5e1000"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[3], DP["quantity"]),
                            ("DIVISIBLE", ADDR[2], DP["quantity"]),
                            ("NODIVISIBLE", ADDR[1], 1),
                        ],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300036f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f6c39ee7c8f3a5ffa6121b0304a7a0de9d3d9a1526f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d9800000000017d784010006cad8dc7f0b66200000000000000014000000000000000440000000017d784000"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], DP["quantity"])],
                        "DEADBEEF",
                        True,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ecc4deadbeef8000000000000000c000000000bebc2008000000002faf0800"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("XCP", ADDR[1], DP["quantity"])],
                        "DEADBEEF",
                        False,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec8844454144424545468000000000000000c000000000bebc2008000000002faf0800"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [
                            ("XCP", ADDR[2], DP["quantity"], "BEEFDEAD", True),
                            ("XCP", ADDR[1], DP["quantity"]),
                        ],
                        "DEADBEEF",
                        True,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ecc4deadbeef8000000000000000c000000000bebc201897ddfbd5b0000000005f5e1000"
                        ),
                    ),
                },
                {
                    "in": (
                        ADDR[0],
                        [("XCP", ADDR[2], DP["quantity"]), ("DIVISIBLE", ADDR[1], DP["quantity"])],
                        None,
                        None,
                    ),
                    "mock_protocol_changes": {"short_tx_type_id": True},
                    "out": (
                        ADDR[0],
                        [],
                        binascii.unhexlify(
                            "0300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d990000000005f5e100400000000000000040000000005f5e10000"
                        ),
                    ),
                },
                {
                    "in": (ADDR[0], [("XCP", ADDR[1], DP["quantity"])], ["memo1"], None),
                    "error": (exceptions.ComposeError, "`memo` must be a string"),
                },
                {
                    "in": (ADDR[0], [("XCP", ADDR[1], DP["quantity"])], "memo1", "nobool"),
                    "error": (exceptions.ComposeError, "`memo_is_hex` must be a boolean"),
                },
            ],
            "parse": [
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": ADDR[0],
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify("00000000")
                            + binascii.unhexlify(
                                "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec400000000000000060000000005f5e10040000000017d78400"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": ADDR[0],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[2],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": None,
                                "msg_index": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[1],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": None,
                                "msg_index": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[1],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[2],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "mpma send",
                                "address": ADDR[0],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"] * 2,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": ADDR[0],
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify("00000000")
                            + binascii.unhexlify(
                                "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ecc4deadbeef8000000000000000c000000000bebc201897ddfbd5b0000000005f5e1000"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": ADDR[0],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[2],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": binascii.unhexlify("BEEFDEAD"),
                                "msg_index": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[1],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": binascii.unhexlify("DEADBEEF"),
                                "msg_index": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[1],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[2],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "mpma send",
                                "address": ADDR[0],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"] * 2,
                            },
                        },
                    ],
                },
                {
                    "in": (
                        {
                            "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                            "source": ADDR[0],
                            "supported": 1,
                            "block_index": DP["default_block_index"],
                            "fee": 10000,
                            "block_time": 155409000,
                            "block_hash": DP["default_block_hash"],
                            "btc_amount": 7800,
                            "data": binascii.unhexlify("00000000")
                            + binascii.unhexlify(
                                "00026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d990000000005f5e100400000000000000040000000005f5e100000300026f4e5638a01efbb2f292481797ae1dcfcdaeb98d006f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec4000002896f8d2d990000000005f5e100400000000000000040000000005f5e10000"
                            ),
                            "tx_index": DP["default_tx_index"],
                            "destination": ADDR[0],
                        },
                    ),
                    "records": [
                        {
                            "table": "sends",
                            "values": {
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[2],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": None,
                                "msg_index": 1,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "sends",
                            "values": {
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "destination": ADDR[1],
                                "quantity": DP["quantity"],
                                "source": ADDR[0],
                                "status": "valid",
                                "memo": None,
                                "msg_index": 0,
                                "tx_hash": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "tx_index": DP["default_tx_index"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[1],
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "credits",
                            "values": {
                                "address": ADDR[2],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "calling_function": "mpma send",
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "mpma send",
                                "address": ADDR[0],
                                "asset": "XCP",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                        {
                            "table": "debits",
                            "values": {
                                "action": "mpma send",
                                "address": ADDR[0],
                                "asset": "DIVISIBLE",
                                "block_index": DP["default_block_index"],
                                "event": "db6d9052b576d973196363e11163d492f50926c2f1d1efd67b3d999817b0d04d",
                                "quantity": DP["quantity"],
                            },
                        },
                    ],
                },
            ],
        },
    }
)
