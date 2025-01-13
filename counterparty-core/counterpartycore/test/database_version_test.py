#! /usr/bin/python3
import tempfile

import pytest

from counterpartycore import server
from counterpartycore.lib import check, config, database

# this is require near the top to do setup of the test suite
from counterpartycore.test import (
    conftest,  # noqa: F401
    util_test,
)
from counterpartycore.test.util_test import CURR_DIR


def test_check_database_version():
    server.initialise(
        database_file=tempfile.gettempdir() + "/fixtures.unittest.db",
        testnet3=True,
        **util_test.COUNTERPARTYD_OPTIONS,
    )
    util_test.restore_database(
        config.DATABASE, CURR_DIR + "/fixtures/scenarios/unittest_fixture.sql"
    )
    db = database.get_connection(read_only=False)
    database.update_version(db)

    version_major, version_minor = database.version(db)
    assert config.VERSION_MAJOR == version_major
    assert config.VERSION_MINOR == version_minor

    check.database_version(db)

    config.VERSION_MAJOR += 1
    with pytest.raises(check.DatabaseVersionError) as exception:
        check.database_version(db)
    assert exception.value.from_block_index == config.BLOCK_FIRST
    assert exception.value.required_action == "rollback"
    config.VERSION_MAJOR -= 1
