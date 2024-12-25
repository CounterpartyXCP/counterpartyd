SCENARIO = [
    {
        "title": "Create asset MYASSETA",
        "transaction": "issuance",
        "source": "$ADDRESS_1",
        "params": {
            "asset": "MYASSETA",
            "quantity": 1000 * 10**8,
            "divisible": True,
            "description": "My super asset A",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=CREDIT,ASSET_ISSUANCE,ASSET_CREATION,DEBIT",
                "result": [
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "address": "$ADDRESS_1",
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "issuance",
                            "event": "$TX_HASH",
                            "quantity": 100000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "ASSET_ISSUANCE",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "asset": "MYASSETA",
                            "asset_longname": None,
                            "asset_events": "creation",
                            "block_index": "$BLOCK_INDEX",
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "My super asset A",
                            "description_locked": False,
                            "divisible": True,
                            "fee_paid": 50000000,
                            "issuer": "$ADDRESS_1",
                            "locked": False,
                            "quantity": 100000000000,
                            "reset": False,
                            "source": "$ADDRESS_1",
                            "status": "valid",
                            "transfer": False,
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "ASSET_CREATION",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "asset_id": "103804245870",
                            "asset_longname": None,
                            "asset_name": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "issuance fee",
                            "address": "$ADDRESS_1",
                            "asset": "XCP",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 50000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Attach asset to UTXO",
        "transaction": "attach",
        "source": "$ADDRESS_1",
        "params": {
            "asset": "MYASSETA",
            "quantity": 10 * 10**8,
        },
        "set_variables": {
            "UTXO_ATTACH_1_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=ATTACH_TO_UTXO,INCREMENT_TRANSACTION_COUNT,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ATTACH_TO_UTXO",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "fee_paid": 0,
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$ADDRESS_1",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "attach",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "attach to utxo",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_1",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "action": "attach to utxo",
                            "address": "$ADDRESS_1",
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "INCREMENT_TRANSACTION_COUNT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "block_index": "$BLOCK_INDEX",
                            "count": 1,
                            "transaction_id": 101,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Move assets from UTXO to UTXO",
        "transaction": "movetoutxo",
        "source": "$UTXO_ATTACH_1_TX_HASH:0",
        "params": {
            "destination": "$ADDRESS_4",
            "exact_fee": 0,
            "inputs_source": "$ADDRESS_1",
        },
        "set_variables": {
            "UTXO_MOVE_1_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=UTXO_MOVE,CREDIT,DEBIT,DISPENSER_UPDATE,NEW_TRANSACTION",
                "result": [
                    {
                        "event": "UTXO_MOVE",
                        "event_index": "$EVENT_INDEX_7",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXO_ATTACH_1_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "move",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_4",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXO_ATTACH_1_TX_HASH:0",
                            "utxo_address": "$ADDRESS_1",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DISPENSER_UPDATE",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "asset": "XCP",
                            "give_remaining": 0,
                            "source": "$ADDRESS_11",
                            "status": 10,
                            "tx_hash": "$DISPENSER_4_TX_HASH",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "address": "$ADDRESS_1",
                            "asset": "XCP",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "close dispenser",
                            "event": "$DISPENSER_4_CLOSE_TX_HASH",
                            "quantity": 20,
                            "tx_index": 0,
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "NEW_TRANSACTION",
                        "event_index": "$EVENT_INDEX_2",
                        "params": {
                            "block_hash": "$BLOCK_HASH",
                            "block_index": "$BLOCK_INDEX",
                            "block_time": "$BLOCK_TIME",
                            "btc_amount": None,
                            "data": None,
                            "destination": None,
                            "fee": None,
                            "source": "",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "utxos_info": "$UTXO_ATTACH_1_TX_HASH:0 $TX_HASH:0 1 ",
                            "transaction_type": "utxomove",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Detach assets from UTXO",
        "transaction": "detach",
        "source": "$UTXO_MOVE_1_TX_HASH:0",
        "params": {
            "destination": "$ADDRESS_5",
            "inputs_source": "$ADDRESS_4",
        },
        "set_variables": {
            "UTXO_DETACH_1_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=DETACH_FROM_UTXO,INCREMENT_TRANSACTION_COUNT,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "DETACH_FROM_UTXO",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$ADDRESS_5",
                            "fee_paid": 0,
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXO_MOVE_1_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "detach",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "address": "$ADDRESS_5",
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "detach from utxo",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "detach from utxo",
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXO_MOVE_1_TX_HASH:0",
                            "utxo_address": "$ADDRESS_4",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Attach asset to new UTXO",
        "transaction": "attach",
        "source": "$ADDRESS_1",
        "params": {
            "asset": "MYASSETA",
            "quantity": 10 * 10**8,
        },
        "set_variables": {
            "UTXO_ATTACH_2_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=ATTACH_TO_UTXO,INCREMENT_TRANSACTION_COUNT,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ATTACH_TO_UTXO",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "fee_paid": 0,
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$ADDRESS_1",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "attach",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "attach to utxo",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_1",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "action": "attach to utxo",
                            "address": "$ADDRESS_1",
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "INCREMENT_TRANSACTION_COUNT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "block_index": "$BLOCK_INDEX",
                            "count": 1,
                            "transaction_id": 101,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Attach asset to new UTXO 2",
        "transaction": "attach",
        "source": "$ADDRESS_5",
        "params": {
            "asset": "MYASSETA",
            "quantity": 10 * 10**8,
        },
        "set_variables": {
            "UTXO_ATTACH_3_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=ATTACH_TO_UTXO,INCREMENT_TRANSACTION_COUNT,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ATTACH_TO_UTXO",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "fee_paid": 0,
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$ADDRESS_5",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "attach",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "attach to utxo",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_5",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "action": "attach to utxo",
                            "address": "$ADDRESS_5",
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "INCREMENT_TRANSACTION_COUNT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "block_index": "$BLOCK_INDEX",
                            "count": 1,
                            "transaction_id": 101,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
    {
        "title": "Move assets from 2 UTXOs to UTXO",
        "transaction": "movetoutxo",
        "source": "$UTXO_ATTACH_3_TX_HASH:0",
        "params": {
            "destination": "$ADDRESS_6",
            "inputs_set": "$UTXO_ATTACH_2_TX_HASH:0,$UTXO_ATTACH_2_TX_HASH:2",
            "use_utxos_with_balances": True,
        },
        "set_variables": {
            "UTXO_MOVE_2_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=UTXO_MOVE,CREDIT,DEBIT,NEW_TRANSACTION",
                "result": [
                    {
                        "event": "UTXO_MOVE",
                        "event_index": "$EVENT_INDEX_8",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "msg_index": 1,
                            "quantity": 1000000000,
                            "source": "$UTXO_ATTACH_2_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "move",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_7",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_6",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXO_ATTACH_2_TX_HASH:0",
                            "utxo_address": "$ADDRESS_1",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "UTXO_MOVE",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXO_ATTACH_3_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "send_type": "move",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_6",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXO_ATTACH_3_TX_HASH:0",
                            "utxo_address": "$ADDRESS_5",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "NEW_TRANSACTION",
                        "event_index": "$EVENT_INDEX_2",
                        "params": {
                            "block_hash": "$BLOCK_HASH",
                            "block_index": "$BLOCK_INDEX",
                            "block_time": "$BLOCK_TIME",
                            "btc_amount": None,
                            "data": None,
                            "destination": None,
                            "fee": None,
                            "source": "",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                            "utxos_info": "$UTXO_ATTACH_3_TX_HASH:0,$UTXO_ATTACH_2_TX_HASH:0 $TX_HASH:0 1 ",
                            "transaction_type": "utxomove",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            },
            {
                "url": "assets/MYASSETA/balances",
                "result": [
                    {
                        "address": "$ADDRESS_1",
                        "asset": "MYASSETA",
                        "asset_longname": None,
                        "quantity": 98000000000,
                        "utxo": None,
                        "utxo_address": None,
                    },
                    {
                        "address": None,
                        "asset": "MYASSETA",
                        "asset_longname": None,
                        "quantity": 2000000000,
                        "utxo": "$TX_HASH:0",
                        "utxo_address": "$ADDRESS_6",
                    },
                ],
            },
            {
                "url": "addresses/$ADDRESS_6/balances",
                "result": [
                    {
                        "address": None,
                        "asset": "MYASSETA",
                        "asset_longname": None,
                        "quantity": 2000000000,
                        "utxo": "$TX_HASH:0",
                        "utxo_address": "$ADDRESS_6",
                    },
                    {
                        "address": "$ADDRESS_6",
                        "asset": "XCP",
                        "asset_longname": None,
                        "quantity": 74999988167,
                        "utxo": None,
                        "utxo_address": None,
                    },
                ],
            },
            {
                "url": "addresses/balances?addresses=$ADDRESS_6,$ADDRESS_1,$ADDRESS_5",
                "result": [
                    {
                        "addresses": [
                            {
                                "address": "$ADDRESS_1",
                                "quantity": 98000000000,
                                "utxo": None,
                                "utxo_address": None,
                            },
                            {
                                "address": None,
                                "quantity": 2000000000,
                                "utxo": "$TX_HASH:0",
                                "utxo_address": "$ADDRESS_6",
                            },
                        ],
                        "asset": "MYASSETA",
                        "asset_longname": None,
                        "total": 100000000000,
                    },
                    {
                        "addresses": [
                            {
                                "address": "$ADDRESS_1",
                                "quantity": 84749988206,
                                "utxo": None,
                                "utxo_address": None,
                            },
                            {
                                "address": "$ADDRESS_5",
                                "quantity": 74999998167,
                                "utxo": None,
                                "utxo_address": None,
                            },
                            {
                                "address": "$ADDRESS_6",
                                "quantity": 74999988167,
                                "utxo": None,
                                "utxo_address": None,
                            },
                        ],
                        "asset": "XCP",
                        "asset_longname": None,
                        "total": 234749974540,
                    },
                ],
            },
            {
                "url": "addresses/$ADDRESS_6/balances/MYASSETA",
                "result": [
                    {
                        "address": None,
                        "asset": "MYASSETA",
                        "asset_longname": None,
                        "quantity": 2000000000,
                        "utxo": "$TX_HASH:0",
                        "utxo_address": "$ADDRESS_6",
                    }
                ],
            },
        ],
    },
    {
        "title": "Test divident to UTXO",
        "transaction": "dividend",
        "source": "$ADDRESS_1",
        "params": {
            "asset": "MYASSETA",
            "quantity_per_unit": 1 * 10**8,
            "dividend_asset": "XCP",
        },
        "set_variables": {
            "DIVIDEND_1_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=ASSET_DIVIDEND,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ASSET_DIVIDEND",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "MYASSETA",
                            "block_index": "$BLOCK_INDEX",
                            "dividend_asset": "XCP",
                            "fee_paid": 20000,
                            "quantity_per_unit": 100000000,
                            "source": "$ADDRESS_1",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "address": None,
                            "asset": "XCP",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "dividend",
                            "event": "$TX_HASH",
                            "quantity": 2000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXO_MOVE_2_TX_HASH:0",
                            "utxo_address": "$ADDRESS_6",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "action": "dividend fee",
                            "address": "$ADDRESS_1",
                            "asset": "XCP",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 20000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "dividend",
                            "address": "$ADDRESS_1",
                            "asset": "XCP",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 2000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": None,
                            "utxo_address": None,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                ],
            }
        ],
    },
]
