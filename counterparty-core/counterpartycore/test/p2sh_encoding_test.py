import binascii
import hashlib
import logging
import tempfile
import time

import bitcoin as bitcoinlib
import pytest

# this is require near the top to do setup of the test suite
from counterpartycore.test import (
    conftest,  # noqa: F401
    util_test,
)
from counterpartycore.test.fixtures.params import ADDR, DP, P2SH_ADDR
from counterpartycore.test.util_test import CURR_DIR

logger = logging.getLogger(__name__)

from counterpartycore.lib import (  # noqa: E402
    backend,
    config,
    deserialize,
    exceptions,
    gettxinfo,
    script,
    transaction,
    util,
)
from counterpartycore.lib.transaction_helper import p2sh_encoding  # noqa: E402

FIXTURE_SQL_FILE = CURR_DIR + "/fixtures/scenarios/unittest_fixture.sql"
FIXTURE_DB = tempfile.gettempdir() + "/fixtures.unittest_fixture.db"


def prefix_cntrprty(block_index):
    return b"CNTRPRTY"


@pytest.mark.usefixtures()
def test_p2sh_encoding_composed(server_db):
    source = ADDR[0]  # noqa: F841
    destination = ADDR[1]  # noqa: F841

    with util_test.ConfigContext(
        DISABLE_ARC4_MOCKING=True, OLD_STYLE_API=True
    ), util_test.MockProtocolChangesContext(enhanced_sends=True, p2sh_encoding=True):
        # BTC Mainnet tx d90dc8637fd2ab9ae39b7c2929c793c5d28d7dea672afb02fb4001637085e9a1
        datatxhex = "010000000102d2b137e49e930ef3e436b342713d8d07bd378e773c915a5938993d81dc7e6000000000fdab0147304402207848293e88563750f647e949cb594cdbec0beb4070faac73040d77d479420f8302201e0ac32788e98bd984279102b7382576d7ddb4b125d1d507725cbd12d97a2908014d60014d1401434e5452505254590300010042276049e5518791be2ffe2c301f5dfe9ef85dd0400001720034b0410000000000000001500000006a79811e000000000000000054000079cec1665f4800000000000000050000000ca91f2d660000000000000005402736c8de6e34d54000000000000001500c5e4c71e081ceb00000000000000054000000045dc03ec4000000000000000500004af1271cf5fc00000000000000054001e71f8464432780000000000000015000002e1e4191f0d0000000000000005400012bc4aaac2a54000000000000001500079c7e774e411c00000000000000054000000045dc0a6f00000000000000015000002e1e486f661000000000000000540001c807abe13908000000000000000475410426156245525daa71f2e84a40797bcf28099a2c508662a8a33324a703597b9aa2661a79a82ffb4caaa9b15f4094622fbfa85f8b9dc7381f991f5a265421391cc3ad0075740087ffffffff0100000000000000000e6a0c31d52bf3b404aefaf596cfd000000000"
        original_prefix = util.prefix
        util.prefix = prefix_cntrprty
        parsed_source, parsed_destination, parsed_btc_amount, parsed_fee, parsed_data, extra = (
            gettxinfo._get_tx_info(
                server_db,
                deserialize.deserialize_tx(datatxhex, use_txid=True),
                util.CURRENT_BLOCK_INDEX,
            )
        )
        util.prefix = original_prefix
        print("!!!!!!!!!!!!!!!!>1")
        print(parsed_source)
        print(parsed_destination)
        print(parsed_btc_amount)
        print(parsed_fee)
        print(parsed_data)
        print(extra)
        print("!!!!!!!!!!!!!!!!<1")


@pytest.mark.usefixtures("cp_server")
def test_p2sh_encoding(server_db):
    source = ADDR[0]
    destination = ADDR[1]

    with util_test.ConfigContext(
        DISABLE_ARC4_MOCKING=True, OLD_STYLE_API=True
    ), util_test.MockProtocolChangesContext(
        enhanced_sends=True, p2sh_encoding=True, short_tx_type_id=False
    ):
        utxos = dict(
            ((utxo["txid"], utxo["vout"]), utxo)
            for utxo in backend.addrindexrs.get_unspent_txouts(source)
        )

        transaction.initialise()
        fee = 20000
        fee_per_kb = 50000
        result = transaction.compose_transaction(
            server_db,
            "send",
            {"source": source, "destination": destination, "asset": "XCP", "quantity": 100},
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
            fee=fee,
        )
        assert not isinstance(result, list)
        pretxhex = result

        pretx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(pretxhex))

        sumvin = sum(
            [
                int(utxos[(bitcoinlib.core.b2lx(vin.prevout.hash), vin.prevout.n)]["amount"] * 1e8)
                for vin in pretx.vin
            ]
        )
        sumvout = sum([vout.nValue for vout in pretx.vout])

        assert len(pretx.vout) == 2
        assert len(pretxhex) / 2 == 142
        assert sumvin == 199909140
        assert sumvout < sumvin
        assert sumvout == (sumvin - fee)

        # data P2SH output
        expected_datatx_length = 435  # noqa: F841
        expected_datatx_fee = fee  # excat fee asked
        assert (
            repr(pretx.vout[0].scriptPubKey)
            == "CScript([OP_HASH160, x('8042727755cf6254a0b8f7f4c82de93c23b507d6'), OP_EQUAL])"
        )
        assert pretx.vout[0].nValue == expected_datatx_fee
        # change output
        assert pretx.vout[1].nValue == sumvin - expected_datatx_fee - fee

        assert (
            pretxhex
            == "0100000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788acffffffff02204e00000000000017a9148042727755cf6254a0b8f7f4c82de93c23b507d687d4c2e90b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
        )
        # 01000000                                                          | version
        # 01                                                                | inputs
        # c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae  | txout hash
        # 00000000                                                          | txout index
        # 19                                                                | script length
        # 76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac                | tx_script
        # ffffffff                                                          | Sequence
        # 02                                                                | number of outputs
        # f654000000000000                                                  | output 1 value (21750)
        # 17                                                                | output 1 length (23 bytes)
        # a9147698101f9b9e5cdf0a0e11c2972dbc4860f374bf87                    | output 1 script
        # febbe90b00000000                                                  | output 2 value (199867390)
        # 19                                                                | output 2 length (25 bytes)
        # 76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac                | output 2 script
        # 00000000                                                          | locktime

        # first transaction should be considered BTC only
        with pytest.raises(exceptions.BTCOnlyError):
            gettxinfo._get_tx_info(
                server_db,
                deserialize.deserialize_tx(pretxhex, True),
                util.CURRENT_BLOCK_INDEX,
            )

        # store transaction
        pretxid, _ = util_test.insert_raw_transaction(pretxhex, server_db)

        logger.debug(f"pretxid {pretxid}")

        # check that when we do another, unrelated, send that it won't use our UTXO
        result = transaction.compose_transaction(
            server_db,
            "send",
            {"source": source, "destination": destination, "asset": "XCP", "quantity": 100},
        )
        othertx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(result))
        othertxid = bitcoinlib.core.lx(
            bitcoinlib.core.b2x(othertx.vin[0].prevout.hash)
        )  # reverse hash
        assert not (
            binascii.hexlify(othertxid).decode("ascii") == pretxid and othertx.vin[0].prevout.n == 0
        )

        # now compose the data transaction
        result = transaction.compose_transaction(
            server_db,
            "send",
            {"source": source, "destination": destination, "asset": "XCP", "quantity": 100},
            p2sh_pretx_txid=pretxid,  # pass the pretxid
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
        )
        assert not isinstance(result, list)
        datatxhex = result

        datatx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(datatxhex))
        sumvin = sum([pretx.vout[n].nValue for n, vin in enumerate(datatx.vin)])
        sumvout = sum([vout.nValue for vout in datatx.vout])
        fee = 10000

        assert len(datatxhex) / 2 == 167
        assert sumvin == expected_datatx_fee
        assert sumvout < sumvin
        assert sumvout == sumvin - expected_datatx_fee
        assert len(datatx.vout) == 1
        # opreturn signalling P2SH
        assert (
            repr(datatx.vout[0].scriptPubKey)
            == "CScript([OP_RETURN, x('03214158f8e4c83c02386ffa')])"
        )  # arc4(PREFIX + 'P2SH')
        assert datatx.vout[0].nValue == 0

        assert (
            datatxhex
            == "010000000119d8ee8a286d755e51877e79a8972abd2914eccc560529effb389c0bcbdd0344000000005d4c5b31544553545858585800000002000000000000000100000000000000646f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec75210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad0075740087ffffffff0100000000000000000e6a0c03214158f8e4c83c02386ffa00000000"
        )
        # 01000000                                                                                    | version
        # 01                                                                                          | inputs
        # 0a0746fe9308ac6e753fb85780a8b788b40655148dcde1435f2048783b784f06                            | txout hash
        # 00000000                                                                                    | txout index (0)
        # 74                                                                                          | script length (116)
        # 31544553545858585800000002000000000000000100000000000000                                    | tx_script
        #         646f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec2975210282b886c087eb37dc8182f14ba6cc    |   ...
        #         3e9485ed618b95804d44aecc17c300b585b0ad007574008717a9147698101f9b9e5cdf0a0e11c297    |   ...
        #         2dbc4860f374bf87                                                                    |   ...
        # ffffffff                                                                                    | Sequence
        # 01                                                                                          | number of outputs
        # 0000000000000000                                                                            | output 1 value (0)
        # 0e                                                                                          | output 1 length (14 bytes)
        # 6a0c8a5dda15fb6f0562da344d2f                                                                | output 1 script
        # 00000000                                                                                    | locktime

        # verify parsed result
        parsed_source, parsed_destination, parsed_btc_amount, parsed_fee, parsed_data, extra = (
            gettxinfo._get_tx_info(
                server_db,
                deserialize.deserialize_tx(datatxhex, True),
                util.CURRENT_BLOCK_INDEX,
            )
        )
        # assert parsed_source == source # make_canonical cannot calculate this address
        assert (
            parsed_data
            == binascii.unhexlify(
                "00000002"
                "0000000000000001"
                "0000000000000064"
                "6f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec"
            )
        )  # ID=enhanced_send(0x02) ASSET=XCP(0x01) VALUE=100(0x64) destination_pubkey(0x6f8d...d6ec)
        assert parsed_btc_amount == 0
        assert parsed_fee == expected_datatx_fee

        # check signing pubkey
        tx_script_start = 8 + 2 + 64 + 8
        tx_script_length = int(datatxhex[tx_script_start : tx_script_start + 2], 16) * 2
        tx_script = datatxhex[tx_script_start + 2 : tx_script_start + 2 + tx_script_length]
        signing_pubkey_hash = tx_script[-44:-4]
        address = script.base58_check_encode(signing_pubkey_hash, config.ADDRESSVERSION)  # noqa: F841


@pytest.mark.usefixtures("cp_server")
def test_p2sh_encoding_long_data(server_db):
    source = ADDR[0]
    destination = ADDR[1]  # noqa: F841

    with util_test.ConfigContext(OLD_STYLE_API=True), util_test.MockProtocolChangesContext(
        enhanced_sends=True, p2sh_encoding=True, short_tx_type_id=False
    ):
        utxos = dict(
            ((utxo["txid"], utxo["vout"]), utxo)
            for utxo in backend.addrindexrs.get_unspent_txouts(source)
        )

        # pprint.pprint(utxos)

        fee_per_kb = 50000
        result = transaction.compose_transaction(
            server_db,
            "broadcast",
            {
                "source": source,
                "text": "The quick brown fox jumped over the lazy dog. " * 12,
                "fee_fraction": 0,
                "timestamp": 1512155862,
                "value": 0,
            },
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
        )
        assert not isinstance(result, list)
        pretxhex = result

        pretx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(pretxhex))
        actual_fee = int(len(pretxhex) / 2 * fee_per_kb / 1000)  # noqa: F841

        sumvin = sum(
            [
                int(utxos[(bitcoinlib.core.b2lx(vin.prevout.hash), vin.prevout.n)]["amount"] * 1e8)
                for vin in pretx.vin
            ]
        )
        sumvout = sum([vout.nValue for vout in pretx.vout])

        # pretx_fee = 12950

        assert len(pretx.vout) == 3
        assert len(pretxhex) / 2 == 174
        assert sumvin == 199909140
        assert sumvout < sumvin
        # assert sumvout == (sumvin - pretx_fee)

        pretx_fee = sumvin - sumvout

        # data P2SH output
        expected_datatx_fee_rounded = config.DEFAULT_REGULAR_DUST_SIZE * 2

        assert (
            repr(pretx.vout[0].scriptPubKey)
            == "CScript([OP_HASH160, x('600fad54f67716af692b33f72862b7c0d457ade6'), OP_EQUAL])"
        )
        assert pretx.vout[0].nValue == config.DEFAULT_REGULAR_DUST_SIZE
        assert pretx.vout[1].nValue == config.DEFAULT_REGULAR_DUST_SIZE
        # change output
        assert pretx.vout[2].nValue == sumvin - (2 * config.DEFAULT_REGULAR_DUST_SIZE) - pretx_fee

        assert (
            pretxhex
            == "0100000001c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788acffffffff03220200000000000017a914600fad54f67716af692b33f72862b7c0d457ade687220200000000000017a9142adb68fe57838e8dd49641e93f6fc70922ade549873a28ea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac00000000"
        )
        # 00000001                                                         | version
        # 01                                                               | inputs
        # c1d8c075936c3495f6d653c50f73d987f75448d97a750249b1eb83bee71b24ae | txout hash
        # 00000000                                                         | txout index
        # 19                                                               | script length
        # 76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac               | tx_script
        # ffffffff                                                         | Sequence
        # 03                                                               | number of outputs (3)
        # e470000000000000                                                 | output 1 value (28900)
        # 17                                                               | output 1 length (23 bytes)
        # a9147698101f9b9e5cdf0a0e11c2972dbc4860f374bf87                   | output 1 script
        # e470000000000000                                                 | output 2 value (28900)
        # 17                                                               | output 2 length (23 bytes)
        # a914676d587edf25cf01d3b153ff0b71f5e9b622386387                   | output 2 script
        # b64ae90b00000000                                                 | output 3 value (199838390)
        # 19                                                               | output 3 length (25 bytes)
        # 76a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac               | output 3 script
        # 00000000                                                         | locktime

        # store transaction
        pretxid, _ = util_test.insert_raw_transaction(pretxhex, server_db)
        logger.debug(f"pretxid {pretxid}")

        # now compose the data transaction
        result = transaction.compose_transaction(
            server_db,
            "broadcast",
            {
                "source": source,
                "text": "The quick brown fox jumped over the lazy dog. " * 12,
                "fee_fraction": 0,
                "timestamp": 1512155862,
                "value": 0,
            },
            p2sh_pretx_txid=pretxid,  # pass the pretxid
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
        )
        assert not isinstance(result, list)
        datatxhex = result

        datatx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(datatxhex))
        sumvin = sum([pretx.vout[n].nValue for n, vin in enumerate(datatx.vin)])
        sumvout = sum([vout.nValue for vout in datatx.vout])
        assert len(datatx.vin) == 2

        assert len(datatxhex) / 2 == 1594 / 2
        assert sumvin == 2 * config.DEFAULT_REGULAR_DUST_SIZE
        assert sumvout < sumvin
        assert sumvout == 0
        assert len(datatx.vout) == 1
        # opreturn signalling P2SH
        assert (
            repr(datatx.vout[0].scriptPubKey)
            == "CScript([OP_RETURN, x('8a5dda15fb6f0562da344d2f')])"
        )  # arc4(PREFIX + 'P2SH')
        assert datatx.vout[0].nValue == 0
        assert (
            datatxhex
            == "0100000002b7bd6fbf86ab2987a37ac78db80a84f2dde28bb65128fce0c2108c9c43538d5900000000fd0a024d07024ddb0154455354585858580000001e5a21aad600000000000000000000000054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f766572207475210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad0075740087ffffffffb7bd6fbf86ab2987a37ac78db80a84f2dde28bb65128fce0c2108c9c43538d59010000009e4c9c4c7154455354585858586865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2054686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e2075210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad5175740087ffffffff0100000000000000000e6a0c8a5dda15fb6f0562da344d2f00000000"
        )
        # 01000000                                                                                              | version
        # 02                                                                                                    | inputs
        # f33f677de4180f1b0c261a991974c57de97f082a7e62332b77ec5d193d13d1a3                                      | txout hash
        # 00000000                                                                                              | txout index (0)
        # fd                                                                                                    | script length (253)
        # 4d024d080254455354585858580000001e5a21aad6000000000000000000000000                                    | tx_script
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e20      |   ...
        #     54686520717569636b2062726f776e20666f78206a756d706564206f766572202975210282b886c087eb37dc8182      |   ...
        #     f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad007574008717a9147698101f9b9e5cdf0a0e11c2972dbc      |   ...
        #     4860f374bf87                                                                                      |   ...
        # ffffffff                                                                                              | Sequence
        # f33f677de4180f1b0c261a991974c57de97f082a7e62332b77ec5d193d13d1a3                                      | txout hash
        # 01000000                                                                                              | txout index (1)
        # 87                                                                                                    | script length (135)
        # 445445535458585858746865206c617a7920646f672e20                                                        | tx_script
        #     54686520717569636b2062726f776e20666f78206a756d706564206f76657220746865206c617a7920646f672e202975  |   ...
        #     210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad517574008717a914676d587edf  |   ...
        #     25cf01d3b153ff0b71f5e9b622386387                                                                  |   ...
        # ffffffff                                                                                              | Sequence
        # 01                                                                                                    | number of outputs
        # 0000000000000000                                                                                      | output 1 value (0)
        # 0e                                                                                                    | output 1 length (14 bytes)
        # 6a0c8a5dda15fb6f0562da344d2f                                                                          | output 1 script
        # 00000000                                                                                              | locktime

        # verify parsed result
        parsed_source, parsed_destination, parsed_btc_amount, parsed_fee, parsed_data, extra = (
            gettxinfo._get_tx_info(
                server_db,
                deserialize.deserialize_tx(datatxhex, True),
                util.CURRENT_BLOCK_INDEX,
            )
        )
        # assert parsed_source == source # make_canonical can't calculate this address

        assert (
            parsed_data
            == binascii.unhexlify("0000001e5a21aad6000000000000000000000000")
            + b"The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. "
        )  # ID=enhanced_send(0x1e) ASSET=XCP(0x01) VALUE=100(0x64) destination_pubkey(0x6f8d...d6ec)
        assert parsed_btc_amount == 0
        assert parsed_fee == expected_datatx_fee_rounded


""" Test that p2sh sources are not supported by the API at this time """


@pytest.mark.usefixtures("cp_server")
def test_p2sh_encoding_p2sh_source_not_supported(server_db):
    source = P2SH_ADDR[0]
    destination = ADDR[1]

    with util_test.ConfigContext(OLD_STYLE_API=True), util_test.MockProtocolChangesContext(
        enhanced_sends=True, p2sh_encoding=True, short_tx_type_id=False
    ):
        fee = 20000
        fee_per_kb = 50000

        with pytest.raises(exceptions.TransactionError):
            result = transaction.compose_transaction(  # noqa: F841
                server_db,
                "send",
                {"source": source, "destination": destination, "asset": "XCP", "quantity": 100},
                encoding="p2sh",
                fee_per_kb=fee_per_kb,
                fee=fee,
            )


""" Manually form a transaction from a p2sh source """


@pytest.mark.usefixtures("cp_server")
def test_p2sh_encoding_manual_multisig_transaction(server_db):
    source = P2SH_ADDR[0]
    destination = ADDR[1]

    with util_test.ConfigContext(OLD_STYLE_API=True), util_test.MockProtocolChangesContext(
        enhanced_sends=True, p2sh_encoding=True, short_tx_type_id=False
    ):
        p2sh_source_multisig_pubkeys_binary = [
            binascii.unhexlify(p)
            for p in [DP["pubkey"][ADDR[0]], DP["pubkey"][ADDR[1]], DP["pubkey"][ADDR[2]]]
        ]
        data_drop = b"deadbeef01"
        script_sig, redeem_script, output_script = p2sh_encoding.make_p2sh_encoding_redeemscript(
            data_drop,
            n=0,
            pub_key=None,
            multisig_pubkeys=p2sh_source_multisig_pubkeys_binary,
            multisig_pubkeys_required=2,
        )
        redeem_script = bitcoinlib.core.script.CScript(redeem_script)
        assert (
            repr(redeem_script)
            == f"CScript([x('{data_drop.hex()}'), OP_DROP, 2, x('{DP['pubkey'][ADDR[0]]}'), x('{DP['pubkey'][ADDR[1]]}'), x('{DP['pubkey'][ADDR[2]]}'), 3, OP_CHECKMULTISIGVERIFY, 0, OP_DROP, OP_DEPTH, 0, OP_EQUAL])"
        )

        # setup transaction
        fee = 20000
        fee_per_kb = 50000
        pretxhex = transaction.compose_transaction(
            server_db,
            "send",
            {
                "source": source,
                "destination": destination,
                "asset": "XCP",
                "quantity": 100,
            },
            p2sh_source_multisig_pubkeys=[
                DP["pubkey"][ADDR[0]],
                DP["pubkey"][ADDR[1]],
                DP["pubkey"][ADDR[2]],
            ],
            p2sh_source_multisig_pubkeys_required=2,
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
            fee=fee,
        )
        # debugTransaction = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(pretxhex))

        # store transaction
        pretxid, _ = util_test.insert_raw_transaction(pretxhex, server_db)
        logger.debug(f"pretxid {pretxid}")

        # now compose the data transaction
        result = transaction.compose_transaction(
            server_db,
            "send",
            {"source": source, "destination": destination, "asset": "XCP", "quantity": 100},
            p2sh_source_multisig_pubkeys=[
                DP["pubkey"][ADDR[0]],
                DP["pubkey"][ADDR[1]],
                DP["pubkey"][ADDR[2]],
            ],
            p2sh_source_multisig_pubkeys_required=2,
            p2sh_pretx_txid=pretxid,  # pass the pretxid
            encoding="p2sh",
            fee_per_kb=fee_per_kb,
        )
        assert not isinstance(result, list)
        datatxhex = result

        datatx = bitcoinlib.core.CTransaction.deserialize(binascii.unhexlify(datatxhex))  # noqa: F841

        # parse the transaction
        parsed_source, parsed_destination, parsed_btc_amount, parsed_fee, parsed_data, extra = (
            gettxinfo._get_tx_info(
                server_db,
                deserialize.deserialize_tx(datatxhex, True),
                util.CURRENT_BLOCK_INDEX,
            )
        )
        assert parsed_source == source
        assert (
            parsed_data
            == binascii.unhexlify(
                "00000002"
                "0000000000000001"
                "0000000000000064"
                "6f8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec"
            )
        )  # ID=enhanced_send(0x02) ASSET=XCP(0x01) VALUE=100(0x64) destination_pubkey(0x6f8d...d6ec)
        assert parsed_btc_amount == 0


@pytest.mark.usefixtures("cp_server")
def test_p2sh_script_decoding():
    script_hex = "1c8a5dda15fb6f05628a061e67576e926dc71a7fa2f0cceb97452b4d564101a914c088c83aeddd211096df9f5f0df1f3b885ac7fe70188210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ad0075740087"
    script_sig = bitcoinlib.core.script.CScript(binascii.unhexlify(script_hex))

    print("script_sig", repr(script_sig), list(script_sig), len(list(script_sig)))

    chunks = list(script_sig)
    if len(chunks) == 3:
        sig = chunks[0]
        datachunk = chunks[1]
        redeemScript = chunks[2]
    else:
        sig = None
        datachunk = chunks[0]
        redeemScript = chunks[1]

    print("sig", binascii.hexlify(sig) if sig else sig)
    print("datachunk", binascii.hexlify(datachunk) if datachunk else datachunk)
    print("redeemScript", binascii.hexlify(redeemScript) if redeemScript else redeemScript)

    if not redeemScript:
        redeemScript = datachunk
        datachunk = sig
        sig = None

    assert datachunk and redeemScript

    print("sig", binascii.hexlify(sig) if sig else sig)
    print("datachunk", binascii.hexlify(datachunk) if datachunk else datachunk)
    print("redeemScript", binascii.hexlify(redeemScript) if redeemScript else redeemScript)

    assert datachunk == binascii.unhexlify(
        "8a5dda15fb6f05628a061e67576e926dc71a7fa2f0cceb97452b4d56"
    )


@pytest.mark.usefixtures("cp_server")
def test_p2sh_signed_multisig_script_decoding():
    original_prefix = util.prefix
    util.prefix = prefix_cntrprty
    txHex = "0100000001bae95e59f83e55035f566dc0e3034f79f0d670dc6d6a0d207a11b4e49e9baecf00000000fd0301483045022100d2d38c2d98285e44a271e91894622fa85044469257dbfc15a49e1ba98cddaf8002202b06bf0ca9d65af9f9c96db13c7585b4cd66cabedba269f9b70659dd8e456c46014cb84c8d434e5452505254591e5a3ae08000000000000000000000000073434950203620737570706f727473207573696e672070327368206164647265737365732061732074686520736f7572636520616464726573732062757420726571756972657320616e206164646974696f6e616c20696e70757420696e207468652064617461207472616e73616374696f6e2e752102e53b79237cacdc221cff4c0fb320223cac3e0fe30a682a22f19a70a3975aa3f8ad0075740087ffffffff0100000000000000000e6a0c804e42751677319b884a2d1b00000000"

    ctx = deserialize.deserialize_tx(txHex, True)
    vin = ctx["vin"][0]
    asm = script.script_to_asm(vin["script_sig"])
    new_source, new_destination, new_data = p2sh_encoding.decode_p2sh_input(asm, 0)

    assert new_data == binascii.unhexlify(
        "1e5a3ae08000000000000000000000000073434950203620737570706f727473207573696e672070327368206164647265737365732061732074686520736f7572636520616464726573732062757420726571756972657320616e206164646974696f6e616c20696e70757420696e207468652064617461207472616e73616374696f6e2e"
    )
    util.prefix = original_prefix


def test_benchmark_outkey_vin():
    m = 100000

    t = time.time()
    for n in range(m):  # noqa: B007
        tx = bitcoinlib.core.CTransaction.deserialize(
            binascii.unhexlify(
                "0100000002eff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b000000006c493046022100ec6fa8316a4f5cfd69816e31011022acce0933bd3b01248caa8b49e60de1b98a022100987ba974b2a4f9976a8d61d94009cb7f7986a827dc5730e999de1fb748d2046c01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffffeff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b010000006a47304402201f8fb2d62df22592cb8d37c68ab26563dbb8e270f7f8409ac0f6d7b24ddb5c940220314e5c767fd12b20116528c028eab2bfbad30eb963bd849993410049cf14a83d01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffff02145fea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000346a32544553540000000a00000000000000010000000005f5e1000000000000000000000000000bebc2000032000000000000271000000000"
            )
        )

    tt = time.time()
    ttn1 = (tt - t) / m

    print(tt - t, f"{ttn1:f}")

    t = time.time()
    for n in range(m):  # noqa: B007
        tx = bitcoinlib.core.CTransaction.deserialize(
            binascii.unhexlify(
                "0100000002eff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b000000006c493046022100ec6fa8316a4f5cfd69816e31011022acce0933bd3b01248caa8b49e60de1b98a022100987ba974b2a4f9976a8d61d94009cb7f7986a827dc5730e999de1fb748d2046c01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffffeff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b010000006a47304402201f8fb2d62df22592cb8d37c68ab26563dbb8e270f7f8409ac0f6d7b24ddb5c940220314e5c767fd12b20116528c028eab2bfbad30eb963bd849993410049cf14a83d01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffff02145fea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000346a32544553540000000a00000000000000010000000005f5e1000000000000000000000000000bebc2000032000000000000271000000000"
            )
        )
        outkey = [(vin.prevout.hash, vin.prevout.n) for vin in tx.vin]

    tt = time.time()
    ttn2 = (tt - t) / m

    print(tt - t, f"{ttn2:f}")

    t = time.time()
    for n in range(m):  # noqa: B007
        tx = bitcoinlib.core.CTransaction.deserialize(
            binascii.unhexlify(
                "0100000002eff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b000000006c493046022100ec6fa8316a4f5cfd69816e31011022acce0933bd3b01248caa8b49e60de1b98a022100987ba974b2a4f9976a8d61d94009cb7f7986a827dc5730e999de1fb748d2046c01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffffeff195acdf2bbd215daa8aca24eb667b563a731d34a9ab75c8d8df5df08be29b010000006a47304402201f8fb2d62df22592cb8d37c68ab26563dbb8e270f7f8409ac0f6d7b24ddb5c940220314e5c767fd12b20116528c028eab2bfbad30eb963bd849993410049cf14a83d01210282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0ffffffff02145fea0b000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac0000000000000000346a32544553540000000a00000000000000010000000005f5e1000000000000000000000000000bebc2000032000000000000271000000000"
            )
        )
        outkey = [(vin.prevout.hash, vin.prevout.n) for vin in tx.vin]
        outkey = hashlib.sha256(str(outkey).encode("ascii")).digest()

    tt = time.time()
    ttn3 = (tt - t) / m

    print(tt - t, f"{ttn3:f}")

    # not sure what to do here since the speed depends on the machine ...
    assert ttn1 < 0.0001
    assert ttn2 < 0.0001
    assert ttn3 < 0.0001

    # maybe assert relative
    assert ttn3 < ttn1 * 2
