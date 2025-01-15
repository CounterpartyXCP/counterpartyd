import tempfile

import pytest

from counterpartycore.lib.api import composer
from counterpartycore.lib.messages import send

# this is require near the top to do setup of the test suite
from counterpartycore.test import (
    conftest,  # noqa: F401
)
from counterpartycore.test.fixtures.params import ADDR
from counterpartycore.test.util_test import CURR_DIR

FIXTURE_SQL_FILE = CURR_DIR + "/fixtures/scenarios/unittest_fixture.sql"
FIXTURE_DB = tempfile.gettempdir() + "/fixtures.unittest_fixture.db"


@pytest.mark.usefixtures("server_db")
def test_transaction_arc4(server_db):
    v = int(100 * 1e8)
    tx_info = send.compose(server_db, ADDR[0], ADDR[1], "XCP", v)
    send1hex = composer.construct(server_db, tx_info, {"regular_dust_size": 5430})

    assert (
        send1hex["rawtransaction"]
        == "0200000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae0000000000ffffffff0336150000000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000000000001e6a1c2a504df746f83442653dd7ada4dc727a030865749e9fba58ba71d71ac346ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
    )
