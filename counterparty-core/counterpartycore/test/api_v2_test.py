import json
import tempfile

import pytest
import requests

from counterpartycore.lib import util
from counterpartycore.lib.api import routes

# this is require near the top to do setup of the test suite
from counterpartycore.test import (
    conftest,  # noqa: F401
)
from counterpartycore.test.fixtures.params import ADDR
from counterpartycore.test.util_test import CURR_DIR

FIXTURE_SQL_FILE = CURR_DIR + "/fixtures/scenarios/unittest_fixture.sql"
FIXTURE_DB = tempfile.gettempdir() + "/fixtures.unittest_fixture.db"
API_V2_FIXTURES = CURR_DIR + "/fixtures/api_v2_fixtures.json"
API_ROOT = "http://localhost:10009"


@pytest.mark.usefixtures("api_server_v2")
def test_api_v2(request):
    block_index = 310491
    address = "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc"
    asset = "NODIVISIBLE"
    asset1 = asset
    asset2 = "XCP"
    tx_hash = "c6d9a615dede9796a5337aff3681347e41d58c722c5ccbabefa0172e1024737c"
    order_hash = "e7038bdcd8fe79d282000f04123f98549c7abb40163fc9580b02486b4c1a55cf"
    bet_hash = "6f5fbb3c63ae13b50d48a10df5317a1615bd5d9bfd2d46d75950689099e461f5"
    dispenser_hash = "0d53631a5f5b18632791ee65aa9723b29b57eb5a6e12d034804b786d99102a03"
    block_hash = "ee0fe3cc9b3a48a2746b6090b63b442b97ea6055d48edcf4b2288396764c6943"
    dividend_hash = "42ae2fd7f3a18f84334bc37aa88283e79d6bff0b234dbf97e788695957d75518"
    issuance_hash = "41875b71d97cc901894b9e4b56de50c535fd9fd8c7619e6ceec4fd7c99288425"
    broadcast_hash = "c82ad252b11a832e8b63211de584c052639c979f56ca2e21e1dbb5d2c259cd97"
    minter_hash = "e0e851286ef46844503ca3177b910c0ccc582130d2c2f5eecc8bec4f79b6d98a"
    mint_hash = "f79c9bf13a2a7743139c3bfb712fbe650978963f7a392cc1b7ad98b74dcd3e7b"
    event = "CREDIT"
    event_index = 10
    tx_index = 2
    exclude_routes = [
        "compose",
        "unpack",
        "info",
        "mempool",
        "healthz",
        "bitcoin",
        "v1",
        "rpc",
        "api",
        "fairminters",  # TEMPORARY
    ]
    results = {}
    fixtures = {}
    with open(API_V2_FIXTURES, "r") as f:
        fixtures = json.load(f)

    for route in routes.ROUTES:
        # TODO: add dividends in fixtures
        if route == "/" or route == "/<path:subpath>" or "<dividend_hash>" in route:
            continue
        if any([exclude in route for exclude in exclude_routes]):
            continue

        url = f"{API_ROOT}{route}"
        url = url.replace("<int:block_index>", str(block_index))
        url = url.replace("<int:tx_index>", str(tx_index))
        if "/dispensers/" in route:
            url = url.replace("<asset>", "XCP")
            url = url.replace("<address>", "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b")
        else:
            url = (
                url.replace("<asset>", asset)
                .replace("<asset1>", asset1)
                .replace("<asset2>", asset2)
            )
            url = url.replace("<address>", address)
        url = url.replace("<event>", event)
        url = url.replace("<int:event_index>", str(event_index))
        url = url.replace("<order_hash>", order_hash)
        url = url.replace("<bet_hash>", bet_hash)
        url = url.replace("<dispenser_hash>", dispenser_hash)
        if "issuances" in url:
            url = url.replace("<tx_hash>", issuance_hash)
        if "broadcasts" in url:
            url = url.replace("<tx_hash>", broadcast_hash)
        if "fairminters" in url:
            url = url.replace("<tx_hash>", minter_hash)
        if "fairmints":
            url = url.replace("<tx_hash>", mint_hash)
        url = url.replace("<tx_hash>", tx_hash)
        url = url.replace("<block_hash>", block_hash)
        url = url.replace("<dividend_hash>", dividend_hash)
        if route.startswith("/v2/events"):
            url += "?limit=5&verbose=true"
        elif (
            route.startswith("/v2/addresses/balances")
            or route.startswith("/v2/addresses/transactions")
            or route.startswith("/v2/addresses/events")
            or route.startswith("/v2/addresses/mempool")
        ):
            url += "?verbose=true&limit=6&addresses=" + ADDR[0] + "," + ADDR[1]
        elif route.startswith("/v2/utxos/withbalances"):
            url += "?verbose=true&utxos=" + tx_hash + ":0," + order_hash + ":0"
        else:
            url += "?verbose=true"
        print(url)
        options_result = requests.options(url)  # noqa: S113
        assert options_result.status_code == 204
        print(options_result.headers)
        assert options_result.headers["Access-Control-Allow-Origin"] == "*"
        assert options_result.headers["Access-Control-Allow-Headers"] == "*"
        assert options_result.headers["Access-Control-Allow-Methods"] == "*"

        result = requests.get(url)  # noqa: S113
        print(result)
        results[url] = result.json()
        print(result.json())
        assert result.status_code == 200
        if not request.config.getoption("saveapifixtures"):
            assert results[url] == fixtures[url]

    if request.config.getoption("saveapifixtures"):
        with open(API_V2_FIXTURES, "w") as f:
            f.write(json.dumps(results, indent=4))


@pytest.mark.usefixtures("api_server_v2")
def test_api_v2_unpack(request, server_db):
    with open(CURR_DIR + "/fixtures/api_v2_unpack_fixtures.json", "r") as f:
        datas = json.load(f)
    url = f"{API_ROOT}/v2/transactions/unpack"

    for data in datas:
        result = requests.get(url, params={"datahex": data["datahex"]})  # noqa: S113
        assert result.status_code == 200
        assert result.json()["result"] == data["result"]


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_balances_by_address():
    alice = ADDR[0]
    url = f"{API_ROOT}/v2/addresses/{alice}/balances"
    result = requests.get(url)  # noqa: S113

    # import json
    print(json.dumps(result.json()["result"], indent=4))

    expected_result = [
        {
            "address": None,
            "asset": "DIVISIBLE",
            "asset_longname": None,
            "quantity": 1,
            "utxo": "7b4bb2e22f2a6d03933266f4ad34a4f7bf3ef7d2d4aeeea81edc5de59493eb7c:0",
            "utxo_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "DIVISIBLE",
            "asset_longname": None,
            "quantity": 98799999999,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 100,
            "utxo": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
            "utxo_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 91674999900,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "RAIDFAIRMIN",
            "asset_longname": None,
            "quantity": 20,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "FREEFAIRMIN",
            "asset_longname": None,
            "quantity": 10,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "A95428956661682277",
            "asset_longname": "PARENT.already.issued",
            "quantity": 100000000,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "PARENT",
            "asset_longname": None,
            "quantity": 100000000,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "MAXI",
            "asset_longname": None,
            "quantity": 9223372036854775807,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "NODIVISIBLE",
            "asset_longname": None,
            "quantity": 985,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "LOCKED",
            "asset_longname": None,
            "quantity": 1000,
            "utxo": None,
            "utxo_address": None,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "CALLABLE",
            "asset_longname": None,
            "quantity": 1000,
            "utxo": None,
            "utxo_address": None,
        },
    ]
    for balance in result.json()["result"]:
        assert balance in expected_result


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_balances_by_asset():
    asset = "XCP"
    url = f"{API_ROOT}/v2/assets/{asset}/balances"
    result = requests.get(url)  # noqa: S113
    import json

    print(json.dumps(result.json()["result"], indent=4))
    expected_result = [
        {
            "address": "1_mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc_mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns_2",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 300000000,
        },
        {
            "address": "mrPk7hTeZWjjSCrMTC2ET4SAUThQt7C4uK",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 14999857,
        },
        {
            "address": "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 46449548498,
        },
        {
            "address": "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 92949122099,
        },
        {
            "address": "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 92999030129,
        },
        {
            "address": "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 92945878046,
        },
        {
            "address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 99999990,
        },
        {
            "address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 91674999900,
        },
        {
            "address": None,
            "utxo": "1e9d0b5cc5b3f56cc59c0e8f3268d6ad10f79337aaf19081580c486caeb4cf53:0",
            "utxo_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 100,
        },
        {
            "address": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 92949130360,
        },
        {
            "address": "myAtcJEHAsDLbTkai6ipWDZeeL7VkxXsiM",
            "utxo": None,
            "utxo_address": None,
            "asset": "XCP",
            "asset_longname": None,
            "quantity": 92999138821,
        },
    ]
    for balance in result.json()["result"]:
        assert balance in expected_result


@pytest.mark.usefixtures("api_server")
@pytest.mark.usefixtures("api_server_v2")
def test_new_get_balances_vs_old():
    asset = "XCP"
    url = f"{API_ROOT}/v2/assets/{asset}/balances"
    new_balances = requests.get(url).json()["result"]  # noqa: S113
    old_balance = util.api(
        "get_balances",
        {
            "filters": [
                {"field": "asset", "op": "==", "value": asset},
                {"field": "quantity", "op": "!=", "value": 0},
            ],
        },
    )
    new_balances = sorted(
        new_balances, key=lambda x: (x["address"] or x["utxo"], x["asset"], x["quantity"])
    )
    old_balance = sorted(
        old_balance, key=lambda x: (x["address"] or x["utxo"], x["asset"], x["quantity"])
    )
    assert len(new_balances) == len(old_balance)
    for new_balance, old_balance in zip(new_balances, old_balance):  # noqa: B020
        assert new_balance["address"] == old_balance["address"]
        assert new_balance["utxo"] == old_balance["utxo"]
        assert new_balance["asset"] == old_balance["asset"]
        assert new_balance["quantity"] == old_balance["quantity"]


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_asset_info():
    asset = "NODIVISIBLE"
    url = f"{API_ROOT}/v2/assets/{asset}"
    result = requests.get(url)  # noqa: S113

    assert result.json()["result"] == {
        "asset": "NODIVISIBLE",
        "asset_longname": None,
        "description": "No divisible asset",
        "description_locked": False,
        "divisible": False,
        "issuer": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        "locked": False,
        "first_issuance_block_index": 310002,
        "last_issuance_block_index": 310002,
        "asset_id": "1911882621324134",
        "owner": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        "supply": 1000,
    }


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_asset_orders():
    asset = "XCP"
    url = f"{API_ROOT}/v2/assets/{asset}/orders"
    result = requests.get(url).json()["result"]  # noqa: S113
    assert len(result) == 6
    assert result[0] == {
        "tx_index": 493,
        "tx_hash": "05bcc7b25130206aca1f3b695e4d9ed392c9f16c0294ab292c0a029c1bb5e4ca",
        "block_index": 310513,
        "source": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
        "give_asset": "BTC",
        "give_quantity": 800000,
        "give_remaining": 800000,
        "get_asset": "XCP",
        "get_quantity": 100000000,
        "get_remaining": 100000000,
        "expiration": 2000,
        "expire_index": 312492,
        "fee_required": 0,
        "fee_required_remaining": 0,
        "fee_provided": 1000000,
        "fee_provided_remaining": 992800,
        "status": "open",
        "get_price": 0.008,
        "give_price": 125.0,
    }


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_order_info():
    tx_hash = "b6c0ce5991e1ab4b46cdd25f612cda202d123872c6250831bc0f510a90c1238e"
    url = f"{API_ROOT}/v2/orders/{tx_hash}"
    result = requests.get(url).json()["result"]  # noqa: S113
    assert result == {
        "tx_index": 11,
        "tx_hash": "b6c0ce5991e1ab4b46cdd25f612cda202d123872c6250831bc0f510a90c1238e",
        "block_index": 310010,
        "source": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        "give_asset": "XCP",
        "give_quantity": 100000000,
        "give_remaining": 100000000,
        "get_asset": "BTC",
        "get_quantity": 1000000,
        "get_remaining": 1000000,
        "expiration": 2000,
        "expire_index": 312010,
        "fee_required": 900000,
        "fee_required_remaining": 900000,
        "fee_provided": 1260,
        "fee_provided_remaining": 1260,
        "status": "open",
        "get_price": 100.0,
        "give_price": 0.01,
    }


@pytest.mark.usefixtures("api_server_v2")
def test_new_get_order_matches():
    tx_hash = "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5"
    url = f"{API_ROOT}/v2/orders/{tx_hash}/matches"
    result = requests.get(url).json()["result"]  # noqa: S113
    assert result[0] == {
        "id": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5_05bcc7b25130206aca1f3b695e4d9ed392c9f16c0294ab292c0a029c1bb5e4ca",
        "tx0_index": 492,
        "tx0_hash": "65e649d58b95602b04172375dbd86783b7379e455a2bc801338d9299d10425a5",
        "tx0_address": "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
        "tx1_index": 493,
        "tx1_hash": "05bcc7b25130206aca1f3b695e4d9ed392c9f16c0294ab292c0a029c1bb5e4ca",
        "tx1_address": "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
        "forward_asset": "XCP",
        "forward_price": 0.008,
        "forward_quantity": 100000000,
        "backward_asset": "BTC",
        "backward_price": 125.0,
        "backward_quantity": 800000,
        "tx0_block_index": 310491,
        "tx1_block_index": 310492,
        "block_index": 310513,
        "tx0_expiration": 2000,
        "tx1_expiration": 2000,
        "match_expire_index": 310512,
        "fee_paid": 7200,
        "status": "expired",
    }


@pytest.mark.usefixtures("api_server_v2")
def test_asset_dispensers():
    asset = "XCP"

    url = f"{API_ROOT}/v2/assets/{asset}/dispensers?status=1"
    result = requests.get(url)  # noqa: S113
    assert result.json()["result"] == []

    url = f"{API_ROOT}/v2/assets/{asset}/dispensers?status=0"
    result = requests.get(url)  # noqa: S113
    assert result.json()["result"] == [
        {
            "tx_index": 108,
            "tx_hash": "0d53631a5f5b18632791ee65aa9723b29b57eb5a6e12d034804b786d99102a03",
            "block_index": 310107,
            "source": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "asset": "XCP",
            "give_quantity": 100,
            "escrow_quantity": 100,
            "satoshirate": 100,
            "status": 0,
            "give_remaining": 100,
            "oracle_address": None,
            "last_status_tx_hash": None,
            "origin": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "price": 1.0,
            "dispense_count": 0,
            "last_status_tx_source": None,
            "close_block_index": None,
        }
    ]

    asset = "TESTDISP"

    url = f"{API_ROOT}/v2/assets/{asset}/dispensers?status=1"
    result = requests.get(url)  # noqa: S113
    assert result.json()["result"] == []

    url = f"{API_ROOT}/v2/assets/{asset}/dispensers?status=0"
    result = requests.get(url)  # noqa: S113
    assert result.json()["result"] == [
        {
            "tx_index": 511,
            "tx_hash": "df0adb4c53c60a08d614da9e33beb4c0b1fdbeb34ecdfc44cf04b00554d24bf2",
            "block_index": 310510,
            "source": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "asset": "TESTDISP",
            "give_quantity": 100,
            "escrow_quantity": 100,
            "satoshirate": 100,
            "status": 0,
            "give_remaining": 100,
            "oracle_address": None,
            "last_status_tx_hash": None,
            "origin": "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "price": 1.0,
            "dispense_count": 0,
            "last_status_tx_source": None,
            "close_block_index": None,
        }
    ]
