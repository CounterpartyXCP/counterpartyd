import binascii

from counterpartycore.lib import config, deserialize, exceptions
from counterpartycore.lib.gettxinfo import SighashFlagError

from ..params import DEFAULT_PARAMS as DP

config.NETWORK_NAME = "testnet3"
config.PREFIX = b"TESTXXXX"

GETTXINFO_VECTOR = {
    "gettxinfo": {
        "get_tx_info": [
            # data in OP_CHECKSIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0636150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac36150000000000001976a9147da51ea175f108a1c63588683dc4c43a7146c46788ac36150000000000001976a9147da51ea175f108a1c6358868173e34e8ca75a06788ac36150000000000001976a9147da51ea175f108a1c637729895c4c468ca75a06788ac36150000000000001976a9147fa51ea175f108a1c63588682ed4c468ca7fa06788ace24ff505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                    [
                        "",
                        "4f4a408d8bd90ca994e1f6b0969a8fe1a6bcf33211a4b5bad876d26b6f3a666b:0",
                        "6",
                        "",
                    ],
                ),
            },
            # data in OP_CHECKMULTISIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0336150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                    [
                        "",
                        "564501b070077eb6e978a547ae28a3e8ec4505da3de856f03a0d127750a44f11:0",
                        "3",
                        "",
                    ],
                ),
            },
            # data in OP_CHECKMULTISIG script, destination = p2sh
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff03361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                    [
                        "",
                        "1f9b910792994070699d898d59217df052bc3568d7b8e4e5d5bba485aa62c73a:0",
                        "3",
                        "",
                    ],
                ),
            },
            {
                # 2 sources is actually invalid, but pre-first_input_is_source this was the consensus!
                "mock_protocol_changes": {"first_input_is_source": False},
                "comment": "data in OP_CHECKMULTISIG script , without first_input_is_source, 2 sources",
                "in": (
                    deserialize.deserialize_tx(
                        "0100000002ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff5ef833190e74ad47d8ae693f841a8b1b500ded7e23ee66b29898b72ec4914fdc0100000000ffffffff03361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753aed2fe7c11000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns-mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
                    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                    [
                        "",
                        "3481e0520d4f928617e86c0695f3d49faabb10b5432d44eb02e01141a4e6fc4d:0",
                        "3",
                        "",
                    ],
                ),
            },
            {
                "comment": "data in OP_CHECKMULTISIG script, with first_input_is_source, 1 source",
                "in": (
                    deserialize.deserialize_tx(
                        "0100000002ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff5ef833190e74ad47d8ae693f841a8b1b500ded7e23ee66b29898b72ec4914fdc0100000000ffffffff03361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753aed2fe7c11000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                    [
                        "",
                        "3481e0520d4f928617e86c0695f3d49faabb10b5432d44eb02e01141a4e6fc4d:0",
                        "3",
                        "",
                    ],
                ),
            },
        ],
        "get_tx_info_legacy": [
            # data in OP_CHECKSIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0636150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac36150000000000001976a9147da51ea175f108a1c63588683dc4c43a7146c46788ac36150000000000001976a9147da51ea175f108a1c6358868173e34e8ca75a06788ac36150000000000001976a9147da51ea175f108a1c637729895c4c468ca75a06788ac36150000000000001976a9147fa51ea175f108a1c63588682ed4c468ca7fa06788ace24ff505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00TESTXXXX\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00TESTXXXX\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00TESTXXXX\x00\x00\x00;\x10\x00\x00\x00\n\x9b\xb3Q\x92(6\xc8\x86\x81i\x87\xe1\x0b\x03\xb8_8v\x8b",
                    [],
                ),
            },
            # # data in OP_CHECKMULTISIG script, unsupported by get_tx_info1
            # {
            #     'in': (b'0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0336150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000', DP['default_block_index']),
            #     'error': (exceptions.DecodeError, 'no prefix')
            # },
            # # data in OP_CHECKSIG script, destination = p2sh, unsupported by get_tx_info1
            # {
            #     'in': (b'0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff06361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e8736150000000000001976a9147da51ea175f108a1c63588683dc4c43a7146c46788ac36150000000000001976a9147da51ea175f108a1c6358868173e34e8ca75a06788ac36150000000000001976a9147da51ea175f108a1c637729895c4c468ca75a06788ac36150000000000001976a9147fa51ea175f108a1c63588682ed4c468ca7fa06788ace24ff505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000', DP['default_block_index']),
            #     'error': (exceptions.DecodeError, 'no prefix')
            # }
        ],
        "get_tx_info_new": [
            # data in OP_CHECKSIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0636150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac36150000000000001976a9147da51ea175f108a1c63588683dc4c43a7146c46788ac36150000000000001976a9147da51ea175f108a1c6358868173e34e8ca75a06788ac36150000000000001976a9147da51ea175f108a1c637729895c4c468ca75a06788ac36150000000000001976a9147fa51ea175f108a1c63588682ed4c468ca7fa06788ace24ff505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    False,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            # data in OP_CHECKMULTISIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0336150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    False,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            # data in OP_CHECKMULTISIG script, destination = p2sh, unsupported by get_tx_info2
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff03361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    False,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            #'get_tx_info3'
            # data in OP_CHECKSIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0636150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac36150000000000001976a9147da51ea175f108a1c63588683dc4c43a7146c46788ac36150000000000001976a9147da51ea175f108a1c6358868173e34e8ca75a06788ac36150000000000001976a9147da51ea175f108a1c637729895c4c468ca75a06788ac36150000000000001976a9147fa51ea175f108a1c63588682ed4c468ca7fa06788ace24ff505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    None,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            # data in OP_CHECKMULTISIG script
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff0336150000000000001976a9144838d8b3588c4c7ba7c1d06f866e9b3739c6303788ac781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    None,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            # data in OP_CHECKMULTISIG script, destination = p2sh, unsupported by get_tx_info2
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001ebe3111881a8733ace02271dcf606b7450c41a48c1cb21fd73f4ba787b353ce4000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88acffffffff03361500000000000017a9144264cfd7eb65f8cbbdba98bd9815d5461fad8d7e87781e000000000000695121035ca51ea175f108a1c63588683dc4c43a7146c46799f864a300263c0813f5fe352102309a14a1a30202f2e76f46acdb2917752371ca42b97460f7928ade8ecb02ea17210319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b97753ae4286f505000000001976a9148d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    None,
                    True,
                ),
                "out": (
                    "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
                    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",
                    5430,
                    10000,
                    b"\x00\x00\x00(\x00\x00R\xbb3d\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x02\xfa\xf0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;\x10\x00\x00\x00\n",
                    [],
                ),
            },
            {
                "in": (
                    deserialize.deserialize_tx(
                        "0100000001aee668de98ef5f37d4962b620b0ec3deed8bbd4c2fb8ddedaf36c2e8ca5e51a7060000001976a914f3a6b6e4a093e5a5b9da76977a5270fd4d62553e88acffffffff04781e000000000000695121027c6a5e4412be80b5ccd5aa0ea685a21e7a577a5e390d138288841d06514b47992103b00007171817fb044e8a5464e3e274210dd64cf68cca9ea9c3e06df384aae6b22103d928d7d5bbe6f435da935ed382a0061c4a22bdc9b60a2ce6deb7d0f134d22eef53ae781e000000000000695121037c6a5e4412be80b5cc13bde2d9b04fd2cd1fc7ff664c0d3b6d8133163857b08f2103bb6fba40bee91bb02b54835b32f14b9e04016bfa34411ec64f09e3a9586efd5d2103d928d7d5bbe6f435da935ed382a0061c4a22bdc9b60a2ce6deb7d0f134d22eef53ae781e00000000000069512102696a5e4412be80b5ccd6aa0ac9a95e43ca49a21d40f762fadc1aab1c25909fb02102176c68252c6b855d7967aee372f14b772c963b2aa0411ec64f09e3a951eefd3e2103d928d7d5bbe6f435da935ed382a0061c4a22bdc9b60a2ce6deb7d0f134d22eef53aea8d37700000000001976a914f3a6b6e4a093e5a5b9da76977a5270fd4d62553e88ac00000000",
                        parse_vouts=True,
                        block_index=DP["default_block_index"],
                    ),
                    DP["default_block_index"],
                    None,
                    True,
                ),
                "error": (exceptions.BTCOnlyError, "no data and not unspendable"),
                #'out': (0,)
            },
        ],
        "select_utxo_destination": [
            {
                # invalid script
                "in": (
                    [
                        {
                            "script_pub_key": b"j] \x02\x03\x04\xfb\x8b\xdd\xe7\xe4\x9d\x9d\xaf\xcc\x8a\x93\xcd\xe0\xa2\x01\x05A\x06\x80\xc2\xd7/\n\xe8\x07\x08\x88\xa4\x01\x16\x01"
                        }
                    ],
                ),
                "out": 0,
            },
            {
                "in": (
                    [
                        # op_return
                        {
                            "script_pub_key": b"j)\x83\xe4b\x1dIm\xbe\x96\x0c\x00\xd1\xe1m\xd7\xed;\xaf\n\xca\x8ah\xaa\x88\xc1\xb49\xbd\x91\xc6\xac\xde/\x1b\xf9\x8dn\xa3\xec\xd5\xc9\xd5"
                        },
                        # invalid script
                        {
                            "script_pub_key": b"j] \x02\x03\x04\xfb\x8b\xdd\xe7\xe4\x9d\x9d\xaf\xcc\x8a\x93\xcd\xe0\xa2\x01\x05A\x06\x80\xc2\xd7/\n\xe8\x07\x08\x88\xa4\x01\x16\x01"
                        },
                    ],
                ),
                "out": 1,
            },
            {
                "in": (
                    [
                        # op_return
                        {
                            "script_pub_key": b"j)\x83\xe4b\x1dIm\xbe\x96\x0c\x00\xd1\xe1m\xd7\xed;\xaf\n\xca\x8ah\xaa\x88\xc1\xb49\xbd\x91\xc6\xac\xde/\x1b\xf9\x8dn\xa3\xec\xd5\xc9\xd5"
                        },
                        # valid script
                        {
                            "script_pub_key": b"\x00\x14\xc1\xbe\xe0\x1c\xc5L\xeeK\xa0\x8e\xfc\xe5\xd8\xd3\xfe\x14\xd7C\xaf\x8d"
                        },
                        # invalid script
                        {
                            "script_pub_key": b"j] \x02\x03\x04\xfb\x8b\xdd\xe7\xe4\x9d\x9d\xaf\xcc\x8a\x93\xcd\xe0\xa2\x01\x05A\x06\x80\xc2\xd7/\n\xe8\x07\x08\x88\xa4\x01\x16\x01"
                        },
                    ],
                ),
                "out": 1,
            },
            {
                "in": (
                    [
                        # invalid script
                        {
                            "script_pub_key": b"j] \x02\x03\x04\xfb\x8b\xdd\xe7\xe4\x9d\x9d\xaf\xcc\x8a\x93\xcd\xe0\xa2\x01\x05A\x06\x80\xc2\xd7/\n\xe8\x07\x08\x88\xa4\x01\x16\x01"
                        },
                        # op_return
                        {
                            "script_pub_key": b"j)\x83\xe4b\x1dIm\xbe\x96\x0c\x00\xd1\xe1m\xd7\xed;\xaf\n\xca\x8ah\xaa\x88\xc1\xb49\xbd\x91\xc6\xac\xde/\x1b\xf9\x8dn\xa3\xec\xd5\xc9\xd5"
                        },
                        # valid script
                        {
                            "script_pub_key": b"\x00\x14\xc1\xbe\xe0\x1c\xc5L\xeeK\xa0\x8e\xfc\xe5\xd8\xd3\xfe\x14\xd7C\xaf\x8d"
                        },
                    ],
                ),
                "out": 0,
            },
        ],
        "get_der_signature_sighash_flag": [
            {
                "comment": "68 length",
                "in": (
                    binascii.unhexlify(
                        "3041021d067f716293ffdaa144d5281185f5f9ca35f09e24f10af0ba7aa8e9ae8f0220555f644564e472d835d707200e03ae7c3728d5e2fee00eb7c351d025d8c6e16701"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "comment": "69 length",
                "in": (
                    binascii.unhexlify(
                        "3042021e78565f3de8b3b526ee9c3a07b396f4e18e082f77175f4aa444b63f66c9ad02205813ea177ac1d9b2dbb43f63cd3a00d47a3a525f3030c5233b8240239f9c15e401"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "comment": "71 length",
                "in": (
                    binascii.unhexlify(
                        "3044022063c96d6644f7d325bc7fed3362fd6cc81d81bf4a4af8df8d5f13147d6c74267a02201340b3b01b1f29d2d0e180abf5e3d14cc832b412cb27a5a68135f98493bb006e01"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "comment": "72 length",
                "in": (
                    binascii.unhexlify(
                        "3045022100c219a522e65ca8500ebe05a70d5a49d840ccc15f2afa4ee9df783f06b2a322310220489a46c37feb33f52c586da25c70113b8eea41216440eb84771cb67a67fdb68c01"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "comment": "73 length",
                "in": (
                    binascii.unhexlify(
                        "3046022100d8697a511eea7c0949f4295dc185d3e19cbd80aed547a2c0d29dd635b04430ef022100b334f949949ad19a3e78c9c3eb82320d877a5acc094e7ed3b15987a45ffca89101"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "comment": "invalid length",
                "in": (
                    binascii.unhexlify(
                        "304600022100c219a522e65ca8500ebe05a70d5840ccc15f2afa4ee9df783f06b2a322310220489a46c37feb33f52c586da25c70113b8eea41216440eb84771cb67a67fdb68c01"
                    ),
                ),
                "out": None,
            },
        ],
        "get_schnorr_signature_sighash_flag": [
            {
                "in": (
                    binascii.unhexlify(
                        "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "in": (
                    binascii.unhexlify(
                        "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae01"
                    ),
                ),
                "out": b"\x01",
            },
            {
                "in": (
                    binascii.unhexlify(
                        "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae83"
                    ),
                ),
                "out": b"\x83",
            },
        ],
        "collect_sighash_flags": [
            {
                "comment": "P2PK",
                "in": (
                    binascii.unhexlify(
                        "483045022100c219a522e65ca8500ebe05a70d5a49d840ccc15f2afa4ee9df783f06b2a322310220489a46c37feb33f52c586da25c70113b8eea41216440eb84771cb67a67fdb68c01"
                    ),
                    [],
                ),
                "out": [b"\x01"],
            },
            {
                "comment": "P2PKH",
                "in": (
                    binascii.unhexlify(
                        "483045022100c233c3a8a510e03ad18b0a24694ef00c78101bfd5ac075b8c1037952ce26e91e02205aa5f8f88f29bb4ad5808ebc12abfd26bd791256f367b04c6d955f01f28a7724012103f0609c81a45f8cab67fc2d050c21b1acd3d37c7acfd54041be6601ab4cef4f31"
                    ),
                    [],
                ),
                "out": [b"\x01"],
            },
            {
                "comment": "P2MS",
                "in": (
                    binascii.unhexlify(
                        "00483045022100af204ef91b8dba5884df50f87219ccef22014c21dd05aa44470d4ed800b7f6e40220428fe058684db1bb2bfb6061bff67048592c574effc217f0d150daedcf36787601483045022100e8547aa2c2a2761a5a28806d3ae0d1bbf0aeff782f9081dfea67b86cacb321340220771a166929469c34959daf726a2ac0c253f9aff391e58a3c7cb46d8b7e0fdc4801"
                    ),
                    [],
                ),
                "out": [b"\x01", b"\x01"],
            },
            {
                "comment": "P2WPKH",
                "in": (
                    b"",
                    [
                        "3045022100c7fb3bd38bdceb315a28a0793d85f31e4e1d9983122b4a5de741d6ddca5caf8202207b2821abd7a1a2157a9d5e69d2fdba3502b0a96be809c34981f8445555bdafdb01",
                        "03f465315805ed271eb972e43d84d2a9e19494d10151d9f6adb32b8534bfd764ab",
                    ],
                ),
                "out": [b"\x01"],
            },
            {
                "comment": "P2TR key path spend",
                "in": (
                    b"",
                    [
                        "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae01"
                    ],
                ),
                "out": [b"\x01"],
            },
            {
                "comment": "P2TR script path spend",
                "in": (
                    b"",
                    [
                        "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae",
                        "5387",
                        "c1a2fc329a085d8cfc4fa28795993d7b666cee024e94c40115141b8e9be4a29fa41324300a84045033ec539f60c70d582c48b9acf04150da091694d83171b44ec9bf2c4bf1ca72f7b8538e9df9bdfd3ba4c305ad11587f12bbfafa00d58ad6051d54962df196af2827a86f4bde3cf7d7c1a9dcb6e17f660badefbc892309bb145f",
                    ],
                ),
                "out": [b"\x01"],
            },
        ],
        "check_signatures_sighash_flag": [
            {
                "in": (
                    {"tx_id": "c8091f1ef768a2f00d48e6d0f7a2c2d272a5d5c8063db78bf39977adcb12e103"},
                ),
                "out": None,
            },
            {
                "comment": "P2PK",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "483045022100c219a522e65ca8500ebe05a70d5a49d840ccc15f2afa4ee9df783f06b2a322310220489a46c37feb33f52c586da25c70113b8eea41216440eb84771cb67a67fdb68c01"
                                ),
                            }
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2PK",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "483045022100c219a522e65ca8500ebe05a70d5a49d840ccc15f2afa4ee9df783f06b2a322310220489a46c37feb33f52c586da25c70113b8eea41216440eb84771cb67a67fdb68c83"
                                ),
                            }
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2PKH",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "483045022100c233c3a8a510e03ad18b0a24694ef00c78101bfd5ac075b8c1037952ce26e91e02205aa5f8f88f29bb4ad5808ebc12abfd26bd791256f367b04c6d955f01f28a7724012103f0609c81a45f8cab67fc2d050c21b1acd3d37c7acfd54041be6601ab4cef4f31"
                                ),
                            }
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2PKH",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "483045022100c233c3a8a510e03ad18b0a24694ef00c78101bfd5ac075b8c1037952ce26e91e02205aa5f8f88f29bb4ad5808ebc12abfd26bd791256f367b04c6d955f01f28a7724832103f0609c81a45f8cab67fc2d050c21b1acd3d37c7acfd54041be6601ab4cef4f31"
                                ),
                            }
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2MS",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "00483045022100af204ef91b8dba5884df50f87219ccef22014c21dd05aa44470d4ed800b7f6e40220428fe058684db1bb2bfb6061bff67048592c574effc217f0d150daedcf36787601483045022100e8547aa2c2a2761a5a28806d3ae0d1bbf0aeff782f9081dfea67b86cacb321340220771a166929469c34959daf726a2ac0c253f9aff391e58a3c7cb46d8b7e0fdc4801"
                                ),
                            }
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2MS",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": False,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "00483045022100af204ef91b8dba5884df50f87219ccef22014c21dd05aa44470d4ed800b7f6e40220428fe058684db1bb2bfb6061bff67048592c574effc217f0d150daedcf36787601483045022100e8547aa2c2a2761a5a28806d3ae0d1bbf0aeff782f9081dfea67b86cacb321340220771a166929469c34959daf726a2ac0c253f9aff391e58a3c7cb46d8b7e0fdc4883"
                                ),
                            }
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2WPKH",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            }
                        ],
                        "vtxinwit": [
                            [
                                "3045022100c7fb3bd38bdceb315a28a0793d85f31e4e1d9983122b4a5de741d6ddca5caf8202207b2821abd7a1a2157a9d5e69d2fdba3502b0a96be809c34981f8445555bdafdb01",
                                "03f465315805ed271eb972e43d84d2a9e19494d10151d9f6adb32b8534bfd764ab",
                            ]
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2WPKH",
                "in": (
                    {
                        "tx_id": "tx_id",  # c8091f1ef768a2f00d48e6d0f7a2c2d272a5d5c8063db78bf39977adcb12e103
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            },
                            {
                                "script_sig": b"",
                            },
                        ],
                        "vtxinwit": [
                            [
                                "304502210095dfc652a9c03911b7c4a0bc7de574ee4764cd1de78ab6599c196c69c741efbe022078ba83e9756e7d0751cb97402f031886bb34e00c70758710b4507db17649795983",
                                "03fef14a1660447a52f507af16a81b6e05ca8e579e0b74b11b44c6d9db6109a415",
                            ],
                            [
                                "3044022031150e6703f6fb7e924446b021211a1d216724693d78634c5a47a43c4edf8e1102203652e2879e9bd62dc1e5994045d81fdb4adacaec4b6c366cb18be74fc020d99601",
                                "031e9c58fa7828643a91fa06cc0146d97fe75b982218bf38745d6579309cfba5fe",
                            ],
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2TR key path spend",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            }
                        ],
                        "vtxinwit": [
                            [
                                "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae01"
                            ]
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2TR key path spend",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            }
                        ],
                        "vtxinwit": [
                            [
                                "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae83"
                            ]
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2TR script path spend",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            }
                        ],
                        "vtxinwit": [
                            [
                                "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae",
                                "5387",
                                "c1a2fc329a085d8cfc4fa28795993d7b666cee024e94c40115141b8e9be4a29fa41324300a84045033ec539f60c70d582c48b9acf04150da091694d83171b44ec9bf2c4bf1ca72f7b8538e9df9bdfd3ba4c305ad11587f12bbfafa00d58ad6051d54962df196af2827a86f4bde3cf7d7c1a9dcb6e17f660badefbc892309bb145f",
                            ]
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2TR script path spend",
                "in": (
                    {
                        "tx_id": "tx_id",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": b"",
                            }
                        ],
                        "vtxinwit": [
                            [
                                "b693a0797b24bae12ed0516a2f5ba765618dca89b75e498ba5b745b71644362298a45ca39230d10a02ee6290a91cebf9839600f7e35158a447ea182ea0e022ae83",
                                "5387",
                                "c1a2fc329a085d8cfc4fa28795993d7b666cee024e94c40115141b8e9be4a29fa41324300a84045033ec539f60c70d582c48b9acf04150da091694d83171b44ec9bf2c4bf1ca72f7b8538e9df9bdfd3ba4c305ad11587f12bbfafa00d58ad6051d54962df196af2827a86f4bde3cf7d7c1a9dcb6e17f660badefbc892309bb145f",
                            ]
                        ],
                    },
                ),
                "error": (SighashFlagError, "invalid SIGHASH flag for transaction tx_id"),
            },
            {
                "comment": "P2SH segwit",
                "in": (
                    {
                        "tx_id": "fa7e8c4a582b4284bd4726de620cd87dfef6b634ee3ebb043ed0dc08901eee83",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "16001415a13032cb59a7b51dd761223e189a48a7f67338"
                                ),
                            }
                        ],
                        "vtxinwit": [
                            [
                                "3045022100ceeccea697ed5fc7583387ba298ba1a84b6cdc24eeb97cf4021e967d795b27ca022070b398697abb41eb402994984c122fc6b4edccaeed819188be5c5ef40b8c685a01",
                                "039db968bfd35439d215dd26196266e8859a1fae89c462b587416779f0b8854e48",
                            ]
                        ],
                    },
                ),
                "out": None,
            },
            {
                "comment": "P2SH segwit",
                "in": (
                    {
                        "tx_id": "fa7e8c4a582b4284bd4726de620cd87dfef6b634ee3ebb043ed0dc08901eee83",
                        "segwit": True,
                        "vin": [
                            {
                                "script_sig": binascii.unhexlify(
                                    "16001415a13032cb59a7b51dd761223e189a48a7f67338"
                                ),
                            }
                        ],
                        "vtxinwit": [
                            [
                                "3045022100ceeccea697ed5fc7583387ba298ba1a84b6cdc24eeb97cf4021e967d795b27ca022070b398697abb41eb402994984c122fc6b4edccaeed819188be5c5ef40b8c685a83",
                                "039db968bfd35439d215dd26196266e8859a1fae89c462b587416779f0b8854e48",
                            ]
                        ],
                    },
                ),
                "error": (
                    SighashFlagError,
                    "invalid SIGHASH flag for transaction fa7e8c4a582b4284bd4726de620cd87dfef6b634ee3ebb043ed0dc08901eee83",
                ),
            },
        ],
    },
}
