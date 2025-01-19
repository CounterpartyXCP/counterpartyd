# Transactions executed to generate the database used by unit tests

from .params import ADDR, MULTISIGADDR, P2SH_ADDR, P2WPKH_ADDR
from .params import DEFAULT_PARAMS as DP

UNITTEST_FIXTURE = [
    [
        "burn",
        {
            "source": ADDR[0],
            "quantity": DP["burn_quantity"],
            "overburn": False,
            "skip_validation": False,
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "DIVISIBLE",
            "quantity": DP["quantity"] * 1000,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Divisible asset",
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "NODIVISIBLE",
            "quantity": 1000,
            "transfer_destination": None,
            "divisible": False,
            "lock": None,
            "reset": None,
            "description": "No divisible asset",
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "CALLABLE",
            "quantity": 1000,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Callable asset",
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "LOCKED",
            "quantity": 1000,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Locked asset",
        },
        {"encoding": "multisig"},
    ],
    ["issuance", (ADDR[0], "LOCKED", 0, None, True, None, None, "LOCK"), {"encoding": "multisig"}],
    [
        "order",
        (ADDR[0], "XCP", DP["quantity"], "DIVISIBLE", DP["quantity"], 2000, 0),
        {"encoding": "multisig"},
    ],
    ["send", (ADDR[0], ADDR[1], "DIVISIBLE", DP["quantity"]), {"encoding": "multisig"}, None],
    ["send", (ADDR[0], ADDR[1], "XCP", DP["quantity"]), {"encoding": "multisig"}, None],
    [
        "order",
        (ADDR[0], "XCP", DP["quantity"], "DIVISIBLE", DP["quantity"], 2000, 0),
        {"encoding": "multisig"},
    ],
    [
        "order",
        (
            ADDR[0],
            "XCP",
            DP["quantity"],
            "BTC",
            round(DP["quantity"] / 100),
            2000,
            DP["fee_required"],
        ),
        {"encoding": "multisig"},
    ],
    [
        "order",
        (ADDR[0], "BTC", round(DP["quantity"] / 150), "XCP", DP["quantity"], 2000, 0),
        {"encoding": "multisig", "fee_provided": DP["fee_provided"]},
    ],
    ["send", (ADDR[0], MULTISIGADDR[0], "XCP", DP["quantity"] * 3), {"encoding": "multisig"}, None],
    [
        "send",
        (ADDR[0], MULTISIGADDR[0], "DIVISIBLE", DP["quantity"] * 10),
        {"encoding": "multisig"},
        None,
    ],
    ["send", (ADDR[0], ADDR[1], "NODIVISIBLE", 5), {"encoding": "multisig"}, None],
    ["send", (ADDR[0], MULTISIGADDR[0], "NODIVISIBLE", 10), {"encoding": "multisig"}, None],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "MAXI",
            "quantity": 2**63 - 1,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Maximum quantity",
        },
        {"encoding": "multisig"},
    ],
    [
        "broadcast",
        (ADDR[0], 1388000000, 1, DP["fee_multiplier"], "Unit Test"),
        {"encoding": "multisig"},
    ],
    ["broadcast", (ADDR[2], 1288000000, 1, 0.0, "lock"), {"encoding": "multisig"}],
    ["bet", (ADDR[0], ADDR[0], 1, 1388000001, 9, 9, 0.0, 5040, 100), {"encoding": "multisig"}],
    ["bet", (ADDR[1], ADDR[0], 0, 1388000001, 9, 9, 0.0, 5040, 100), {"encoding": "multisig"}],
    ["create_next_block", 100],  # 310100
    ["bet", (ADDR[1], ADDR[0], 3, 1388000200, 10, 10, 0.0, 5040, 1000), {"encoding": "multisig"}],
    [
        "broadcast",
        (ADDR[0], 1388000002, 1, DP["fee_multiplier"], "Unit Test"),
        {"encoding": "multisig"},
    ],
    ["burn", (ADDR[4], DP["burn_quantity"]), {"encoding": "multisig"}],
    ["burn", (ADDR[5], DP["burn_quantity"]), {"encoding": "multisig"}],
    ["burn", (ADDR[6], DP["burn_quantity"]), {"encoding": "multisig"}],
    ["burn", (ADDR[8], DP["burn_verysmall_quantity"]), {"encoding": "multisig"}],
    ["dispenser", (ADDR[5], "XCP", 100, 100, 100, 0), {"encoding": "opreturn"}],
    ["burn", (P2SH_ADDR[0], int(DP["burn_quantity"] / 2)), {"encoding": "opreturn"}],
    [
        "issuance",
        (P2SH_ADDR[0], "PAYTOSCRIPT", 1000, None, False, None, None, "PSH issued asset"),
        {"encoding": "multisig", "multisig_pubkey": DP["pubkey"][ADDR[0]]},
    ],
    [
        "send",
        (ADDR[0], P2SH_ADDR[0], "DIVISIBLE", DP["quantity"]),
        {"encoding": "multisig", "multisig_pubkey": DP["pubkey"][ADDR[0]]},
        None,
    ],
    [
        "broadcast",
        (P2SH_ADDR[0], 1388000002, 1, DP["fee_multiplier"], "Unit Test"),
        {"encoding": "opreturn"},
    ],
    [
        "bet",
        (P2SH_ADDR[0], P2SH_ADDR[0], 3, 1388000200, 10, 10, 0.0, 5040, 1000),
        {"encoding": "opreturn"},
    ],
    # locked with an issuance after lock
    [
        "issuance",
        {
            "address": ADDR[6],
            "asset": "LOCKEDPREV",
            "quantity": 1000,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Locked asset",
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[6],
            "asset": "LOCKEDPREV",
            "quantity": 0,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "LOCK",
        },
        {"encoding": "multisig"},
    ],
    [
        "issuance",
        {
            "address": ADDR[6],
            "asset": "LOCKEDPREV",
            "quantity": 0,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "changed",
        },
        {"encoding": "multisig"},
    ],
    ["burn", (P2WPKH_ADDR[0], DP["burn_quantity"]), {"encoding": "opreturn"}],
    ["create_next_block", 480],
    # force 2 enhanced sends
    [
        "send",
        (ADDR[0], ADDR[1], "XCP", DP["quantity"], "hello", False, True),
        {"encoding": "opreturn"},
        {"enhanced_sends": True},
    ],
    [
        "send",
        (ADDR[1], ADDR[0], "XCP", DP["quantity"], "fade0001", True, True),
        {"encoding": "opreturn"},
        {"enhanced_sends": True},
    ],
    ["create_next_block", 485],
    [
        "broadcast",
        (ADDR[4], 1388000000, 1, DP["fee_multiplier"], "Unit Test"),
        {"encoding": "multisig"},
    ],
    ["bet", (ADDR[4], ADDR[4], 1, 1388000001, 9, 9, 0.0, 5040, 100), {"encoding": "multisig"}],
    # To test REQUIRE_MEMO
    [
        "broadcast",
        (ADDR[4], 1388000002, 1, 0.0, "options 0"),
        {"encoding": "multisig"},
        {"options_require_memo": True},
    ],
    ["broadcast", (ADDR[4], 1388000003, 1, 0.0, "lock"), {"encoding": "multisig"}],
    # To test REQUIRE_MEMO
    [
        "broadcast",
        (ADDR[6], 1388000004, 1, 0.0, "options 1"),
        {"encoding": "multisig"},
        {"options_require_memo": True},
    ],
    # ['create_next_block', 490],
    [
        "order",
        (
            ADDR[0],
            "XCP",
            DP["quantity"],
            "BTC",
            round(DP["quantity"] / 125),
            2000,
            DP["fee_required"],
        ),
        {"encoding": "multisig"},
    ],
    [
        "order",
        (ADDR[1], "BTC", round(DP["quantity"] / 125), "XCP", DP["quantity"], 2000, 0),
        {"encoding": "multisig", "exact_fee": DP["fee_provided"]},
    ],
    ["burn", (ADDR[2], DP["burn_quantity"]), {"encoding": "multisig"}],
    [
        "issuance",
        {
            "address": ADDR[2],
            "asset": "DIVIDEND",
            "quantity": 100,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Test dividend",
        },
        {"encoding": "multisig"},
    ],
    ["send", (ADDR[2], ADDR[3], "DIVIDEND", 10), {"encoding": "multisig"}, None],
    ["send", (ADDR[2], ADDR[3], "XCP", 92945878046), {"encoding": "multisig"}, None],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "PARENT",
            "quantity": DP["quantity"] * 1,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Parent asset",
        },
        {"encoding": "opreturn"},
    ],
    [
        "issuance",
        {
            "address": ADDR[0],
            "asset": "PARENT.already.issued",
            "quantity": DP["quantity"] * 1,
            "transfer_destination": None,
            "divisible": True,
            "lock": None,
            "reset": None,
            "description": "Child of parent",
        },
        {"encoding": "opreturn"},
    ],
    [
        "fairminter",
        (ADDR[0], "FREEFAIRMIN", "", 0, 1, 10),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairminter",
        (ADDR[0], "PAIDFAIRMIN", "", 10, 1, 0),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairmint",
        (ADDR[0], "FREEFAIRMIN", 0),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairminter",
        (
            ADDR[0],  # source
            "RAIDFAIRMIN",  # asset
            "",  # asset_parent
            10,  # price
            1,  # quantity_by_price
            10,  # max_mint_per_tx
            30,  # hard_cap
            20,  # premint_quantity
        ),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairminter",
        (
            ADDR[0],  # source
            "QAIDFAIRMIN",  # asset
            "",  # asset_parent,
            10,  # price=0,
            1,  # quantity_by_price
            0,  # max_mint_per_tx,
            50,  # hard_cap=0,
            20,  # premint_quantity=0,
            0,  # start_block=0,
            0,  # end_block=0,
            20,  # soft_cap=0,
            400000,  # soft_cap_deadline_block=0,
            0.5,  # minted_asset_commission=0.0,
        ),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairminter",
        (
            ADDR[1],  # source
            "A160361285792733729",  # asset
            "",  # asset_parent,
            10,  # price=0,
            1,  # quantity_by_price
            0,  # max_mint_per_tx,
            50,  # hard_cap=0,
            20,  # premint_quantity=0,
            0,  # start_block=0,
            0,  # end_block=0,
            20,  # soft_cap=0,
            310520,  # soft_cap_deadline_block=0,
            0.3,  # minted_asset_commission=0.0,
            False,  # burn_payment=False,
            True,  # lock_description=False,
            True,  # lock_quantity
            True,  # divisible
            "softcap description",
        ),
        {"encoding": "multisig"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairmint",
        (ADDR[1], "A160361285792733729", 10),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "fairmint",
        (ADDR[1], "A160361285792733729", 20),
        {"encoding": "opreturn"},
        {"short_tx_type_id": True, "fairminter": True},
    ],
    [
        "attach",
        (ADDR[0], "XCP", 100),
        {"encoding": "multisig"},
        {"short_tx_type_id": True, "utxo_support": True, "spend_utxo_to_detach": True},
    ],
    [
        "attach",
        (
            ADDR[0],
            "DIVISIBLE",
            1,
        ),
        {"encoding": "multisig"},
        {"short_tx_type_id": True, "utxo_support": True, "spend_utxo_to_detach": True},
    ],
    [
        "issuance",
        (ADDR[5], "TESTDISP", 1000, None, False, None, None, "Test dispensers asset"),
        {"encoding": "multisig"},
    ],
    ["dispenser", (ADDR[5], "TESTDISP", 100, 100, 100, 0), {"encoding": "opreturn"}],
    ["create_next_block", 703],
]
