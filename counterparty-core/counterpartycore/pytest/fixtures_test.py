import apsw
import pytest

from .fixtures import unitestdb
from .mocks import bitcoind


@pytest.fixture(scope="function")
def bitcoind_mock(monkeypatch):
    monkeypatch.setattr("counterpartycore.lib.backend.bitcoind.list_unspent", bitcoind.list_unspent)
    monkeypatch.setattr(
        "counterpartycore.lib.backend.bitcoind.satoshis_per_vbyte", bitcoind.satoshis_per_vbyte
    )
    return bitcoind


@pytest.fixture(scope="function")
def ledger_db(bitcoind_mock):
    return unitestdb.buid_unitest_db(bitcoind_mock)


def test_temp(ledger_db):
    assert isinstance(ledger_db, apsw.Connection)
