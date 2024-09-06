from fractions import Fraction

from counterpartycore.lib import exceptions
from counterpartycore.lib.ledger import CreditError, DebitError
from counterpartycore.lib.util import QuantityError

from ..params import (
    ADDR,
)
from ..params import DEFAULT_PARAMS as DP

LEDGER_VECTOR = {
    "ledger": {
        "generate_asset_id": [
            {"in": ("BTC", DP["default_block_index"]), "out": 0},
            {"in": ("XCP", DP["default_block_index"]), "out": 1},
            {"in": ("BCD", 308000), "error": (exceptions.AssetNameError, "too short")},
            {
                "in": ("ABCD", 308000),
                "error": (exceptions.AssetNameError, "non‐numeric asset name starts with ‘A’"),
            },
            {
                "in": (f"A{26 ** 12}", 308000),
                "error": (exceptions.AssetNameError, "numeric asset name not in range"),
            },
            {
                "in": (f"A{2 ** 64}", 308000),
                "error": (exceptions.AssetNameError, "numeric asset name not in range"),
            },
            {"in": (f"A{26 ** 12 + 1}", 308000), "out": 26**12 + 1},
            {"in": (f"A{2 ** 64 - 1}", 308000), "out": 2**64 - 1},
            {
                "in": ("LONGASSETNAMES", 308000),
                "error": (exceptions.AssetNameError, "long asset names must be numeric"),
            },
            {
                "in": ("BCDE_F", 308000),
                "error": (exceptions.AssetNameError, "invalid character:"),
            },
            {"in": ("BAAA", 308000), "out": 26**3},
            {"in": ("ZZZZZZZZZZZZ", 308000), "out": 26**12 - 1},
        ],
        "generate_asset_name": [
            {"in": (0, DP["default_block_index"]), "out": "BTC"},
            {"in": (1, DP["default_block_index"]), "out": "XCP"},
            {"in": (26**12 - 1, 308000), "out": "ZZZZZZZZZZZZ"},
            {"in": (26**3, 308000), "out": "BAAA"},
            {"in": (2**64 - 1, 308000), "out": f"A{2 ** 64 - 1}"},
            {"in": (26**12 + 1, 308000), "out": f"A{26 ** 12 + 1}"},
            {"in": (26**3 - 1, 308000), "error": (exceptions.AssetIDError, "too low")},
            {"in": (2**64, 308000), "error": (exceptions.AssetIDError, "too high")},
        ],
        "price": [{"in": (1, 10), "out": Fraction(1, 10)}],
        "last_message": [
            {
                "in": (),
                "out": {
                    "message_index": 1729,
                    "block_index": 310703,
                    "command": "parse",
                    "category": "blocks",
                    "bindings": '{"block_index":310703,"ledger_hash":"810efa958965423c5a4a3c88c9a673936a8f52c56836e899889bced0f62d4723","messages_hash":"a9c4435d25e51813cf5536e7dc8bdaf1afb7294e668bca71ddba2afbc91aa1de","transaction_count":0,"txlist_hash":"8b0a201e4d019a83a91ef66517d27b5320c2680ab0e0761a28ba4a3cff96b77b"}',
                    "timestamp": 0,
                    "event": "BLOCK_PARSED",
                    "tx_hash": None,
                    "event_hash": "1e8ea806a0149038a2974114b51ccd4fe248a8f5f6e1a69cc7908ef464b81f66",
                },
            }
        ],
        "get_asset_id": [
            {"in": ("XCP", DP["default_block_index"]), "out": 1},
            {"in": ("BTC", DP["default_block_index"]), "out": 0},
            {
                "in": ("foobar", DP["default_block_index"]),
                "error": (exceptions.AssetError, "No such asset: foobar"),
            },
        ],
        "resolve_subasset_longname": [
            {"in": ("XCP",), "out": "XCP"},
            {"in": ("PARENT",), "out": "PARENT"},
            {"in": ("PARENT.nonexistent.subasset",), "out": "PARENT.nonexistent.subasset"},
            {"in": ("PARENT.ILEGAL^^^",), "out": "PARENT.ILEGAL^^^"},
            {"in": ("PARENT.already.issued",), "out": f"A{26 ** 12 + 101}"},
        ],
        "debit": [
            {"in": (ADDR[0], "XCP", 1, 0), "out": None},
            {
                "in": (ADDR[0], "BTC", DP["quantity"], 0),
                "error": (DebitError, "Cannot debit bitcoins."),
            },
            {
                "in": (ADDR[0], "BTC", -1 * DP["quantity"], 0),
                "error": (DebitError, "Negative quantity."),
            },
            {
                "in": (ADDR[0], "BTC", 1.1 * DP["quantity"], 0),
                "error": (DebitError, "Quantity must be an integer."),
            },
            {"in": (ADDR[0], "XCP", 2**40, 0), "error": (DebitError, "Insufficient funds.")},
        ],
        "credit": [
            {"in": (ADDR[0], "XCP", 1, 0), "out": None},
            {
                "in": (ADDR[0], "BTC", DP["quantity"], 0),
                "error": (CreditError, "Cannot debit bitcoins."),
            },
            {
                "in": (ADDR[0], "BTC", -1 * DP["quantity"], 0),
                "error": (CreditError, "Negative quantity."),
            },
            {
                "in": (ADDR[0], "BTC", 1.1 * DP["quantity"], 0),
                "error": (CreditError, "Quantity must be an integer."),
            },
        ],
        "is_divisible": [
            {"in": ("XCP",), "out": True},
            {"in": ("BTC",), "out": True},
            {"in": ("DIVISIBLE",), "out": True},
            {"in": ("NODIVISIBLE",), "out": False},
            {"in": ("foobar",), "error": (exceptions.AssetError, "No such asset: foobar")},
        ],
        "value_in": [
            {
                "in": (
                    1.1,
                    "leverage",
                ),
                "out": 1,
            },
            {
                "in": (
                    1 / 10,
                    "fraction",
                ),
                "out": 0.1,
            },
            {
                "in": (
                    1,
                    "NODIVISIBLE",
                ),
                "out": 1,
            },
            {
                "in": (
                    1.111111111111,
                    "DIVISIBLE",
                ),
                "error": (
                    QuantityError,
                    "Divisible assets have only eight decimal places of precision.",
                ),
            },
            {
                "in": (
                    1.1,
                    "NODIVISIBLE",
                ),
                "error": (QuantityError, "Fractional quantities of indivisible assets."),
            },
        ],
        "value_out": [
            {
                "in": (
                    1.1,
                    "leverage",
                ),
                "out": "1.1",
            },
            {
                "in": (
                    1 / 10,
                    "fraction",
                ),
                "out": "10.0%",
            },
            {
                "in": (
                    1,
                    "NODIVISIBLE",
                ),
                "out": 1,
            },
            {
                "in": (
                    1.1,
                    "NODIVISIBLE",
                ),
                "error": (QuantityError, "Fractional quantities of indivisible assets."),
            },
        ],
        "xcp_created": [{"in": (), "out": 604506847920}],
        "xcp_destroyed": [{"in": (), "out": 675000020}],
        "xcp_supply": [
            {
                "in": (),
                "out": 603831847900,
            }
        ],
        "creations": [
            {
                "in": (),
                "out": {
                    "XCP": 604506847920,
                    "CALLABLE": 1000,
                    "DIVIDEND": 100,
                    "DIVISIBLE": 100000000000,
                    "FREEFAIRMIN": 10,
                    "LOCKED": 1000,
                    "LOCKEDPREV": 1000,
                    "MAXI": 9223372036854775807,
                    "NODIVISIBLE": 1000,
                    "PAIDFAIRMIN": 0,
                    "PAYTOSCRIPT": 1000,
                    "A95428956661682277": 100000000,
                    "PARENT": 100000000,
                    "QAIDFAIRMIN": 20,
                    "RAIDFAIRMIN": 20,
                    "A160361285792733729": 50,
                },
            }
        ],
        "destructions": [{"in": (), "out": {"XCP": 675000020}}],
        "asset_supply": [
            {
                "in": ("DIVISIBLE",),
                "out": 100000000000,
            }
        ],
        "supplies": [
            {
                "in": (),
                "out": {
                    "XCP": 603831847900,
                    "A95428956661682277": 100000000,
                    "CALLABLE": 1000,
                    "DIVIDEND": 100,
                    "DIVISIBLE": 100000000000,
                    "FREEFAIRMIN": 10,
                    "LOCKED": 1000,
                    "LOCKEDPREV": 1000,
                    "MAXI": 9223372036854775807,
                    "NODIVISIBLE": 1000,
                    "PAIDFAIRMIN": 0,
                    "PARENT": 100000000,
                    "PAYTOSCRIPT": 1000,
                    "QAIDFAIRMIN": 20,
                    "RAIDFAIRMIN": 20,
                    "A160361285792733729": 50,
                },
            }
        ],
        "get_balance": [
            {"in": (ADDR[0], "XCP"), "out": 91674999880},
            {"in": (ADDR[0], "foobar"), "out": 0},
        ],
        "get_asset_name": [
            {"in": (1, DP["default_block_index"]), "out": "XCP"},
            {"in": (0, DP["default_block_index"]), "out": "BTC"},
            {"in": (453, DP["default_block_index"]), "out": 0},
        ],
        "holders": [
            {
                "in": ("XCP",),
                "out": [
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 91674999880,
                        "escrow": None,
                    },
                    {
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "address_quantity": 99999990,
                        "escrow": None,
                    },
                    {
                        "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        "address_quantity": 300000000,
                        "escrow": None,
                    },
                    {
                        "address": "myAtcJEHAsDLbTkai6ipWDZeeL7VkxXsiM",
                        "address_quantity": 92999138821,
                        "escrow": None,
                    },
                    {
                        "address": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
                        "address_quantity": 92999130360,
                        "escrow": None,
                    },
                    {
                        "address": "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
                        "address_quantity": 92949122099,
                        "escrow": None,
                    },
                    {
                        "address": "mrPk7hTeZWjjSCrMTC2ET4SAUThQt7C4uK",
                        "address_quantity": 14999857,
                        "escrow": None,
                    },
                    {
                        "address": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                        "address_quantity": 46449548498,
                        "escrow": None,
                    },
                    {
                        "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
                        "address_quantity": 92999030129,
                        "escrow": None,
                    },
                    {
                        "address": "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                        "address_quantity": 0,
                        "escrow": None,
                    },
                    {
                        "address": "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
                        "address_quantity": 92945878046,
                        "escrow": None,
                    },
                    {
                        "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        "address_quantity": 0,
                        "escrow": None,
                    },
                    {
                        "address": "4f0433ba841038e2e16328445930dd7bca35309b14b0da4451c8f94c631368b8:1",
                        "address_quantity": 100,
                        "escrow": None,
                    },
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 100000000,
                        "escrow": "4f0433ba841038e2e16328445930dd7bca35309b14b0da4451c8f94c631368b8",
                    },
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 100000000,
                        "escrow": "21460d5c07284f9be9baf824927d0d4e4eb790e297f3162305841607b672349b",
                    },
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 100000000,
                        "escrow": "1899b2e6ec36ba4bc9d035e6640b0a62b08c3a147c77c89183a77d9ed9081b3a",
                    },
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 100000000,
                        "escrow": "74db175c4669a3d3a59e3fcddce9e97fcd7d12c35b58ef31845a1b20a1739498",
                    },
                    {
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "address_quantity": 10,
                        "escrow": "db4ea092bea6036e3d1e5f6ec863db9b900252b4f4d6d9faa6165323f433c51e",
                    },
                    {
                        "address": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                        "address_quantity": 10,
                        "escrow": "d79b590e4ec3e74cbc3eb4d0f956ce7abb0e3af2ccac85ff90ed8acf13f2e048",
                    },
                    {
                        "address": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
                        "address_quantity": 100,
                        "escrow": None,
                    },
                ],
            },
            {
                "in": ("DIVISIBLE",),
                "out": [
                    {
                        "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "address_quantity": 98799999999,
                        "escrow": None,
                    },
                    {
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "address_quantity": 100000000,
                        "escrow": None,
                    },
                    {
                        "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
                        "address_quantity": 1000000000,
                        "escrow": None,
                    },
                    {
                        "address": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                        "address_quantity": 100000000,
                        "escrow": None,
                    },
                    {
                        "address": "4f0433ba841038e2e16328445930dd7bca35309b14b0da4451c8f94c631368b8:1",
                        "address_quantity": 1,
                        "escrow": None,
                    },
                ],
            },
        ],
        "last_db_index": [{"in": (), "out": DP["default_block_index"] - 1}],
        "get_credits_by_asset": [
            {
                "in": ("A160361285792733729",),
                "out": [
                    {
                        "block_index": 310504,
                        "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        "asset": "A160361285792733729",
                        "quantity": 20,
                        "calling_function": "escrowed premint",
                        "event": "737fb998f29418a3253fad04de9c5406b18331f411a7cfa89ae8ee6b55f7ce03",
                        "tx_index": 505,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310505,
                        "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        "asset": "A160361285792733729",
                        "quantity": 10,
                        "calling_function": "escrowed fairmint",
                        "event": "6f4c3965a1cc2891e7dcdb4a3c12b73e6cf2e56e750dabcdf87c82443f08e1d8",
                        "tx_index": 506,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        "asset": "A160361285792733729",
                        "quantity": 20,
                        "calling_function": "escrowed fairmint",
                        "event": "ba6c7582f5c1e39bed32074c16f54ab338c79d0eefd3c8a7ba1f949e2febcd18",
                        "tx_index": 507,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "asset": "A160361285792733729",
                        "quantity": 7,
                        "calling_function": "unescrowed fairmint",
                        "event": "6f4c3965a1cc2891e7dcdb4a3c12b73e6cf2e56e750dabcdf87c82443f08e1d8",
                        "tx_index": 506,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "asset": "A160361285792733729",
                        "quantity": 3,
                        "calling_function": "fairmint commission",
                        "event": "6f4c3965a1cc2891e7dcdb4a3c12b73e6cf2e56e750dabcdf87c82443f08e1d8",
                        "tx_index": 506,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "asset": "A160361285792733729",
                        "quantity": 14,
                        "calling_function": "unescrowed fairmint",
                        "event": "ba6c7582f5c1e39bed32074c16f54ab338c79d0eefd3c8a7ba1f949e2febcd18",
                        "tx_index": 507,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "asset": "A160361285792733729",
                        "quantity": 6,
                        "calling_function": "fairmint commission",
                        "event": "ba6c7582f5c1e39bed32074c16f54ab338c79d0eefd3c8a7ba1f949e2febcd18",
                        "tx_index": 507,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "block_index": 310506,
                        "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "asset": "A160361285792733729",
                        "quantity": 20,
                        "calling_function": "premint",
                        "event": "737fb998f29418a3253fad04de9c5406b18331f411a7cfa89ae8ee6b55f7ce03",
                        "tx_index": 0,
                        "utxo": None,
                        "utxo_address": None,
                    },
                ],
            }
        ],
        "get_debits_by_asset": [
            {
                "in": ("A160361285792733729",),
                "out": [
                    {
                        "block_index": 310506,
                        "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                        "asset": "A160361285792733729",
                        "quantity": 50,
                        "action": "unescrowed fairmint",
                        "event": "737fb998f29418a3253fad04de9c5406b18331f411a7cfa89ae8ee6b55f7ce03",
                        "tx_index": 0,
                        "utxo": None,
                        "utxo_address": None,
                    }
                ],
            }
        ],
    },
}
