import binascii

from bitcoinutils.keys import P2pkhAddress, P2wpkhAddress
from bitcoinutils.script import Script, b_to_h
from bitcoinutils.transactions import TxInput, TxOutput, TxWitnessInput

from counterpartycore.lib import config, exceptions

from ..params import ADDR, DEFAULT_PARAMS, DP, MULTISIGADDR, P2WPKH_ADDR

PROVIDED_PUBKEYS = ",".join([DEFAULT_PARAMS["pubkey"][ADDR[0]], DEFAULT_PARAMS["pubkey"][ADDR[1]]])

ARC4_KEY = "0000000000000000000000000000000000000000000000000000000000000000"
UTXO_1 = "344dcc8909ca3a137630726d0071dfd2df4f7c855bac150c7d3a8367835c90bc:1"
UTXO_2 = "4f0433ba841038e2e16328445930dd7bca35309b14b0da4451c8f94c631368b8:1"
UTXO_3 = "1fc2e5a57f584b2f2edd05676e75c33d03eed1d3098cc0550ea33474e3ec9db1:1"

MULTISIG_PAIRS = [
    (
        "02e34ccc12f76f0562d24e7b0b3b01be4d90750dcf94eda3f22947221e07c1300e",
        "02ecc4a8544f08f3d5aa6d5af2a442904638c351f441d44ebe97243de761813949",
    ),
    (
        "02e34ccc12f76f0562d263720b3842b23aa86813c7d1848efb2944611270f92d2a",
        "03f2cced3d6201f3d6e9612dcab95c980351ee58f4429742c9af3923ef24e814be",
    ),
    (
        "02fe4ccc12f76f0562d26a72087b4ec502b5761b82b8a987fb2a076d6548e43335",
        "02fa89cc75076d9fb9c5417aa5cb30fc22198b34982dbb629ec04b4f8b05a071ab",
    ),
]
OPRETURN_DATA = b"\x8a]\xda\x15\xfbo\x05b\xc2cr\x0b8B\xb2:\xa8h\x13\xc7\xd1"

COMPOSER_VECTOR = {
    "api.composer": {
        "address_to_script_pub_key": [
            {
                "comment": "P2PKH address",
                "in": (ADDR[0], [], {}),
                "out": P2pkhAddress(ADDR[0]).to_script_pub_key(),
            },
            {
                "comment": "P2WPKH address",
                "in": (P2WPKH_ADDR[0], [], {}),
                "out": P2wpkhAddress(P2WPKH_ADDR[0]).to_script_pub_key(),
            },
            {
                "comment": "multisig address",
                "in": (MULTISIGADDR[0], [], {"pubkeys": PROVIDED_PUBKEYS}),
                "out": Script(
                    [
                        1,
                        DEFAULT_PARAMS["pubkey"][ADDR[0]],
                        DEFAULT_PARAMS["pubkey"][ADDR[1]],
                        2,
                        "OP_CHECKMULTISIG",
                    ]
                ),
            },
        ],
        "create_tx_output": [
            {
                "comment": "from address",
                "in": (666, ADDR[0], [], {}),
                "out": TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key()),
            },
            {
                "comment": "from script",
                "in": (666, P2pkhAddress(ADDR[0]).to_script_pub_key().to_hex(), [], {}),
                "out": TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key()),
            },
            {
                "comment": "from script",
                "in": (666, "00aaff", [], {}),
                "out": TxOutput(666, Script.from_raw("00aaff")),
            },
            {
                "comment": "from invalid script",
                "in": (666, "00aafff", [], {}),
                "error": (
                    exceptions.ComposeError,
                    "Invalid script or address for output: 00aafff (error: invalid script)",
                ),
            },
            {
                "comment": "from invalid address",
                "in": (666, "toto", [], {}),
                "error": (
                    exceptions.ComposeError,
                    "Invalid script or address for output: toto (error: Invalid address: toto)",
                ),
            },
        ],
        "regular_dust_size": [
            {
                "in": ({},),
                "out": 546,
            },
            {
                "in": ({"regular_dust_size": 666},),
                "out": 666,
            },
            {
                "in": ({"regular_dust_size": None},),
                "out": 546,
            },
        ],
        "multisig_dust_size": [
            {
                "in": ({},),
                "out": 1000,
            },
            {
                "in": ({"multisig_dust_size": 666},),
                "out": 666,
            },
            {
                "in": ({"multisig_dust_size": None},),
                "out": 1000,
            },
        ],
        "dust_size": [
            {
                "in": (ADDR[0], {}),
                "out": 546,
            },
            {
                "in": (ADDR[0], {"regular_dust_size": 666}),
                "out": 666,
            },
            {
                "in": (MULTISIGADDR[0], {}),
                "out": 1000,
            },
            {
                "in": (MULTISIGADDR[0], {"multisig_dust_size": 666}),
                "out": 666,
            },
        ],
        "perpare_non_data_outputs": [
            {
                "comment": "P2PKH address",
                "in": ([(ADDR[0], 0)], [], {}),
                "out": [TxOutput(546, P2pkhAddress(ADDR[0]).to_script_pub_key())],
            },
            {
                "comment": "Multisig address",
                "in": ([(MULTISIGADDR[0], 0)], [], {"pubkeys": PROVIDED_PUBKEYS}),
                "out": [
                    TxOutput(
                        1000,
                        Script(
                            [
                                1,
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                DEFAULT_PARAMS["pubkey"][ADDR[1]],
                                2,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    )
                ],
            },
            {
                "in": ([(ADDR[0], 2024)], [], {}),
                "out": [TxOutput(2024, P2pkhAddress(ADDR[0]).to_script_pub_key())],
            },
        ],
        "determine_encoding": [
            {
                "in": (b"Hello, World!", {}),
                "out": "opreturn",
            },
            {
                "in": (b"Hello, World!" * 100, {}),
                "out": "multisig",
            },
            {
                "in": (b"Hello, World!", {"encoding": "p2sh"}),
                "error": (exceptions.ComposeError, "Not supported encoding: p2sh"),
            },
            {
                "in": (b"Hello, World!", {"encoding": "toto"}),
                "error": (exceptions.ComposeError, "Not supported encoding: toto"),
            },
        ],
        "encrypt_data": [
            {
                "in": (b"Hello, World!", ARC4_KEY),
                "out": b"\x96}\xe5-\xcc\x1b}m\xe5tr\x03v",
            },
        ],
        "prepare_opreturn_output": [
            {
                "in": (b"Hello, World!", ARC4_KEY),
                "out": [
                    TxOutput(
                        0,
                        Script(
                            [
                                "OP_RETURN",
                                b_to_h(OPRETURN_DATA),
                            ]
                        ),
                    )
                ],
            },
        ],
        "is_valid_pubkey": [
            {
                "in": (DEFAULT_PARAMS["pubkey"][ADDR[0]],),
                "out": True,
            },
            {
                "in": (DEFAULT_PARAMS["pubkey"][ADDR[0]][::-1],),
                "out": False,
            },
        ],
        "search_pubkey": [
            {
                "in": (ADDR[0], [], {}),
                "out": DEFAULT_PARAMS["pubkey"][ADDR[0]],
            },
            {
                "in": (ADDR[0], [], {"pubkeys": PROVIDED_PUBKEYS}),
                "out": DEFAULT_PARAMS["pubkey"][ADDR[0]],
            },
        ],
        "make_valid_pubkey": [
            {
                "in": (binascii.unhexlify("aa" * 31),),
                "out": b"\x02\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa|",
            },
            {
                "in": (binascii.unhexlify("bb" * 31),),
                "out": b"\x03\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xbb\xc4",
            },
        ],
        "data_to_pubkey_pairs": [
            {
                "in": (b"Hello, World!" * 10, ARC4_KEY),
                "out": MULTISIG_PAIRS,
            },
        ],
        "prepare_multisig_output": [
            {
                "comment": "Encrypted",
                "in": (ADDR[0], b"Hello, World!" * 10, ARC4_KEY, [], {"pubkeys": PROVIDED_PUBKEYS}),
                "out": [
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[0][0],
                                MULTISIG_PAIRS[0][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[1][0],
                                MULTISIG_PAIRS[1][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[2][0],
                                MULTISIG_PAIRS[2][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                ],
            },
        ],
        "prepare_data_outputs": [
            {
                "in": (ADDR[0], b"Hello, World!", [{"txid": ARC4_KEY}], {}),
                "out": [TxOutput(0, Script(["OP_RETURN", b_to_h(OPRETURN_DATA)]))],
            },
            {
                "in": (
                    ADDR[0],
                    b"Hello, World!" * 10,
                    [{"txid": ARC4_KEY}],
                    {"pubkeys": PROVIDED_PUBKEYS, "encoding": "opreturn"},
                ),
                "error": (exceptions.ComposeError, "One `OP_RETURN` output per transaction"),
            },
            {
                "in": (
                    ADDR[0],
                    b"Hello, World!" * 10,
                    [{"txid": ARC4_KEY}],
                    {"pubkeys": PROVIDED_PUBKEYS, "encoding": "multisig"},
                ),
                "out": [
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[0][0],
                                MULTISIG_PAIRS[0][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[1][0],
                                MULTISIG_PAIRS[1][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[2][0],
                                MULTISIG_PAIRS[2][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                ],
            },
            {
                "in": (
                    ADDR[0],
                    b"Hello, World!" * 10,
                    [],
                    {"pubkeys": PROVIDED_PUBKEYS, "encoding": "p2sh"},
                ),
                "error": (exceptions.ComposeError, "Not supported encoding: p2sh"),
            },
        ],
        "prepare_more_outputs": [
            {
                "in": (f"546:{ADDR[0]}", [], {}),
                "out": [TxOutput(546, P2pkhAddress(ADDR[0]).to_script_pub_key())],
            },
            {
                "comment": "Multisig address",
                "in": (f"546:{MULTISIGADDR[0]}", [], {"pubkeys": PROVIDED_PUBKEYS}),
                "out": [
                    TxOutput(
                        546,
                        Script(
                            [
                                1,
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                DEFAULT_PARAMS["pubkey"][ADDR[1]],
                                2,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    )
                ],
            },
            {
                "in": (f"2024:{ADDR[0]}", [], {}),
                "out": [TxOutput(2024, P2pkhAddress(ADDR[0]).to_script_pub_key())],
            },
            {
                "in": ("666:00aaff", [], {}),
                "out": [TxOutput(666, Script.from_raw("00aaff"))],
            },
            {
                "in": (
                    f"546:{ADDR[0]},546:{MULTISIGADDR[0]},2024:{ADDR[0]},666:00aaff",
                    [],
                    {"pubkeys": PROVIDED_PUBKEYS},
                ),
                "out": [
                    TxOutput(546, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(
                        546,
                        Script(
                            [
                                1,
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                DEFAULT_PARAMS["pubkey"][ADDR[1]],
                                2,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(2024, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(666, Script.from_raw("00aaff")),
                ],
            },
        ],
        "prepare_outputs": [
            {
                "in": (ADDR[0], [(ADDR[0], 9999)], b"Hello, World!", [{"txid": ARC4_KEY}], {}),
                "out": [
                    TxOutput(9999, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(0, Script(["OP_RETURN", b_to_h(OPRETURN_DATA)])),
                ],
            },
            {
                "in": (ADDR[0], [(ADDR[0], 9999)], b"Hello, World!", [{"txid": ARC4_KEY}], {}),
                "out": [
                    TxOutput(9999, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(
                        0,
                        Script(
                            [
                                "OP_RETURN",
                                b_to_h(OPRETURN_DATA),
                            ]
                        ),
                    ),
                ],
            },
            {
                "in": (
                    ADDR[0],
                    [(ADDR[0], 9999)],
                    b"Hello, World!" * 10,
                    [{"txid": ARC4_KEY}],
                    {"pubkeys": PROVIDED_PUBKEYS, "encoding": "multisig"},
                ),
                "out": [
                    TxOutput(9999, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[0][0],
                                MULTISIG_PAIRS[0][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[1][0],
                                MULTISIG_PAIRS[1][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[2][0],
                                MULTISIG_PAIRS[2][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                ],
            },
            {
                "in": (
                    ADDR[0],
                    [(ADDR[0], 9999)],
                    b"Hello, World!" * 10,
                    [{"txid": ARC4_KEY}],
                    {
                        "pubkeys": PROVIDED_PUBKEYS,
                        "encoding": "multisig",
                        "more_outputs": f"546:{ADDR[0]}",
                    },
                ),
                "out": [
                    TxOutput(9999, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[0][0],
                                MULTISIG_PAIRS[0][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[1][0],
                                MULTISIG_PAIRS[1][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(
                        config.DEFAULT_MULTISIG_DUST_SIZE,
                        Script(
                            [
                                1,
                                MULTISIG_PAIRS[2][0],
                                MULTISIG_PAIRS[2][1],
                                DEFAULT_PARAMS["pubkey"][ADDR[0]],
                                3,
                                "OP_CHECKMULTISIG",
                            ]
                        ),
                    ),
                    TxOutput(546, P2pkhAddress(ADDR[0]).to_script_pub_key()),
                ],
            },
        ],
        "complete_unspent_list": [
            {
                "in": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                        }
                    ],
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 199909140,
                        "amount": 1.9990914,
                        "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                        "is_segwit": False,
                    }
                ],
            },
            {
                "in": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2",
                            "vout": 0,
                        }
                    ],
                ),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2:0 (transaction not found)",
                ),
            },
        ],
        "prepare_inputs_set": [
            {
                "in": ("aabb",),
                "error": (exceptions.ComposeError, "invalid UTXOs: aabb (invalid format)"),
            },
            {
                "in": ("aa:bb:cc:dd:ee",),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: aa:bb:cc:dd:ee (invalid format)",
                ),
            },
            {
                "in": ("aa:3:cc:dd",),
                "error": (exceptions.ComposeError, "invalid UTXOs: aa:3:cc:dd (invalid format)"),
            },
            {
                "in": ("ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:aa",),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:aa (invalid value)",
                ),
            },
            {
                "in": (
                    "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:100:aagh",
                ),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:100:aagh (invalid script_pub_key)",
                ),
            },
            {
                "in": (
                    "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:100:aa00",
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 100,
                        "script_pub_key": "aa00",
                    }
                ],
            },
            {
                "in": (
                    "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0:100:aa00,ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2:0:200:aa00",
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 100,
                        "script_pub_key": "aa00",
                    },
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2",
                        "vout": 0,
                        "value": 200,
                        "script_pub_key": "aa00",
                    },
                ],
            },
        ],
        "utxo_to_address": [
            {
                "in": ("1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",),
                "out": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            },
            {
                "in": ("ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0",),
                "out": ADDR[0],
            },
            {
                "in": ("ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2:0",),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2:0 (not found in the database or Bitcoin Core)",
                ),
            },
        ],
        "ensure_utxo_is_first": [
            {
                "in": (
                    "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0",
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 1,
                        },
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                        },
                    ],
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                    },
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 1,
                    },
                ],
            },
            {
                "in": (
                    "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0",
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 1,
                        },
                    ],
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 999,
                    },
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 1,
                    },
                ],
            },
        ],
        "filter_utxos_with_balances": [
            {
                "in": (
                    ADDR[0],
                    [
                        {
                            "txid": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53",
                            "vout": 0,
                        }
                    ],
                    {},
                ),
                "error": (
                    exceptions.ComposeError,
                    "invalid UTXOs: 1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0 (use `use_utxos_with_balances=True` to include them or `exclude_utxos_with_balances=True` to exclude them silently)",
                ),
            },
            {
                "in": (
                    ADDR[0],
                    [
                        {
                            "txid": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53",
                            "vout": 0,
                        }
                    ],
                    {"exclude_utxos_with_balances": True},
                ),
                "out": [],
            },
            {
                "in": (
                    ADDR[0],
                    [
                        {
                            "txid": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53",
                            "vout": 0,
                        },
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 1,
                        },
                    ],
                    {"exclude_utxos_with_balances": True},
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 1,
                    }
                ],
            },
            {
                "in": (
                    ADDR[0],
                    [
                        {
                            "txid": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53",
                            "vout": 0,
                        }
                    ],
                    {"use_utxos_with_balances": True},
                ),
                "out": [
                    {
                        "txid": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53",
                        "vout": 0,
                    }
                ],
            },
        ],
        "prepare_unspent_list": [
            {
                "in": (
                    ADDR[0],
                    {},
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 199909140,
                        "amount": 1.9990914,
                        "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                        "is_segwit": False,
                    }
                ],
            },
            {
                "in": (
                    ADDR[0],
                    {
                        "inputs_set": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0"
                    },
                ),
                "out": [
                    {
                        "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                        "vout": 0,
                        "value": 199909140,
                        "amount": 1.9990914,
                        "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                        "is_segwit": False,
                    }
                ],
            },
            {
                "in": (
                    ADDR[0],
                    {
                        "exclude_utxos": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1:0"
                    },
                ),
                "error": (
                    exceptions.ComposeError,
                    f"No UTXOs found for {ADDR[0]}, provide UTXOs with the `inputs_set` parameter",
                ),
            },
            {
                "in": (
                    ADDR[0],
                    {
                        "unspent_tx_hash": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c2"
                    },
                ),
                "error": (
                    exceptions.ComposeError,
                    f"No UTXOs found for {ADDR[0]}, provide UTXOs with the `inputs_set` parameter",
                ),
            },
        ],
        "utxos_to_txins": [
            {
                "in": (
                    [
                        {
                            "txid": UTXO_1.split(":")[0],
                            "vout": int(UTXO_1.split(":")[1]),
                            "value": 999,
                        },
                        {
                            "txid": UTXO_2.split(":")[0],
                            "vout": int(UTXO_2.split(":")[1]),
                            "value": 999,
                        },
                        {
                            "txid": UTXO_3.split(":")[0],
                            "vout": int(UTXO_3.split(":")[1]),
                            "value": 999,
                        },
                    ],
                ),
                "out": [
                    TxInput(UTXO_1.split(":")[0], int(UTXO_1.split(":")[1])),
                    TxInput(UTXO_2.split(":")[0], int(UTXO_2.split(":")[1])),
                    TxInput(UTXO_3.split(":")[0], int(UTXO_3.split(":")[1])),
                ],
            }
        ],
        "get_dummy_script_sig": [
            {
                "comment": "P2PK",
                "in": (
                    "41049464205950188c29d377eebca6535e0f3699ce4069ecd77ffebfbd0bcf95e3c134cb7d2742d800a12df41413a09ef87a80516353a2f0a280547bb5512dc03da8ac",
                ),
                "out": Script.from_raw(
                    "48304500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                ),
            },
            {
                "comment": "P2PKH",
                "in": ("76a91455ae51684c43435da751ac8d2173b2652eb6410588ac",),
                "out": Script.from_raw(
                    "4830450000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000021030000000000000000000000000000000000000000000000000000000000000000"
                ),
            },
            {
                "comment": "P2MS",
                "in": (
                    "524104d81fd577272bbe73308c93009eec5dc9fc319fc1ee2e7066e17220a5d47a18314578be2faea34b9f1f8ca078f8621acd4bc22897b03daa422b9bf56646b342a24104ec3afff0b2b66e8152e9018fe3be3fc92b30bf886b3487a525997d00fd9da2d012dce5d5275854adc3106572a5d1e12d4211b228429f5a7b2f7ba92eb0475bb14104b49b496684b02855bc32f5daefa2e2e406db4418f3b86bca5195600951c7d918cdbe5e6d3736ec2abf2dd7610995c3086976b2c0c7b4e459d10b34a316d5a5e753ae",
                ),
                "out": Script.from_raw(
                    "00304500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000304500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                ),
            },
            {
                "comment": "P2SH",
                "in": ("a914748284390f9e263a4b766a75d0633c50426eb87587",),
                "out": Script.from_raw(
                    "004830450000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000048304500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                ),
            },
            {
                "comment": "P2WPKH",
                "in": ("0014841b80d2cc75f5345c482af96294d04fdd66b2b7",),
                "out": None,
            },
            {
                "comment": "P2WSH",
                "in": ("002065f91a53cb7120057db3d378bd0f7d944167d43a7dcbff15d6afc4823f1d3ed3",),
                "out": None,
            },
            {
                "comment": "P2TR",
                "in": ("51200f0c8db753acbd17343a39c2f3f4e35e4be6da749f9e35137ab220e7b238a667",),
                "out": None,
            },
        ],
        "get_dummy_witness": [
            {
                "comment": "P2WPKH",
                "in": ("0014841b80d2cc75f5345c482af96294d04fdd66b2b7",),
                "out": TxWitnessInput(
                    [
                        "304500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                        "030000000000000000000000000000000000000000000000000000000000000000",
                    ]
                ),
            },
            {
                "comment": "P2WSH",
                "in": ("002065f91a53cb7120057db3d378bd0f7d944167d43a7dcbff15d6afc4823f1d3ed3",),
                "out": TxWitnessInput(
                    [
                        "4830450000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000021030000000000000000000000000000000000000000000000000000000000000000",
                        "002065f91a53cb7120057db3d378bd0f7d944167d43a7dcbff15d6afc4823f1d3ed3",
                    ]
                ),
            },
            {
                "comment": "P2TR",
                "in": ("51200f0c8db753acbd17343a39c2f3f4e35e4be6da749f9e35137ab220e7b238a667",),
                "out": TxWitnessInput(
                    [
                        "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                    ]
                ),
            },
            {
                "comment": "P2PK",
                "in": (
                    "41049464205950188c29d377eebca6535e0f3699ce4069ecd77ffebfbd0bcf95e3c134cb7d2742d800a12df41413a09ef87a80516353a2f0a280547bb5512dc03da8ac",
                ),
                "out": None,
            },
            {
                "comment": "P2PKH",
                "in": ("76a91455ae51684c43435da751ac8d2173b2652eb6410588ac",),
                "out": None,
            },
            {
                "comment": "P2MS",
                "in": (
                    "524104d81fd577272bbe73308c93009eec5dc9fc319fc1ee2e7066e17220a5d47a18314578be2faea34b9f1f8ca078f8621acd4bc22897b03daa422b9bf56646b342a24104ec3afff0b2b66e8152e9018fe3be3fc92b30bf886b3487a525997d00fd9da2d012dce5d5275854adc3106572a5d1e12d4211b228429f5a7b2f7ba92eb0475bb14104b49b496684b02855bc32f5daefa2e2e406db4418f3b86bca5195600951c7d918cdbe5e6d3736ec2abf2dd7610995c3086976b2c0c7b4e459d10b34a316d5a5e753ae",
                ),
                "out": None,
            },
            {
                "comment": "P2SH",
                "in": ("a914748284390f9e263a4b766a75d0633c50426eb87587",),
                "out": None,
            },
        ],
        "prepare_fee_parameters": [
            {"in": ({"exact_fee": 1000},), "out": (1000, None, None)},
            {"in": ({"exact_fee": 666, "max_fee": 1000},), "out": (666, None, None)},
            {"in": ({"max_fee": 1000},), "out": (None, 3, 1000)},
            {"in": ({"max_fee": 1000, "sat_per_vbyte": 8},), "out": (None, 8, 1000)},
            {"in": ({"max_fee": 1000, "confirmation_target": 8},), "out": (None, 16, 1000)},
        ],
        "prepare_inputs_and_change": [
            {
                "comment": "using exact_fee",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {"exact_fee": 1000},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    199909140,
                    [TxOutput(199909140 - 666 - 1000, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                ),
            },
            {
                "comment": "using exact_fee and change_address",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {"exact_fee": 1000, "change_address": ADDR[1]},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    199909140,
                    [TxOutput(199909140 - 666 - 1000, P2pkhAddress(ADDR[1]).to_script_pub_key())],
                ),
            },
            {
                "comment": "using exact_fee, change_address and use_all_inputs_set",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        },
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 1,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        },
                    ],
                    {"exact_fee": 1000, "change_address": ADDR[1], "use_all_inputs_set": True},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        },
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 1,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        },
                    ],
                    199909140 * 2,
                    [
                        TxOutput(
                            199909140 * 2 - 666 - 1000, P2pkhAddress(ADDR[1]).to_script_pub_key()
                        )
                    ],
                ),
            },
            {
                "comment": "using default construct_params",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    199909140,
                    [TxOutput(199909140 - 666 - 678, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                ),
            },
            {
                "comment": "using max_fee",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {"max_fee": 200},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    199909140,
                    [TxOutput(199909140 - 666 - 200, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                ),
            },
            {
                "comment": "using high fee so no change",
                "in": (
                    ADDR[0],
                    [TxOutput(666, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {"exact_fee": 199909140 - 666 - 10},
                ),
                "out": (
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    199909140,
                    [],
                ),
            },
            {
                "comment": "not enough funds",
                "in": (
                    ADDR[0],
                    [TxOutput(199909140, P2pkhAddress(ADDR[0]).to_script_pub_key())],
                    [
                        {
                            "txid": "ae241be7be83ebb14902757ad94854f787d9730fc553d6f695346c9375c0d8c1",
                            "vout": 0,
                            "value": 199909140,
                            "amount": 1.9990914,
                            "script_pub_key": "76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                            "is_segwit": False,
                        }
                    ],
                    {"exact_fee": 1000},
                ),
                "error": (
                    exceptions.ComposeError,
                    f"Insufficient funds for the target amount: 199909140 < {199909140 + 1000}",
                ),
            },
        ],
        "construct": [
            {
                "in": ((ADDR[0], [(ADDR[1], 666)], b"Hello, World!"), {}),
                "out": {
                    "btc_change": 199907700,
                    "btc_fee": 774,
                    "btc_in": 199909140,
                    "btc_out": 666,
                    "data": b"TESTXXXXHello, World!",
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf7459ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "signed_tx_estimated_size": {
                        "adjusted_vsize": 258,
                        "sigops_count": 8,
                        "vsize": 258,
                    },
                },
            },
            {
                "in": ((ADDR[0], [(ADDR[1], 666)], b"Hello, World!"), {"exact_fee": 1000}),
                "out": {
                    "btc_change": 199909140 - 666 - 1000,
                    "btc_fee": 1000,
                    "btc_in": 199909140,
                    "btc_out": 666,
                    "data": b"TESTXXXXHello, World!",
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "signed_tx_estimated_size": {
                        "adjusted_vsize": 258,
                        "sigops_count": 8,
                        "vsize": 258,
                    },
                },
            },
        ],
        "check_transaction_sanity": [
            {
                "in": (
                    (ADDR[0], [(ADDR[1], 666)], b"Hello, World!"),
                    {
                        "btc_change": 199909140 - 666 - 1000,
                        "btc_fee": 1000,
                        "btc_in": 199909140,
                        "btc_out": 666,
                        "data": b"TESTXXXXHello, World!",
                        "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                        "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    },
                    {"exact_fee": 1000},
                ),
                "out": None,
            },
            {
                "in": (
                    (ADDR[1], [(ADDR[1], 666)], b"Hello, World!"),
                    {
                        "btc_change": 199909140 - 666 - 1000,
                        "btc_fee": 1000,
                        "btc_in": 199909140,
                        "btc_out": 666,
                        "data": b"TESTXXXXHello, World!",
                        "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                        "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    },
                    {"exact_fee": 1000},
                ),
                "error": (
                    exceptions.ComposeError,
                    "Sanity check error: source address does not match the first input address",
                ),
            },
            {
                "in": (
                    (ADDR[0], [(ADDR[0], 666)], b"Hello, World!"),
                    {
                        "btc_change": 199909140 - 666 - 1000,
                        "btc_fee": 1000,
                        "btc_in": 199909140,
                        "btc_out": 666,
                        "data": b"TESTXXXXHello, World!",
                        "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                        "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    },
                    {"exact_fee": 1000},
                ),
                "error": (
                    exceptions.ComposeError,
                    "Sanity check error: destination address does not match the output address",
                ),
            },
            {
                "in": (
                    (ADDR[0], [(ADDR[1], 665)], b"Hello, World!"),
                    {
                        "btc_change": 199909140 - 666 - 1000,
                        "btc_fee": 1000,
                        "btc_in": 199909140,
                        "btc_out": 666,
                        "data": b"TESTXXXXHello, World!",
                        "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                        "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    },
                    {"exact_fee": 1000},
                ),
                "error": (
                    exceptions.ComposeError,
                    "Sanity check error: destination value does not match the output value",
                ),
            },
            {
                "in": (
                    (ADDR[0], [(ADDR[1], 666)], b"Hello, World!!!"),
                    {
                        "btc_change": 199909140 - 666 - 1000,
                        "btc_fee": 1000,
                        "btc_in": 199909140,
                        "btc_out": 666,
                        "data": b"TESTXXXXHello, World!",
                        "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                        "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac0000000000000000176a152a504df746f834422d58bbc1cbf0522d6c7a0911bf9258ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    },
                    {"exact_fee": 1000},
                ),
                "error": (
                    exceptions.ComposeError,
                    "Sanity check error: data does not match the output data",
                ),
            },
        ],
        "prepare_construct_params": [
            {
                "in": (
                    {
                        "fee_per_kb": 1024,
                        "fee_provided": 666,
                        "dust_return_pubkey": DEFAULT_PARAMS["pubkey"][ADDR[0]],
                        "return_psbt": True,
                        "regular_dust_size": 357,
                        "multisig_dust_size": 1200,
                        "extended_tx_info": True,
                        "old_style_api": True,
                        "p2sh_pretx_txid": "aabbb",
                        "segwit": True,
                        "unspent_tx_hash": "aabbcc",
                    },
                ),
                "out": (
                    {
                        "sat_per_vbyte": 1,
                        "max_fee": 666,
                        "mutlisig_pubkey": DEFAULT_PARAMS["pubkey"][ADDR[0]],
                        "verbose": True,
                        "regular_dust_size": 357,
                        "multisig_dust_size": 1200,
                        "extended_tx_info": True,
                        "old_style_api": True,
                        "p2sh_pretx_txid": "aabbb",
                        "segwit": True,
                        "unspent_tx_hash": "aabbcc",
                    },
                    [
                        "The `fee_per_kb` parameter is deprecated, use `sat_per_vbyte` instead",
                        "The `fee_provided` parameter is deprecated, use `max_fee` instead",
                        "The `dust_return_pubkey` parameter is deprecated, use `mutlisig_pubkey` instead",
                        "The `return_psbt` parameter is deprecated, use `verbose` instead",
                        "The `regular_dust_size` parameter is deprecated, automatically calculated",
                        "The `multisig_dust_size` parameter is deprecated, automatically calculated",
                        "The `extended_tx_info` parameter is deprecated (api v1 only), use api v2 instead",
                        "The `old_style_api` parameter is deprecated (api v1 only), use api v2 instead",
                        "The `p2sh_pretx_txid` parameter is ignored, p2sh disabled",
                        "The `segwit` parameter is ignored, segwit automatically detected",
                        "The `unspent_tx_hash` parameter is deprecated, use `inputs_set` instead",
                    ],
                ),
            },
            {
                "in": (
                    {
                        "fee_per_kb": 1023,
                        "fee_provided": 666,
                        "dust_return_pubkey": DEFAULT_PARAMS["pubkey"][ADDR[0]],
                        "return_psbt": True,
                        "regular_dust_size": 357,
                        "multisig_dust_size": 1200,
                        "extended_tx_info": True,
                        "old_style_api": True,
                        "p2sh_pretx_txid": "aabbb",
                        "segwit": True,
                        "unspent_tx_hash": "aabbcc",
                    },
                ),
                "out": (
                    {
                        "sat_per_vbyte": 1023 / 1024,
                        "max_fee": 666,
                        "mutlisig_pubkey": DEFAULT_PARAMS["pubkey"][ADDR[0]],
                        "verbose": True,
                        "regular_dust_size": 357,
                        "multisig_dust_size": 1200,
                        "extended_tx_info": True,
                        "old_style_api": True,
                        "p2sh_pretx_txid": "aabbb",
                        "segwit": True,
                        "unspent_tx_hash": "aabbcc",
                    },
                    [
                        "The `fee_per_kb` parameter is deprecated, use `sat_per_vbyte` instead",
                        "The `fee_provided` parameter is deprecated, use `max_fee` instead",
                        "The `dust_return_pubkey` parameter is deprecated, use `mutlisig_pubkey` instead",
                        "The `return_psbt` parameter is deprecated, use `verbose` instead",
                        "The `regular_dust_size` parameter is deprecated, automatically calculated",
                        "The `multisig_dust_size` parameter is deprecated, automatically calculated",
                        "The `extended_tx_info` parameter is deprecated (api v1 only), use api v2 instead",
                        "The `old_style_api` parameter is deprecated (api v1 only), use api v2 instead",
                        "The `p2sh_pretx_txid` parameter is ignored, p2sh disabled",
                        "The `segwit` parameter is ignored, segwit automatically detected",
                        "The `unspent_tx_hash` parameter is deprecated, use `inputs_set` instead",
                    ],
                ),
            },
        ],
        "compose_transaction": [
            {
                "in": (
                    "send",
                    {
                        "source": ADDR[0],
                        "destination": ADDR[1],
                        "asset": "XCP",
                        "quantity": 10,
                    },
                    {},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0322020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000000000001e6a1c2a504df746f83442653dd7ada4dc727a030865749e9fba5aee7a3310d759ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
                },
            },
            {
                "in": (
                    "burn",
                    {
                        "source": ADDR[1],
                        "quantity": DP["burn_quantity"],
                    },
                    {"encoding": "multisig"},
                ),
                "out": {
                    "rawtransaction": "0200000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce40000000000ffffffff02800bb203000000001976a914a11b66a67b3ff69671c8f82254099faf374b800e88acdad24302000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000"
                },
            },
            {
                "in": (
                    "issuance",
                    {
                        "source": ADDR[0],
                        "transfer_destination": None,
                        "asset": "BSSET",
                        "quantity": 1000,
                        "divisible": True,
                        "description": "",
                    },
                    {"encoding": "multisig"},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210358415bf04af834423d3dd7adb2dc727a03086e897d9fba5aee7a331919e487d6210254da540fb2663b75e6c3cc61190ad0c2431643bab28ced783cd94079bbe72447210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
                },
            },
            {
                "in": (
                    "order",
                    {
                        "source": ADDR[0],
                        "give_asset": "BTC",
                        "give_quantity": DP["small"],
                        "get_asset": "XCP",
                        "get_quantity": DP["small"] * 2,
                        "expiration": DP["expiration"],
                        "fee_required": 0,
                    },
                    {"encoding": "multisig", "fee_provided": DP["fee_provided"]},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff02e8030000000000006951210348415bf04af834423d3dd7adaedc727a030865759e9fba5aee78c9ea71e5870f210354da540fb2673b75e6c3c994f80ad0c8431643bab28ced783cd94079bbe72445210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b053ae4056ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "warnings": [
                        "The `fee_provided` parameter is deprecated, use `max_fee` instead"
                    ],
                },
            },
            {
                "mock_protocol_changes": {"enhanced_sends": True},
                "in": (
                    "send",
                    {
                        "memo": "0102030405",
                        "memo_is_hex": True,
                        "source": ADDR[0],
                        "destination": ADDR[1],
                        "asset": "XCP",
                        "quantity": DP["small"],
                    },
                    {},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff020000000000000000386a362a504df746f83442653dd7afa4dc727a030865749e9fba5aec80c39a9e68edbc79e78ed45723c1072c38aededa458f95fa42b8b188e8115cea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
                },
            },
            {
                "in": (
                    "attach",
                    {
                        "source": ADDR[0],
                        "asset": "XCP",
                        "quantity": 10,
                    },
                    {"verbose": True},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0310270000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000126a102a504df746f83442006594fdd8ed42060d35ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "btc_in": 199909140,
                    "btc_out": 10000,
                    "btc_change": 199898381,
                    "btc_fee": 759,
                    "data": b"TESTXXXXeXCP|10|",
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "signed_tx_estimated_size": {
                        "vsize": 253,
                        "adjusted_vsize": 253,
                        "sigops_count": 8,
                    },
                    "psbt": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0310270000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000126a102a504df746f83442006594fdd8ed42060d35ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "params": {
                        "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "asset": "XCP",
                        "quantity": 10,
                        "utxo_value": None,
                        "destination_vout": None,
                        "skip_validation": False,
                    },
                    "name": "attach",
                },
            },
            {
                "in": (
                    "attach",
                    {
                        "source": ADDR[0],
                        "asset": "XCP",
                        "quantity": 10,
                        "utxo_value": 666,
                    },
                    {"verbose": True},
                ),
                "out": {
                    "rawtransaction": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000126a102a504df746f83442006594fdd8ed42068359ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "btc_in": 199909140,
                    "btc_out": 666,
                    "btc_change": 199907715,
                    "btc_fee": 759,
                    "data": b"TESTXXXXeXCP|10|",
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "signed_tx_estimated_size": {
                        "vsize": 253,
                        "adjusted_vsize": 253,
                        "sigops_count": 8,
                    },
                    "psbt": "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff039a020000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000126a102a504df746f83442006594fdd8ed42068359ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "params": {
                        "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                        "asset": "XCP",
                        "quantity": 10,
                        "utxo_value": 666,
                        "destination_vout": None,
                        "skip_validation": False,
                    },
                    "name": "attach",
                },
            },
            {
                "in": (
                    "move",
                    {
                        "source": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
                        "destination": ADDR[1],
                    },
                    {
                        "verbose": True,
                        "inputs_set": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0:999999999:76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                    },
                ),
                "out": {
                    "rawtransaction": "020000000153cfb4ae6c480c588190f1aa3793f710add668328f0e9cc56cf5b3c55c0b9d1e0000000000ffffffff0210270000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac49a09a3b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "btc_in": 999999999,
                    "btc_out": 10000,
                    "btc_change": 999989321,
                    "btc_fee": 678,
                    "data": None,
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "signed_tx_estimated_size": {
                        "vsize": 226,
                        "adjusted_vsize": 226,
                        "sigops_count": 8,
                    },
                    "psbt": "020000000153cfb4ae6c480c588190f1aa3793f710add668328f0e9cc56cf5b3c55c0b9d1e0000000000ffffffff0210270000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac49a09a3b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "params": {
                        "source": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
                        "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "utxo_value": None,
                        "skip_validation": False,
                    },
                    "name": "move",
                },
            },
            {
                "in": (
                    "move",
                    {
                        "source": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
                        "destination": ADDR[1],
                        "utxo_value": 666,
                    },
                    {
                        "verbose": True,
                        "inputs_set": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0:999999999:76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac",
                    },
                ),
                "out": {
                    "rawtransaction": "020000000153cfb4ae6c480c588190f1aa3793f710add668328f0e9cc56cf5b3c55c0b9d1e0000000000ffffffff029a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acbfc49a3b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "btc_in": 999999999,
                    "btc_out": 666,
                    "btc_change": 999998655,
                    "btc_fee": 678,
                    "data": None,
                    "lock_scripts": ["76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac"],
                    "signed_tx_estimated_size": {
                        "vsize": 226,
                        "adjusted_vsize": 226,
                        "sigops_count": 8,
                    },
                    "psbt": "020000000153cfb4ae6c480c588190f1aa3793f710add668328f0e9cc56cf5b3c55c0b9d1e0000000000ffffffff029a020000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acbfc49a3b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000",
                    "params": {
                        "source": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
                        "destination": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                        "utxo_value": 666,
                        "skip_validation": False,
                    },
                    "name": "move",
                },
            },
        ],
    },
}
