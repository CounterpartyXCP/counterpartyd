SCENARIO = [
    {
        "title": "Create asset UTXOASSET",
        "transaction": "issuance",
        "source": "$ADDRESS_7",
        "params": {
            "asset": "UTXOASSET",
            "quantity": 1000 * 10**8,
            "divisible": True,
            "description": "My super asset",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=CREDIT,ASSET_ISSUANCE,ASSET_CREATION,DEBIT",
                "result": [
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "address": "$ADDRESS_7",
                            "asset": "UTXOASSET",
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
                            "asset": "UTXOASSET",
                            "asset_longname": None,
                            "asset_events": "creation",
                            "block_index": "$BLOCK_INDEX",
                            "call_date": 0,
                            "call_price": 0.0,
                            "callable": False,
                            "description": "My super asset",
                            "description_locked": False,
                            "divisible": True,
                            "fee_paid": 50000000,
                            "issuer": "$ADDRESS_7",
                            "locked": False,
                            "quantity": 100000000000,
                            "reset": False,
                            "source": "$ADDRESS_7",
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
                            "asset_id": "4336417415635",
                            "asset_longname": None,
                            "asset_name": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "issuance fee",
                            "address": "$ADDRESS_7",
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
        "source": "$ADDRESS_7",
        "params": {
            "asset": "UTXOASSET",
            "quantity": 10 * 10**8,
        },
        "set_variables": {
            "UTXOASSET_UTXO_1_TX_HASH": "$TX_HASH",
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=ATTACH_TO_UTXO,INCREMENT_TRANSACTION_COUNT,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "ATTACH_TO_UTXO",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "fee_paid": 0,
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$ADDRESS_7",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "INCREMENT_TRANSACTION_COUNT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "block_index": "$BLOCK_INDEX",
                            "count": 3,
                            "transaction_id": 100,
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "attach to utxo",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_7",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_3",
                        "params": {
                            "action": "attach to utxo",
                            "address": "$ADDRESS_7",
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
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
        "title": "Move assets from UTXO to UTXO",
        "transaction": "movetoutxo",
        "source": "$UTXOASSET_UTXO_1_TX_HASH:0",  # first output of attach transaction, second is OP_RETURN
        "no_confirmation": True,
        "params": {
            "destination": "$ADDRESS_8",
            "more_utxos": "$UTXOASSET_UTXO_1_TX_HASH:2",  # third output is change of attach transaction
        },
        "set_variables": {
            "UTXOASSET_UTXO_2_TX_HASH": "$TX_HASH",
            "UTXOASSET_UTXO_2_TX_INDEX": "$TX_INDEX",
        },
        "controls": [
            {
                "url": "mempool/transactions/$TX_HASH/events?event_name=UTXO_MOVE,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "UTXO_MOVE",
                        "params": {
                            "asset": "UTXOASSET",
                            "block_index": 9999999,
                            "destination": "$TX_HASH:0",
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXOASSET_UTXO_1_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "params": {
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_8",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXOASSET_UTXO_1_TX_HASH:0",
                            "utxo_address": "$ADDRESS_7",
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
        "source": "$UTXOASSET_UTXO_2_TX_HASH:0",
        "params": {
            "destination": "$ADDRESS_7",
            "exact_fee": 0,
        },
        "controls": [
            {
                "url": "blocks/$BLOCK_INDEX/events?event_name=UTXO_MOVE,CREDIT,DEBIT",
                "result": [
                    {
                        "event": "UTXO_MOVE",
                        "event_index": "$EVENT_INDEX_9",
                        "params": {
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$TX_HASH:0",
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXOASSET_UTXO_2_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$TX_HASH",
                            "tx_index": "$TX_INDEX",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_8",
                        "params": {
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$TX_HASH:0",
                            "utxo_address": "$ADDRESS_7",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_7",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": "$TX_INDEX",
                            "utxo": "$UTXOASSET_UTXO_2_TX_HASH:0",
                            "utxo_address": "$ADDRESS_8",
                        },
                        "tx_hash": "$TX_HASH",
                    },
                    {
                        "event": "UTXO_MOVE",
                        "event_index": "$EVENT_INDEX_6",
                        "params": {
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "destination": "$UTXOASSET_UTXO_2_TX_HASH:0",
                            "msg_index": 0,
                            "quantity": 1000000000,
                            "source": "$UTXOASSET_UTXO_1_TX_HASH:0",
                            "status": "valid",
                            "tx_hash": "$UTXOASSET_UTXO_2_TX_HASH",
                            "tx_index": 68,
                        },
                        "tx_hash": "$UTXOASSET_UTXO_2_TX_HASH",
                    },
                    {
                        "event": "CREDIT",
                        "event_index": "$EVENT_INDEX_5",
                        "params": {
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "calling_function": "utxo move",
                            "event": "$UTXOASSET_UTXO_2_TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": 68,
                            "utxo": "$UTXOASSET_UTXO_2_TX_HASH:0",
                            "utxo_address": "$ADDRESS_8",
                        },
                        "tx_hash": "$UTXOASSET_UTXO_2_TX_HASH",
                    },
                    {
                        "event": "DEBIT",
                        "event_index": "$EVENT_INDEX_4",
                        "params": {
                            "action": "utxo move",
                            "address": None,
                            "asset": "UTXOASSET",
                            "block_index": "$BLOCK_INDEX",
                            "event": "$UTXOASSET_UTXO_2_TX_HASH",
                            "quantity": 1000000000,
                            "tx_index": 68,
                            "utxo": "$UTXOASSET_UTXO_1_TX_HASH:0",
                            "utxo_address": "$ADDRESS_7",
                        },
                        "tx_hash": "$UTXOASSET_UTXO_2_TX_HASH",
                    },
                ],
            },
        ],
    },
]
