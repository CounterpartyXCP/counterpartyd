"""
This is a collection of default transaction data used to test various components.
"""

UNIT = 100000000

"""This structure is used throughout the test suite to populate transactions with standardized and tested data."""
DEFAULT_PARAMS = {
    "addresses": [
        [
            "mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc",
            "4838d8b3588c4c7ba7c1d06f866e9b3739c63037",
            "cPdUqd5EbBWsjcG9xiL1hz8bEyGFiz4SW99maU9JgpL9TEcxUf3j",
            "0282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0",
        ],
        [
            "mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns",
            "8d6ae8a3b381663118b4e1eff4cfc7d0954dd6ec",
            "cQ897jnCVRrawNbw8hgmjMiRNHejwzg4KbzdMCzc91iaTif8ReqX",
            "0319f6e07b0b8d756156394b9dcf3b011fe9ac19f2700bd6b69a6a1783dbb8b977",
        ],
        [
            "mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH",
            "4e5638a01efbb2f292481797ae1dcfcdaeb98d00",
            "cRNnyC1h5qjv3tHkkt74Y5wowknM1BBDK5Ft2hj5SzfV3mgwPvC3",
            "0378ee11c3fb97054877a809ce083db292b16d971bcdc6aa4c8f92087133729d8b",
        ],
        [
            "mqPCfvqTfYctXMUfmniXeG2nyaN8w6tPmj",
            "6c39ee7c8f3a5ffa6121b0304a7a0de9d3d9a152",
            "cNNz8RhmTQufdmCKsCYjxPy43J6AxrH1wnAjutrxbeQs7Cy4C9q1",
            "037af2e06061b54cdfe3657bbc8496d69000b822e2db0c86ccbe376346a700b833",
        ],
        [
            "myAtcJEHAsDLbTkai6ipWDZeeL7VkxXsiM",
            "c1a6de504b9bc0d0d6987312b2e37564079791b7",
            "cPEo2oY8z3Fe9dDcFmzA7Wr1LjFh7iVQkCgBoXZEvQ8X6T2kfAHk",
            "02610f28a56e187f5cd133d7bfe107b159fa3b5129ba35e91fb915fe9a8efa43b4",
        ],
        [
            "munimLLHjPhGeSU5rYB2HN79LJa8bRZr5b",
            "9c8d1f5405451de6070bf1db86ab6accb495b625",
            "cNGEvSnRJ4wqdKWrni3fcX9wKTHXJt1gmoBUTrfqNrtKVZCnTUR2",
            "025bc8fb22d87eb72fb5e297803ab9aa3ace5bf38df4e23918b876fd3ea0cdd7b8",
        ],
        [
            "mwtPsLQxW9xpm7gdLmwWvJK5ABdPUVJm42",
            "b390187ef2854422ac5e4a2eb6ffe92496bef523",
            "cQiFxpxU2twNfViTqv3Tp3nY6H6Wd2YnypKjJFCkuim8YY3iQo2B",
            "03c403a9364dcb223cc32df5a4afab6089e941590cecfd5ac823c4fcff46e8f6c5",
        ],
        ["mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB", "", "", ""],  # Empty address for testing purposes
        [
            "mrPk7hTeZWjjSCrMTC2ET4SAUThQt7C4uK",
            "",
            "cSrcqM6oaUxhYo48ejQJbtRYLeyAMe6p44Fdoc91KtpYHiBG9hWd",
            "033ae8ae93bca8a08043768879a623b05f352a64cd64e1b8de4291c4cc52778936",
        ],
    ],
    "quantity": UNIT,
    "small": round(UNIT / 2),
    "expiration": 10,
    "fee_required": 900000,
    "fee_provided": 1000000,
    "fee_multiplier": 0.05,
    "unspendable": "mvCounterpartyXXXXXXXXXXXXXXW24Hef",
    "burn_start": 310000,
    "burn_end": 4017708,
    "burn_quantity": int(0.62 * UNIT),
    "burn_verysmall_quantity": int(0.0001 * UNIT),
    "default_block_index": 310000 + 704,
    "default_tx_index": 705,
    "default_block_hash": "2d62095b10a709084b1854b262de77cb9f4f7cd76ba569657df8803990ffbfc6c12bca3c18a44edae9498e1f0f054072e16eef32dfa5e3dd4be149009115b4b8",
    "regular_dust_size": 5430,  # This was the default value used in a lot of tests historically
}
DEFAULT_PARAMS["privkey"] = {
    addr: priv for (addr, pubkeyhash, priv, pub) in DEFAULT_PARAMS["addresses"]
}
DEFAULT_PARAMS["pubkey"] = {
    addr: pub for (addr, pubkeyhash, priv, pub) in DEFAULT_PARAMS["addresses"]
}
ADDR = [a[0] for a in DEFAULT_PARAMS["addresses"]]
SHORT_ADDR_BYTES = ["6f" + a[1] for a in DEFAULT_PARAMS["addresses"]]
DP = DEFAULT_PARAMS
MULTISIGADDR = [
    f"1_{ADDR[0]}_{ADDR[1]}_2",
    f"1_{ADDR[2]}_{ADDR[1]}_2",
    f"1_{ADDR[0]}_{ADDR[2]}_2",
    f"2_{ADDR[0]}_{ADDR[1]}_2",
    f"2_{ADDR[2]}_{ADDR[1]}_2",
    f"1_{ADDR[0]}_{ADDR[2]}_{ADDR[1]}_3",
    f"1_{ADDR[0]}_{ADDR[2]}_{ADDR[3]}_3",
    f"2_{ADDR[0]}_{ADDR[2]}_{ADDR[1]}_3",
    f"2_{ADDR[0]}_{ADDR[2]}_{ADDR[3]}_3",
    f"3_{ADDR[0]}_{ADDR[2]}_{ADDR[1]}_3",
    f"3_{ADDR[0]}_{ADDR[2]}_{ADDR[3]}_3",
]

P2SH_ADDR = [
    "2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy",  # 2of2 mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns
    "2N6P6d3iypnnud4YJDfHZ6kc513N8ezWmPx",  # 2of3 mn6q3dS2EnDUx3bmyWc6D4szJNVGtaR7zc mtQheFaSfWELRB2MyMBaiWjdDm6ux9Ezns mnfAHmddVibnZNSkh8DvKaQoiEfNsxjXzH
]

DEFAULT_PARAMS["pubkey"]["2MyJHMUenMWonC35Yi6PHC7i2tkS7PuomCy"] = (
    "0282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0"
)
DEFAULT_PARAMS["pubkey"]["2N6P6d3iypnnud4YJDfHZ6kc513N8ezWmPx"] = (
    "0282b886c087eb37dc8182f14ba6cc3e9485ed618b95804d44aecc17c300b585b0"
)

P2WPKH_ADDR = ["tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"]
