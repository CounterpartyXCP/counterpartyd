# Release Notes - Counterparty Core v10.7.4 (2024-12-??)


# Upgrading


# ChangeLog

## Protocol Changes

## Bugfixes

- Fix `block.close_block_index` field type
- Set `issuances.reset` and `issuances.locked` default value to False instead None 
- Save also `utxo_address` in `address_events` table
- Clean useless indexes
- Don't rollback or reparse to a block index higher than current block index
- Fix dividend distribution to UTXO order after a rollback
- Exclude zero balances when getting balances by address and asset
- Remove lock file from RSFetcher
- Handle correctly RSFetcher invalid version
- Close correctly Ledger DB on shutdown

## Codebase

- Replace `counterparty.api.db` with `state.db`
- Add `issuances.asset_events`, `dispenses.btc_amount` and `mempool.addresses` field in Ledger DB
- Remove duplicate table from `state.db`
- Add `api/dbbuilder.py` module and refactor migrations to build `state.db`
- Use migrations to rollback `state.db`
- Remove rollback event by event in `state.db`
- Add version checking for `state.db`: launch a rollback when a reparse or a rollback is necessary for the Ledger DB
- Use `event_hash` to detect Blockchain reorganization and launch a rollback of `state.db`
- Refactor functions to refresh `util.CURRENT_BLOCK_INDEX` in `wsgi.py`
- Remove `compose_utxo()` function and clean `compose_attach()` and `compose_detach`
- Add `transaction_type` field in `transactions` table

## API

- Add `description_locked` in asset info
- Tweak `compose_movetoutxo` documentation
- Add `transaction_type` parameter for Get Transactions endpoints
- Add `transaction_types_count` table in State DB
- Add the following routes:
    - `/v2/transactions/counts`
    - `/v2/blocks/<int:block_index>/transactions/counts`
    - `/v2/addresses/<address>/transactions/counts`

## CLI

- Add `build-state-db` command
- `rollback` and `reparse` commands trigger a re-build of the State DB

# Credits

* droplister 
* Ouziel Slama
* Adam Krellenstein