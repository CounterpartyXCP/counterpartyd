# soft cap not reached
SCENARIO = [
    {
        "title": "Create FAIRMINTB fairminter",
        "transaction": "fairminter",
        "source": "$ADDRESS_1",
        "params": {
            "asset": "FAIRMINTB",
            "price": 1,
            "hard_cap": 100 * 10**8,
            "soft_cap": 10 * 10**8,
            "soft_cap_deadline_block": 130,
        },
        "set_variables": {
            "FAIRMINTB_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "assets/FAIRMINTB/fairminters",
                "result": [
                    {
                        "tx_hash": "$TX_HASH",
                        "tx_index": 14,
                        "block_index": 126,
                        "source": "$ADDRESS_1",
                        "asset": "FAIRMINTB",
                        "asset_parent": "",
                        "asset_longname": "",
                        "description": "",
                        "price": 1,
                        "hard_cap": 100 * 10**8,
                        "burn_payment": False,
                        "max_mint_per_tx": 0,
                        "premint_quantity": 0,
                        "start_block": 0,
                        "end_block": 0,
                        "minted_asset_commission_int": 0,
                        "soft_cap": 10 * 10**8,
                        "soft_cap_deadline_block": 130,
                        "lock_description": False,
                        "lock_quantity": False,
                        "divisible": True,
                        "pre_minted": False,
                        "status": "open",
                        "earned_quantity": None,
                        "commission": None,
                        "paid_quantity": None,
                        "confirmed": True,
                    }
                ],
            }
        ],
    },
    {
        "title": "mint FAIRMINTB with ADDRESS_2",
        "transaction": "fairmint",
        "source": "$ADDRESS_2",
        "params": {
            "asset": "FAIRMINTB",
            "quantity": 1 * 10**8,
        },
        "set_variables": {
            "FAIRMINTB_WITH_ADDRESS_2_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/127/events?event_name=CREDIT,DEBIT,ASSET_ISSUANCE,NEW_FAIRMINT",
                "result": [
                    {
                        "event": "ASSET_ISSUANCE",
                        "event_index": 128,
                        "params": {
                            "asset": "FAIRMINTB",
                            "asset_longname": "",
                            "block_index": 127,
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "",
                            "description_locked": False,
                            "divisible": True,
                            "fair_minting": True,
                            "fee_paid": 0,
                            "issuer": "$ADDRESS_1",
                            "locked": False,
                            "msg_index": 0,
                            "quantity": 100000000,
                            "reset": False,
                            "source": "$ADDRESS_2",
                            "status": "valid",
                            "transfer": False,
                            "tx_hash": "$TX_HASH",
                            "tx_index": 15,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "NEW_FAIRMINT",
                        "event_index": 127,
                        "params": {
                            "asset": "FAIRMINTB",
                            "block_index": 127,
                            "commission": 0,
                            "earn_quantity": 100000000,
                            "fairminter_tx_hash": "$FAIRMINTB_TX_HASH",
                            "paid_quantity": 100000000,
                            "source": "$ADDRESS_2",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": 15,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 126,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "FAIRMINTB",
                            "block_index": 127,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 15,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 125,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "XCP",
                            "block_index": 127,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 15,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": 124,
                        "params": {
                            "action": "escrowed fairmint",
                            "address": "$ADDRESS_2",
                            "asset": "XCP",
                            "block_index": 127,
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 15,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "mint FAIRMINTB with ADDRESS_3",
        "transaction": "fairmint",
        "source": "$ADDRESS_3",
        "params": {
            "asset": "FAIRMINTB",
            "quantity": 1 * 10**8,
        },
        "set_variables": {
            "FAIRMINTB_WITH_ADDRESS_3_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/128/events?event_name=CREDIT,DEBIT,ASSET_ISSUANCE,NEW_FAIRMINT",
                "result": [
                    {
                        "event": "ASSET_ISSUANCE",
                        "event_index": 137,
                        "params": {
                            "asset": "FAIRMINTB",
                            "asset_longname": "",
                            "block_index": 128,
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "",
                            "description_locked": False,
                            "divisible": True,
                            "fair_minting": True,
                            "fee_paid": 0,
                            "issuer": "$ADDRESS_1",
                            "locked": False,
                            "msg_index": 0,
                            "quantity": 100000000,
                            "reset": False,
                            "source": "$ADDRESS_3",
                            "status": "valid",
                            "transfer": False,
                            "tx_hash": "$TX_HASH",
                            "tx_index": 16,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "NEW_FAIRMINT",
                        "event_index": 136,
                        "params": {
                            "asset": "FAIRMINTB",
                            "block_index": 128,
                            "commission": 0,
                            "earn_quantity": 100000000,
                            "fairminter_tx_hash": "$FAIRMINTB_TX_HASH",
                            "paid_quantity": 100000000,
                            "source": "$ADDRESS_3",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": 16,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 135,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "FAIRMINTB",
                            "block_index": 128,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 16,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 134,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "XCP",
                            "block_index": 128,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 16,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": 133,
                        "params": {
                            "action": "escrowed fairmint",
                            "address": "$ADDRESS_3",
                            "asset": "XCP",
                            "block_index": 128,
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 16,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "mint FAIRMINTB with ADDRESS_4",
        "transaction": "fairmint",
        "source": "$ADDRESS_4",
        "params": {
            "asset": "FAIRMINTB",
            "quantity": 1 * 10**8,
        },
        "set_variables": {
            "FAIRMINTB_WITH_ADDRESS_4_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/129/events?event_name=CREDIT,DEBIT,ASSET_ISSUANCE,NEW_FAIRMINT",
                "result": [
                    {
                        "event": "ASSET_ISSUANCE",
                        "event_index": 146,
                        "params": {
                            "asset": "FAIRMINTB",
                            "asset_longname": "",
                            "block_index": 129,
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "",
                            "description_locked": False,
                            "divisible": True,
                            "fair_minting": True,
                            "fee_paid": 0,
                            "issuer": "$ADDRESS_1",
                            "locked": False,
                            "msg_index": 0,
                            "quantity": 100000000,
                            "reset": False,
                            "source": "$ADDRESS_4",
                            "status": "valid",
                            "transfer": False,
                            "tx_hash": "$TX_HASH",
                            "tx_index": 17,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "NEW_FAIRMINT",
                        "event_index": 145,
                        "params": {
                            "asset": "FAIRMINTB",
                            "block_index": 129,
                            "commission": 0,
                            "earn_quantity": 100000000,
                            "fairminter_tx_hash": "$FAIRMINTB_TX_HASH",
                            "paid_quantity": 100000000,
                            "source": "$ADDRESS_4",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": 17,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 144,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "FAIRMINTB",
                            "block_index": 129,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 17,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 143,
                        "params": {
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "XCP",
                            "block_index": 129,
                            "calling_function": "escrowed fairmint",
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 17,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": 142,
                        "params": {
                            "action": "escrowed fairmint",
                            "address": "$ADDRESS_4",
                            "asset": "XCP",
                            "block_index": 129,
                            "event": "$TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 17,
                            "utxo": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "mint empty block to trigger soft cap checking",
        "transaction": "mine_blocks",
        "params": {"blocks": 1},
        "controls": [
            {
                "url": "blocks/130/events?event_name=ASSET_DESTRUCTION,ASSET_ISSUANCE,FAIRMINTER_UPDATE,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ASSET_DESTRUCTION",
                        "event_index": 157,
                        "params": {
                            "asset": "FAIRMINTB",
                            "block_index": 130,
                            "quantity": 300000000,
                            "source": "$ADDRESS_1",
                            "status": "valid",
                            "tag": "soft cap not reached",
                            "tx_hash": "$FAIRMINTB_TX_HASH",
                            "tx_index": 14,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "ASSET_ISSUANCE",
                        "event_index": 156,
                        "params": {
                            "asset": "FAIRMINTB",
                            "asset_longname": "",
                            "block_index": 130,
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "",
                            "description_locked": False,
                            "divisible": True,
                            "fair_minting": False,
                            "fee_paid": 0,
                            "issuer": "$ADDRESS_1",
                            "locked": False,
                            "msg_index": 1,
                            "quantity": 0,
                            "reset": False,
                            "source": "$ADDRESS_4",
                            "status": "valid",
                            "transfer": False,
                            "tx_hash": "$FAIRMINTB_WITH_ADDRESS_4_TX_HASH",
                            "tx_index": 17,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "FAIRMINTER_UPDATE",
                        "event_index": 155,
                        "params": {"status": "closed", "tx_hash": "$FAIRMINTB_TX_HASH"},
                        "tx_hash": None,
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 154,
                        "params": {
                            "address": "$ADDRESS_4",
                            "asset": "XCP",
                            "block_index": 130,
                            "calling_function": "fairmint refund",
                            "event": "$FAIRMINTB_WITH_ADDRESS_4_TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 17,
                            "utxo": None,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 153,
                        "params": {
                            "address": "$ADDRESS_3",
                            "asset": "XCP",
                            "block_index": 130,
                            "calling_function": "fairmint refund",
                            "event": "$FAIRMINTB_WITH_ADDRESS_3_TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 16,
                            "utxo": None,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "CREDIT",
                        "event_index": 152,
                        "params": {
                            "address": "$ADDRESS_2",
                            "asset": "XCP",
                            "block_index": 130,
                            "calling_function": "fairmint refund",
                            "event": "$FAIRMINTB_WITH_ADDRESS_2_TX_HASH",
                            "quantity": 100000000,
                            "tx_index": 15,
                            "utxo": None,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "DEBIT",
                        "event_index": 151,
                        "params": {
                            "action": "unescrowed fairmint payment",
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "XCP",
                            "block_index": 130,
                            "event": "$FAIRMINTB_TX_HASH",
                            "quantity": 300000000,
                            "tx_index": 0,
                            "utxo": None,
                        },
                        "tx_hash": None,
                    },
                    {
                        "event": "DEBIT",
                        "event_index": 150,
                        "params": {
                            "action": "unescrowed fairmint",
                            "address": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
                            "asset": "FAIRMINTB",
                            "block_index": 130,
                            "event": "$FAIRMINTB_TX_HASH",
                            "quantity": 300000000,
                            "tx_index": 0,
                            "utxo": None,
                        },
                        "tx_hash": None,
                    },
                ],
            }
        ],
    },
]
