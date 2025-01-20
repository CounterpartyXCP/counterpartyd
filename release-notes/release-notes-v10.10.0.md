# Release Notes - Counterparty Core v10.10.0 (2025-01-??)

# Upgrading


# ChangeLog

## Protocol Changes

## Bugfixes

- Fix ignored deprecated parameters in Compose API
- Fix Get Mempool Events By Addresses endpoint for attach, detach and UTXO move
- Retry ten times on telemetry request error

## Codebase

- Remove counterparty-wallet
- Split vector file
- Move python tests from `counterparty-rs` to `counterparty-core`
- Reorganize files and functions, split too big files, delete all unused functions
- Remove globals in `lib/util.py` and `ledger.py`
- Use yoyo migrations to update database

## API

- Add no_dispense parameter to not automatically compose a dispense transaction even if the destination is a dispenser
- Add `event_name` parameter to Get Mempool Events By Addresses endpoint
- Check addresses and hashes format in parameters
- `sat_per_vbyte` parameter accepts float

## CLI


# Credits

- Ouziel Slama
- Warren Puffet
- Adam Krellenstein
