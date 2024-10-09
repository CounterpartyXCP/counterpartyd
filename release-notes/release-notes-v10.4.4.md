# Release Notes - Counterparty Core v10.4.4 (2024-10-??)


# Upgrading


# ChangeLog

## Bugfixes

- Handle invalid scripts in outputs properly
- Fix `last_block` in `get_running_info` command (API v1)
- Fix blockchain reorganization support

## Codebase

- Add `regtest` support in RSFetcher

## API

- Add Gunicorn support

## CLI

- Add `wsgi-server` (`werkzeug` or `gunicorn`) and `gunicorn-workers` flags
- Enable Sentry Caches and Queries pages

# Credits

* Ouziel Slama
* Warren Puffett
* Adam Krellenstein