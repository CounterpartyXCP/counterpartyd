from counterpartycore.lib import (
    backend,
    ledger,
    transaction,
)
from counterpartycore.lib.api import util

# Define the API routes except root (`/`) defined in `api_server.py`
ROUTES = util.prepare_routes(
    {
        ### /blocks ###
        "/blocks": ledger.get_blocks,
        "/blocks/<int:block_index>": ledger.get_block,
        "/blocks/<int:block_index>/transactions": ledger.get_transactions_by_block,
        "/blocks/<int:block_index>/events": ledger.get_events_by_block,
        "/blocks/<int:block_index>/events/counts": ledger.get_events_counts_by_block,
        "/blocks/<int:block_index>/events/<event>": ledger.get_events_by_block_and_event,
        "/blocks/<int:block_index>/credits": ledger.get_credits_by_block,
        "/blocks/<int:block_index>/debits": ledger.get_debits_by_block,
        "/blocks/<int:block_index>/expirations": ledger.get_expirations,
        "/blocks/<int:block_index>/cancels": ledger.get_cancels,
        "/blocks/<int:block_index>/destructions": ledger.get_destructions,
        "/blocks/<int:block_index>/issuances": ledger.get_issuances_by_block,
        "/blocks/<int:block_index>/sends": ledger.get_sends_or_receives_by_block,
        "/blocks/<int:block_index>/dispenses": ledger.get_dispenses_by_block,
        "/blocks/<int:block_index>/sweeps": ledger.get_sweeps_by_block,
        ### /transactions ###
        "/transactions/info": transaction.info,
        "/transactions/unpack": transaction.unpack,
        "/transactions/<tx_hash>": ledger.get_transaction,
        ### /addresses ###
        "/addresses/<address>/balances": ledger.get_address_balances,
        "/addresses/<address>/balances/<asset>": ledger.get_balance_object,
        "/addresses/<address>/credits": ledger.get_credits_by_address,
        "/addresses/<address>/debits": ledger.get_debits_by_address,
        "/addresses/<address>/bets": ledger.get_bet_by_feed,
        "/addresses/<address>/broadcasts": ledger.get_broadcasts_by_source,
        "/addresses/<address>/burns": ledger.get_burns_by_address,
        "/addresses/<address>/sends": ledger.get_send_by_address,
        "/addresses/<address>/receives": ledger.get_receive_by_address,
        "/addresses/<address>/sends/<asset>": ledger.get_send_by_address_and_asset,
        "/addresses/<address>/receives/<asset>": ledger.get_receive_by_address_and_asset,
        "/addresses/<address>/dispensers": ledger.get_dispensers_by_address,
        "/addresses/<address>/dispensers/<asset>": ledger.get_dispensers_by_address_and_asset,
        "/addresses/<address>/sweeps": ledger.get_sweeps_by_address,
        ### /address/<address>/compose/ ###
        "/address/<address>/compose/bet": transaction.compose_bet,
        "/address/<address>/compose/broadcast": transaction.compose_broadcast,
        "/address/<address>/compose/btcpay": transaction.compose_btcpay,
        "/address/<address>/compose/burn": transaction.compose_burn,
        "/address/<address>/compose/cancel": transaction.compose_cancel,
        "/address/<address>/compose/destroy": transaction.compose_destroy,
        "/address/<address>/compose/dispenser": transaction.compose_dispenser,
        "/address/<address>/compose/dividend": transaction.compose_dividend,
        "/address/<address>/compose/issuance": transaction.compose_issuance,
        "/address/<address>/compose/mpma": transaction.compose_mpma,
        "/address/<address>/compose/order": transaction.compose_order,
        "/address/<address>/compose/send": transaction.compose_send,
        "/address/<address>/compose/sweep": transaction.compose_sweep,
        ### /assets ###
        "/assets": ledger.get_valid_assets,
        "/assets/<asset>": ledger.get_asset_info,
        "/assets/<asset>/balances": ledger.get_asset_balances,
        "/assets/<asset>/balances/<address>": ledger.get_balance_object,
        "/assets/<asset>/orders": ledger.get_orders_by_asset,
        "/assets/<asset>/credits": ledger.get_credits_by_asset,
        "/assets/<asset>/debits": ledger.get_debits_by_asset,
        "/assets/<asset>/dividends": ledger.get_dividends,
        "/assets/<asset>/issuances": ledger.get_issuances_by_asset,
        "/assets/<asset>/sends": ledger.get_sends_or_receives_by_asset,
        "/assets/<asset>/dispensers": ledger.get_dispensers_by_asset,
        "/assets/<asset>/dispensers/<address>": ledger.get_dispensers_by_address_and_asset,
        "/assets/<asset>/holders": ledger.get_asset_holders,
        ### /orders ###
        "/orders/<tx_hash>": ledger.get_order,
        "/orders/<tx_hash>/matches": ledger.get_order_matches_by_order,
        "/orders/<tx_hash>/btcpays": ledger.get_btcpays_by_order,
        ### /bets ###
        "/bets/<tx_hash>": ledger.get_bet,
        "/bets/<tx_hash>/matches": ledger.get_bet_matches_by_bet,
        "/bets/<tx_hash>/resolutions": ledger.get_resolutions_by_bet,
        ### /burns ###
        "/burns": ledger.get_all_burns,
        ### /dispensers ###
        "/dispensers/<tx_hash>": ledger.get_dispenser_info_by_tx_hash,
        "/dispensers/<tx_hash>/dispenses": ledger.get_dispenses_by_dispenser,
        ### /events ###
        "/events": ledger.get_all_events,
        "/events/<int:event_index>": ledger.get_event_by_index,
        "/events/counts": ledger.get_all_events_counts,
        "/events/<event>": ledger.get_events_by_event,
        ### /healthz ###
        "/healthz": util.handle_healthz_route,
        ### /backend ###
        "/backend/addresses/<address>/transactions": backend.search_raw_transactions,
        "/backend/addresses/<address>/transactions/oldest": backend.get_oldest_tx,
        "/backend/addresses/<address>/utxos": backend.get_unspent_txouts,
        "/backend/addresses/<address>/pubkey": util.pubkeyhash_to_pubkey,
        "/backend/transactions/<tx_hash>": util.get_raw_transaction,
        "/backend/estimatesmartfee": backend.fee_per_kb,
        ### /mempool ###
        "/mempool/events": ledger.get_all_mempool_events,
        "/mempool/events/<event>": ledger.get_mempool_events_by_event,
    }
)
