import json
import logging
import sys
import warnings

import requests

from counterpartycore.lib import config, database, ledger, util  # noqa: F401

logger = logging.getLogger(config.LOGGER_NAME)

CONSENSUS_HASH_SEED = (
    "We can only see a short distance ahead, but we can see plenty there that needs to be done."
)

CONSENSUS_HASH_VERSION_MAINNET = 2
CHECKPOINTS_MAINNET = {
    config.BLOCK_FIRST_MAINNET: {
        "ledger_hash": "766ff0a9039521e3628a79fa669477ade241fc4c0ae541c3eae97f34b547b0b7",
        "txlist_hash": "766ff0a9039521e3628a79fa669477ade241fc4c0ae541c3eae97f34b547b0b7",
    },
    280000: {
        "ledger_hash": "265719e2770d5a6994f6fe49839069183cd842ee14f56c2b870e56641e8a8725",
        "txlist_hash": "a59b33b4633649db4f14586af47e258ed9b8884dbb7aa308fb1f49a653ee60f4",
    },
    290000: {
        "ledger_hash": "4612ed7034474b4ff1727eb0e216d533ebe7ac755fb015e0f9a170c063f3e84c",
        "txlist_hash": "c15423c849fd360d38cbd6c6c3ea37a07fece723da92353f3056facc2676d9e7",
    },
    300000: {
        "ledger_hash": "9a3dd4949780404d61e5ca1929f94a43f08eb0fa19ccb4b5d6a61cafd7943199",
        "txlist_hash": "efa02dbdcc4158a598e3b476ece5ba9cc8d26f3abc8ac3777ac6dde0f0afc7e6",
    },
    310000: {
        "ledger_hash": "45e43d5cc77ea01129df01d7f55b0c89b2d4e18cd3d626fd92f30bfb37a85f4d",
        "txlist_hash": "83cdcf75833d828ded09979b601fde87e2fdb0f5eb1cc6ab5d2042b7ec85f90e",
    },
    320000: {
        "ledger_hash": "91c1d33626669e8098bc762b1a9e3f616884e4d1cadda4881062c92b0d3d3e98",
        "txlist_hash": "761793042d8e7c80e14a16c15bb9d40e237c468a87c207a59730b616bdfde7d4",
    },
    330000: {
        "ledger_hash": "dd56aa97e5ca15841407f383ce1d7814536a594d7cfffcb4cf60bee8b362065a",
        "txlist_hash": "3c45b4377a99e020550a198daa45c378c488a72ba199b53deb90b320d55a897b",
    },
    334000: {
        "ledger_hash": "24c4fa4097106031267439eb9fbe8ce2a18560169c67726652b608908c1ca9bb",
        "txlist_hash": "764ca9e8d3b9546d1c4ff441a39594548989f60daefc6f28e046996e76a273bf",
    },
    335000: {
        "ledger_hash": "e57c9d606a615e7e09bf99148596dd28e64b25cd8b081e226d535a64c1ed08d1",
        "txlist_hash": "437d9507185b5e193627edf4998aad2264755af8d13dd3948ce119b32dd50ce2",
    },
    336000: {
        "ledger_hash": "1329ff5b80d034b64f6ea3481b7c7176437a8837b2a7cb7b8a265fdd1397572d",
        "txlist_hash": "33eb8cacd4c750f8132d81e8e43ca13bd565f1734d7d182346364847414da52f",
    },
    337000: {
        "ledger_hash": "607e6a93e8d97cefea9bd55384898ee90c8477ded8a46017f2294feedbc83409",
        "txlist_hash": "20b535a55abcc902ca70c19dd648cbe5149af8b4a4157b94f41b71fc422d428e",
    },
    338000: {
        "ledger_hash": "f043914c71e4b711abb1c1002767b9a4e7d605e249facaaf7a2046b0e9741204",
        "txlist_hash": "fa2c3f7f76345278271ed5ec391d582858e10b1f154d9b44e5a1f4896400ee46",
    },
    339000: {
        "ledger_hash": "49f7240bc90ebc2f242dd599c7d2c427b9d2ac844992131e6e862b638ae4393a",
        "txlist_hash": "c1e3b497c054dcf67ddd0dc223e8b8a6e09a1a05bacb9fef5c03e48bd01e64e7",
    },
    340000: {
        "ledger_hash": "255760e2abfb79fdd76b65759f1590f582c1747f3eeccc4b2ae37d23e30e0729",
        "txlist_hash": "8502004bb63e699b243ac8af072d704c69b817905e74787c2031af971e8cd87c",
    },
    341000: {
        "ledger_hash": "1369cba3909e564d2e725879a8b2cd987df075db121d1d421c8ce16b65f4bf04",
        "txlist_hash": "d217d0bed190cb27f58fcb96b255f8006bc4b9ed739e1bb08507201c49c426c8",
    },
    342000: {
        "ledger_hash": "9e7e9b8620717189ccea697ff2f84fe71bc4ae8d991481ff235164d72a9e6e4f",
        "txlist_hash": "adf75d023760101b2b337f6359dd811b12521c83837eb3f7db3bbfd0b095aa54",
    },
    343000: {
        "ledger_hash": "aa47312ebe94b35504bec6c74713e404e5f36854e0836839344d13debe50558c",
        "txlist_hash": "6bdbbc96364b3c92cea132fe66a0925f9445a249f7062326bdcc4ad4711f0c01",
    },
    344000: {
        "ledger_hash": "40187263aa96d1362bf7b19c8ba0fff7f0c0f3eb132a40fc90601b5926c7e6e3",
        "txlist_hash": "98da8efe705c4b54275bfd25f816a7e7a4ff1f67647e17d7a0aaa2a3fef8bda0",
    },
    345000: {
        "ledger_hash": "e4a1e1be4beea63d9740ca166b75bb4e3ffa2af33e1fe282e5b09c4952a7448c",
        "txlist_hash": "777f163eaa5ad79dcb738871d4318a0699defec469d8afe91ab6277ff8d3e8b8",
    },
    350000: {
        "ledger_hash": "6a67e9f2e9d07e7bb3277cf9c24f84c857ed1b8fff4a37e589cd56ade276dd95",
        "txlist_hash": "96bcbdbce74b782a845d4fda699846d2d3744044c2870a413c018642b8c7c3bf",
    },
    355000: {
        "ledger_hash": "a84b17992217c7845e133a8597dac84eba1ee8c48bcc7f74bcf512837120f463",
        "txlist_hash": "210d96b42644432b9e1a3433a29af9acb3bad212b67a7ae1dbc011a11b04bc24",
    },
    360000: {
        "ledger_hash": "ddca07ea43b336b703fb8ebab6c0dc30582eb360d6f0eb0446e1fe58b53dee0a",
        "txlist_hash": "31d0ff3e3782cf9464081829c5595b3de5ac477290dc069d98672f3f552767f8",
    },
    365000: {
        "ledger_hash": "2d55b126cca3eca15c07b5da683988f9e01d7346d2ca430e940fd7c07ce84fd7",
        "txlist_hash": "7988a823cc1e3234953cc87d261d3c1fede8493d0a31b103357eb23cc7dc2eda",
    },
    366000: {
        "ledger_hash": "64ce274df2784f9ca88a8d7071613ec6527e506ec31cd434eca64c6a3345a6b7",
        "txlist_hash": "0d4374da6100e279b24f4ba4a2d6afbfc4fb0fc2d312330a515806e8c5f49404",
    },
    370000: {
        "ledger_hash": "fabb2a2e91fad3fe7734169d554cca396c1030243044cef42fcf65717cf0fa61",
        "txlist_hash": "41d1732868c9ac25951ace5ca9f311a15d5eca9bf8d548e0d988c050bd2aff87",
    },
    375000: {
        "ledger_hash": "a7ac4e2948cea0c426c8fc201cf57d9c313027ea7bff2b32a25ed28d3dbaa581",
        "txlist_hash": "96118a7aa2ca753488755b7419a0f44a7fbc371bc58dcc7ab083c70fc14ef8b3",
    },
    380000: {
        "ledger_hash": "70453ba04c1c0198c4771e7964cffa25f9456c2f71456a8b05dfe935d5fcdc88",
        "txlist_hash": "8bf2070103cca6f0bde507b7d20b0ba0630da6349beb560fa64c926d08dbcaef",
    },
    385000: {
        "ledger_hash": "93eb0a6e820bee197e7591edbc5ead7bfa38f32c88aabf4785f080fd6ae96c4c",
        "txlist_hash": "1f8f17fd5766382a8c10a2a0e995a7d5a5d1bcd5fc0220d1e2691b2a94dcc78f",
    },
    390000: {
        "ledger_hash": "7d42b98eecbc910a67a5f4ac8dc7d6d9b6995ebc5bdf53663b414965fe7d2c5e",
        "txlist_hash": "b50efc4a4241bf3ec33a38c3b5f34756a9f305fe5fa9a80f7f9b70d5d7b2a780",
    },
    395000: {
        "ledger_hash": "89f9ac390b35e69dd75d6c34854ba501dce2f662fc707aee63cad5822c7660f2",
        "txlist_hash": "2151dd2f0aa14685f3d041727a689d5d242578072a049123b317724fc4f1100c",
    },
    400000: {
        "ledger_hash": "eb681a305125e04b6f044b36045e23ee248ce4eb68433cea2b36d15e7e74d5f1",
        "txlist_hash": "b48e9501e8d6f1f1b4127d868860885d3db76698c2c31a567777257df101cf61",
    },
    405000: {
        "ledger_hash": "3725055b37a8958ade6ca1c277cf50fee6036b4a92befb8da2f7c32f0b210881",
        "txlist_hash": "871b2adfd246e3fe69f0fe9098e3251045ed6e9712c4cf90ea8dfdd1eb330ed6",
    },
    410000: {
        "ledger_hash": "1fa9a34f233695ebd7ebb08703bf8d99812fa099f297efc5d307d1ebef902ffd",
        "txlist_hash": "ee3bd84c728a37e2bbe061c1539c9ee6d71db18733b1ed53ee8d320481f55030",
    },
    415000: {
        "ledger_hash": "6772a8a1c784db14c0bf111e415919c9da4e5ca142be0b9e323c82c1b13c74e0",
        "txlist_hash": "cfb81785cd48e9ba0e54fee4d62f49b347489da82139fd5e1555ae0bc11a33d5",
    },
    420000: {
        "ledger_hash": "42167117e16943f44bb8117aa0a39bed2d863a454cd694d0bc5006a7aab23b06",
        "txlist_hash": "a1139870bef8eb9bbe60856029a4f01fce5432eb7aeacd088ba2e033757b86e3",
    },
    500000: {
        "ledger_hash": "8f41812d620181c2d566f7c932e5686d645335e8d6df5c7fbb9dd5b5bba414f4",
        "txlist_hash": "ecd99b7d0fdfd7233a975c3c28127ce341cb24bec44d21f9a79c3db4aef5a771",
    },
    600000: {
        "ledger_hash": "ab9f9c1aafdfc816a19aa403775c56b0b63e4c977685427f8fcee85db449cb15",
        "txlist_hash": "c8c7b8c0a86d601274e047d7038d47cd20f7147d9245f0d22449102b4b0c6fbf",
    },
    650000: {
        "ledger_hash": "7e4d5af885d20a68eb78d939f3b56f10c3e4defbb797297754579122e9611679",
        "txlist_hash": "14405c618a97fb2fc8b5640f84ad8a4aece924474a5b4ffc4e67c46914676ba6",
    },
    700000: {
        "ledger_hash": "4e84538d7bde57bbea518563f2a50f4245597bf5e5619fc4cbe9d981ab9d0adc",
        "txlist_hash": "abb48c10d692c159180a376b4a9002abcf582fab1b5652ba3ccdc73f4b5e0d8a",
    },
    725000: {
        "ledger_hash": "b4b44f2c87bc7fa59b442a0b81de23ad8bcf9b38c15f943934219c224e1ff51e",
        "txlist_hash": "3c9a87bd4150368ed3af587764d67e0fa9c4cdd89aeb364ac60a57c122610464",
    },
    750000: {
        "ledger_hash": "a944441af4a3b4b40dd892f225d8d44236979f7f837fdb2bf10fb4097712f9a1",
        "txlist_hash": "2466a57ab625ffc9a57bce0230f530bc9176406b62d30a43e761b2b92f175044",
    },
    775000: {
        "ledger_hash": "e8973858cf2aabf01264c5cde87676e657944fcdba7d6cd19fd9e2112f52b590",
        "txlist_hash": "81970d14f86e76577dfd819bb5291f8caf71a3a44fb18e9c119cfd73169be053",
    },
    775500: {
        "ledger_hash": "162bfd5c036fe2c6bb38f261578ce2df0b6d82e23d02f43375f92acd5f30c461",
        "txlist_hash": "6d323ec8af4f5b1b0ba65028ce574b50d410f279234fe7d7de3d18621d97331a",
    },
    776000: {
        "ledger_hash": "03c9d43c4e099a8dc6a77f86f34a62d76133af18c7f5c255f47fcfc87427bfff",
        "txlist_hash": "59968551a22d2241dbf04bb8dca12ac34120313e32fe3ab2f5436853b499ec3e",
    },
    776500: {
        "ledger_hash": "2e95c34487e252e3098b07e1d8d413c562a0995f6d58a46a0684598f7334882b",
        "txlist_hash": "5344d9d86af82bcb5ec139d214dc97e012aba300f6f150f8c8b2a13f6c854923",
    },
    777000: {
        "ledger_hash": "3c12194549f2a7ca0de57a211522c2c02d03c792982d887017881e0b50da1c01",
        "txlist_hash": "3c52bc42e685ce050418fdb1c4c907161f7ecc6669b1b7585cb74e2cfed3ea17",
    },
    777500: {
        "ledger_hash": "0ee8b7cd915b632891e380c23e278cb231be0eb2e8ee265a636f0cf16c15d5dc",
        "txlist_hash": "61073b558c84d51cbf45d0c9983486c030f5aae3fd27a77eae436e52f9479c0b",
    },
    778000: {
        "ledger_hash": "4a82415ba2d4d1c882fe1e7779773434926b277d6526030f3f5a4099f3c8d33e",
        "txlist_hash": "31c4f80ff660b2e5c14a8e6aef89412da2d9ce4a0406601bb07efdd2aa05a0d4",
    },
    778500: {
        "ledger_hash": "63410eefef4a136f57da84c391b052c46ccad7df1dbc3af853a24f0a8fbab60f",
        "txlist_hash": "64bf65bc4ace9046556ada65c84e10e66d05d88bdfbc35327a49f221f18ba55a",
    },
    779000: {
        "ledger_hash": "0bcf893450abe3e8ecd068c3881b27dd978db7dee89744644dfb179fc0e45a90",
        "txlist_hash": "1b698bb19eade25020713a72e803833b231a5b335d0589c98b595980255d338b",
    },
    779500: {
        "ledger_hash": "6b9b7c228ab69c67b0955d622365ec5680f8627d32b2a3b4a150e195d8d6cac2",
        "txlist_hash": "47f8a9010b1761619e3c845bb81d53f04855c6e96c87fe75d8028669f837bc7c",
    },
    780000: {
        "ledger_hash": "c2b27ddb9a060f7f85ef9d6bc17ef4b093e6366b0c83254995279b5929157fb0",
        "txlist_hash": "c1d5c1860270b9ec0f8e8e801c252ac58b9251206773258e2abe207deeb1ddbf",
    },
    780500: {
        "ledger_hash": "727d97d434036f5b7ab8f4d20271b73a7ffb1da00fa82e72dc8046936dffd2fa",
        "txlist_hash": "79969f1bdd63c1f3ee7479ea6daa853212940f65775e5c23d143a7dea5b4673a",
    },
    781000: {
        "ledger_hash": "1b94efb58db7d006bb8683262ab3b3f56a4f45b6c14fb1faf3f5d4b6a27031b0",
        "txlist_hash": "c9b74bbbb6218dda42f38dcedf845b35e15b7ab6ac929258d1bf5754c371a81b",
    },
    781500: {
        "ledger_hash": "eb0f62f5e603b71d74dc29c80cf65e60acc4b33f649131431bd6a94e13a6cac8",
        "txlist_hash": "6315ffcc0e5d739f946f9d14e7d5847f4fed1a4de5c9240329db161613adaee4",
    },
    782000: {
        "ledger_hash": "84bbe627a8b35bc8b4085745fa82f4064c3ded80243029f592f6be5c7762f03c",
        "txlist_hash": "f44bb1f2b5fd28deddeee59b7dfae8e9c252b87705dd11b1b2d6619498cd38e5",
    },
    782500: {
        "ledger_hash": "0ae2344029eb70eb3caec435faaeb4c03926cc0c454d68e099b6e05f97e22021",
        "txlist_hash": "9cca1b2034e84b8652a46c1fd2ac52e7ad32f8f5bd1dd9edde43411d6fb73373",
    },
    783000: {
        "ledger_hash": "459543e0ecebd9ec37bb44e52a698fe3059be590f7f7de56ab0fa4c463a112fe",
        "txlist_hash": "d41dd8eb0f9143de848c8c52018df5362b842a506cbbdfb2b989333069ae59f2",
    },
    783500: {
        "ledger_hash": "40b338562c78d186c6e028e557aed04e7cbcf90a50fde35004319767ad315c21",
        "txlist_hash": "6769b94212aa3fba96a413d3aceb97ca6e254516ce9e60c75cc6b779fce29005",
    },
    784000: {
        "ledger_hash": "7d073aa4e0cc5d348bb9fae60b333eb23c530c670b0aa3e58263eb255cd4cb8a",
        "txlist_hash": "a1bc1dc2bc502d7df6e33b08f420a6e92d4385eb5f1d085c521fe0b89128ad3f",
    },
    784500: {
        "ledger_hash": "70ed9a534d1fc0277be1b17c90625faba6b4f26e02121cbd29bb4a7a9f58c127",
        "txlist_hash": "ba1711aae5e68b643f7721fe659e740d96c6af53b0847ea9126195a602472d18",
    },
    785000: {
        "ledger_hash": "2e4488cf8afb3ec6100fc4b5aec68bbaf0358b93ae78871e626fee5fc6b78480",
        "txlist_hash": "29f401d28aa5eec5d12a80c40e333c170aef3f8d21f1863dd98d566aba2bd78a",
    },
    785500: {
        "ledger_hash": "3b2e715da336ba0d9c73896015287cdf8e595e8ad10044662b0d0a0f0cdc6c19",
        "txlist_hash": "4baf4a10d0c932e663b24a6a100b11784eb5644602d00dbbe6b1f1c5dd71e10f",
    },
    786000: {
        "ledger_hash": "0c0148fb6690794f0f9bbe5b189d7c828ee96482d94c270be6e9837192f9aeb2",
        "txlist_hash": "92dceab6e95997867bd82149ef77ca93667df4400cdb487b201e579f8ad4e84e",
    },
    786500: {
        "ledger_hash": "6145c920231e3fe2e5e72a9af8fe9ff0c6fd0a08deff55b2848815c7f1963814",
        "txlist_hash": "7d50d881a87bf88803b8be2272c4cedc97bcca457e06e7c55dbc93522ebe2e06",
    },
    787000: {
        "ledger_hash": "0964d4be96ab36f07973d994c76dda15ccf0bcdc20fcb95bd7f0c01b936e17ac",
        "txlist_hash": "70c0139e3bcb9ae243d8c051ebfa7fbc56e84fb19f70b8246e6d7c451f3161de",
    },
    787500: {
        "ledger_hash": "b2eb368797c3118b73713a190e94e1a693e6022088b06e53dbb136f06b36eda1",
        "txlist_hash": "ade0c47cf7d75eef1dfeb7c3783fe0ffe187dcb2d31a56c16ff73cdc1f38efaf",
    },
    788000: {
        "ledger_hash": "3ffd9a9e9613a5e8b57157bb02662f35126cf4eba6514ba51ef5b9bbc66e6601",
        "txlist_hash": "1c84819804bf28a3d86ad01998123e05b1491277cbc3f6d660599ec217480f52",
    },
    788500: {
        "ledger_hash": "b4d47766c95e4af3e7a6c4771278f68c8e6a3d27097d80b3f6ce7f367bfe016a",
        "txlist_hash": "2a46945783308df4521d1b46451942f5ac3c76ad3a10b4ba4cd72276c3719474",
    },
    789000: {
        "ledger_hash": "e68af5d0e4d8c41424f38306ab70177a42a8f877886df8bad5b9ef1d1c455e1d",
        "txlist_hash": "7b2834a2d791530eb75d6f7323265bb6c55bb90b61aae2e44e1517019633652d",
    },
    789500: {
        "ledger_hash": "44a6c0d9459ee441282f7bfd1b92f36a100a1126817bb2868d6337015bbbbc99",
        "txlist_hash": "9edf514d577f89e2cc6eccfa272b903689b7c36b7ac4819f32c20dd86a62c557",
    },
    790000: {
        "ledger_hash": "f71ebb93ae284a09701fc3d5eec9d6b1815adab198881746467ddee23f0aeb98",
        "txlist_hash": "0b50b95f056126fe0bbd57698a3a248e04071cb8f25dacfa8b29ca9fdef9e7ce",
    },
    790500: {
        "ledger_hash": "262494d50ba0771dbd4238e20ef5c6fdc9c685134864f52c80ddda5dccc499d7",
        "txlist_hash": "a69bf7808cb6ee6061de42d7c7695f080716aabf233032790ba6d126b3ec694e",
    },
    791000: {
        "ledger_hash": "1c642f7d07fa9dc017a2c5aec7abe906b10fd6a5306820323fab2f3b04f815a0",
        "txlist_hash": "9c88afe6c076aad24a75cc1e18fc6bc1aff1701fb6aa667f17d3b3855e16788e",
    },
    791500: {
        "ledger_hash": "753f85888a2d7fa4f4b48ea3a2c96b12fa6f5975092da27775b069f2b29fbabb",
        "txlist_hash": "c8afafbf958e64c745d3f6d9926b66a8d8ade167f6002b50793bdaa315c34986",
    },
    792000: {
        "ledger_hash": "c430e13020d7d0dd35cb3df9c42dd72ef0809bc9eab0f7a6b71385e4dc76e9da",
        "txlist_hash": "a41c578fdfb8bfc5175154f20eb2cda66cf284434ea25a40792f2663ae283017",
    },
    792500: {
        "ledger_hash": "fa73024f2e70f9b3ae64acdb811123ea5d1eaf87a080f60a6b071434980a25f0",
        "txlist_hash": "159e80767cdeaf2195feaaad418266c144fdb1c23e43b5712711509b0450743e",
    },
    793000: {
        "ledger_hash": "5b7e28a25e96e86128882ff040fa9abbd12b7bf2971c71a2aeb6e9aa3c34cf7b",
        "txlist_hash": "f25d1f410b2691990725169017e9c42e3982699646722c29a04156edc000a3e8",
    },
    793500: {
        "ledger_hash": "4a693ab01726d8dbefae5cfaf4eba9021462215cfa63b7b638475d987f5cd1c8",
        "txlist_hash": "9bb933573506c25df3ad1d5fd900590913a2313e20775174ad0d6d494e2b1d5d",
    },
    794000: {
        "ledger_hash": "e04a7aaa8a1c03a9402e820d6ad86709544a181e0ef8a70fe33bd1643b411e31",
        "txlist_hash": "bc1c163c8934af5f294036844ab37dbf9f9776d266bd5a2a15f21d7668bd6e23",
    },
    794500: {
        "ledger_hash": "57c24c3bc6409b00367db331a95825908cfdf28decee8cd35645be082df126d5",
        "txlist_hash": "6aa1c672994857640e30be8554d0d0b9796a8c607c7cbc639e7474c17c25bf27",
    },
    795000: {
        "ledger_hash": "de1e45661219ae5274922dfaa50276c8ae95f4ff8f36aeca33a551750483b1b2",
        "txlist_hash": "e56f7a5d219b95b3280a022736cbf2064a08093b6fcfc703ee2a26523de17d4b",
    },
    795500: {
        "ledger_hash": "4cc36753d519722f2ded5b9c58f9d9d94b7f24883c90f41049906088d5e35d9b",
        "txlist_hash": "b4b7a89d7c0d223c3b173a5b70a4ce95be19527758e963ebf2b8b462449e8af6",
    },
    796000: {
        "ledger_hash": "80a991d5db218e9a375733e5a9c74e24a5b9798e1cae71a9d680042d77c82456",
        "txlist_hash": "d9a64a6ad4c930f7ee1403ce42264732b8a2b43a302cf0afd86b3f6f86bdda2f",
    },
    796500: {
        "ledger_hash": "e71b5bcf23e90426c582a8678c608985d8b3d2785d867fedb63be320b1f58fe7",
        "txlist_hash": "1fa9ce2cf898a049cbe5cf51db1e21751dfe9bc3622a150c6d40a48ae32277dd",
    },
    797000: {
        "ledger_hash": "07d5ce46922f49315dc6921648389fb2342f181d8f4ce6864c937307bc57f78b",
        "txlist_hash": "b952cf5ef8943c4b064772961b76b3bdbdcca83adad448b99e83a88c99025fb1",
    },
    797500: {
        "ledger_hash": "fe757ce4945a78b98d236fca6faabf9ae57894d39cdc73c5529d80d993b22fba",
        "txlist_hash": "5ef7b81a289718bf2803d07866f7a9f7af6a6e9585931a5cf7c20c953e442bdc",
    },
    798000: {
        "ledger_hash": "3419c8588860bbed1e111afd3aa96f3ec7b72af3d9ea295a170d6629920f7c7e",
        "txlist_hash": "2c4437ef523c307ab1c66f9a2f1ebb6c0b96e579da52b7d05598642e2b3e3cb3",
    },
    798500: {
        "ledger_hash": "7b8c30444b232d524f77b5849ae6eecec3ceb316af41027ba82e58637d697e77",
        "txlist_hash": "5e40bf1508dcc0c789c503e8c22dd9032508d1e617fb79675c9a65766720bd56",
    },
    799000: {
        "ledger_hash": "530c774526e30d67d71b3ee415fd29a6a9a3063ec79210e759a77fbdd1dcd0d4",
        "txlist_hash": "23a122876df0d21e4e2645ff51800fad1a749e22a0b580470cafb15592f2e4e1",
    },
    799500: {
        "ledger_hash": "351f2685c82a3592159f5a287dc999a677233e14b24a4a597ecb25ec898a0bc8",
        "txlist_hash": "aaf997a519ca432700dbe87cb4c9d90f28dfd9fc103c4157c124b905ff782605",
    },
    800000: {
        "ledger_hash": "608777958aa89f5465742ba28c82ab24c3aefd402bbb636745088bfb31cf67f4",
        "txlist_hash": "bfc49c705823f30ad63e8f81ec44a364eeb6d48a0e9b2f6374f0934767a3c948",
    },
    800500: {
        "ledger_hash": "6074a03b294f571ae079a242e323a86428848349f928916ad44d9b20f469a5a8",
        "txlist_hash": "f747068f9cfab2e1a5ecda4da3b2320e2c4776089b1b0c60202fc02db2fd7f04",
    },
    801000: {
        "ledger_hash": "7b8595f07982fe4cc62821c65d70b3e5b9d68feb8f5974f2e28ce1a1cfbbe596",
        "txlist_hash": "02b2e3290bbb314bb3fa7dfc81c5cf4c18bf79b31a02529eb0043280fda34b22",
    },
    801500: {
        "ledger_hash": "2542004f0ce0c195e61baa0ea7bc8c5aad76d8fbde069df3ae36c5f9a02baf3b",
        "txlist_hash": "3a77b972e44507668ab570c7e4dd15610b4b5cb6a1c8ed3d7c7c31e853275311",
    },
    802000: {
        "ledger_hash": "2146a998ac0d142b2518d6d94d63d38ba74a4e213196869111d7ea9952381733",
        "txlist_hash": "c9273e9360924ee0ef9e10585db442b5ec1d43d082a993ded9aa382f5e779015",
    },
    802500: {
        "ledger_hash": "6a3e9b1ec8ee3bf15d075f9e378885d72087e0e00af359e52c53c957b5053cec",
        "txlist_hash": "f3f15331e612ec403515cafc6cbfc1791154eeda21fce46494ab5712a8184951",
    },
    803000: {
        "ledger_hash": "5a8fdec7a30316e7a939b874a46e73760a8e7bed61e5377a8e9cce724e1df901",
        "txlist_hash": "9a85ece61f4e56fcd2dda3029776cb9999ef683ceb0cbab7cd31139f2693f2c9",
    },
    803500: {
        "ledger_hash": "3a7758a0c935ce2268da9e05a919ce67232804cd929f7e43860ed1572c475c1e",
        "txlist_hash": "65403001f670456b8ce241e5fdab3345e09d42bd4777b6849f52b51e358973f9",
    },
    804000: {
        "ledger_hash": "0695d792d6ecb357a4947f13fafc015238503f1a5de865c1f3510e016d23abec",
        "txlist_hash": "f12d8bebb4ad034b5d5eedc6b1c75cc9414fb8944d2007bcc3b700099cd40948",
    },
    804500: {
        "ledger_hash": "f150cab8a33c731116e0c8c63db6f4fef45bdb45f8e3af15a5e20e5cf41e08b7",
        "txlist_hash": "e6e760b79d928538692e0fdc5fe9a9c7ef3849485b20847b1084e72ace2f9a55",
    },
    805000: {
        "ledger_hash": "fb0cdf7c440a68876e8fa05b336c3b0d76503ec5c3a417ae06d96ef0226ddadd",
        "txlist_hash": "313f3712ffee8ba4d5aa2b0205fcfdd776cc325aa7da5a321bb0567de1e49d15",
    },
    805500: {
        "ledger_hash": "f85ec5183c000fe1715c311cf281926b5593841cb69cfca0d19c9899c29fa7f9",
        "txlist_hash": "21b00361b1b1c5206af1f0d2e3fa8a9de8aa65158b11f35d6ab88a1a22ead983",
    },
    806000: {
        "ledger_hash": "7ae775019c80b3df133b093e241a0071c8242842458d801b35d618c344b4d10e",
        "txlist_hash": "efdd67a4ecced666b962adad8f0e88500eb6ed6652a2eb6fe774ea1506194590",
    },
    806500: {
        "ledger_hash": "e86bd9e5e694e11a47f915e6831dfeba3ae5d6957dea23f0fb585386fe15b1a2",
        "txlist_hash": "bbb095b066622e7297e849b3f2b5d8344dd2de276fbda1ee85483c0099d9a199",
    },
    807000: {
        "ledger_hash": "18dabe46e3b9199ae8fc3edb20df391fd9607f2467a05eed0f589537f4466641",
        "txlist_hash": "cad5e5429ee8207be8a49c0199c07e25e6e87613e73e8aa79c1247be4c1a95be",
    },
    807500: {
        "ledger_hash": "50c5c1b1d4fae539a1db29b95edf22f2393808f004ddcbcf1698e53c75e918dc",
        "txlist_hash": "0b7fe21bcddcee8d8c08bd805409503b734c538034b63c9a7dde901779e97b22",
    },
    808000: {
        "ledger_hash": "fc59871f8d288740f513531337b6deaf22a7a83c076bd7481234386d44190bca",
        "txlist_hash": "f16c177e98fbef73c7628da37021a13791489e38f5bbaf52da9c5fff6a575cb6",
    },
    808500: {
        "ledger_hash": "a8fef253ae5880e4742203b3677459121c4c974dda8d46b395d075777c498f32",
        "txlist_hash": "6b7a992be65c4d6b4f945a31c4702c564d0791b1c3e10f3cb119add9fbf13669",
    },
    809000: {
        "ledger_hash": "95db90effb39eb7c41acfedf73c9c0966e01cda222fbc3395c554fddce5155ae",
        "txlist_hash": "c5999010c2d22a6b9fef30f2fcc1fe6e130e417c951ac942cf4e536d880fe4fa",
    },
    809500: {
        "ledger_hash": "ffa5ab8c793fde0e9e147af8d4f997ccbf4529e08fa9c397dd58e666d3068c23",
        "txlist_hash": "f90387ff18d8e94391c60af1a0b460b5d63f1c8a22b4fbad6a71a8b2c53fabb8",
    },
    810000: {
        "ledger_hash": "ff7d9defd96b4b1ca716f8e5b313762335f7eeb26dcf6b1b5b629befdd2cbbba",
        "txlist_hash": "0432b1238760c9229f3b71621b2605999fdbaed9502c4536fcc105c4e58c516a",
    },
    810500: {
        "ledger_hash": "8f1c68ba08920385286a911b9a984fcae53f562477f1bfd78069c86dae852106",
        "txlist_hash": "5d3a57c573185dbf432e3dba9a862bbe3bcf44a0f0443e27b265520eedfc0710",
    },
    811000: {
        "ledger_hash": "b27de714230d60cf487c2f81cd8dbc00be37b8d481f370be351097e5fe981879",
        "txlist_hash": "130c217aa4062bdfe0a58096cdef3b3500b4ee67fe5f32e801ed3d390258a846",
    },
    811500: {
        "ledger_hash": "cbce7ef28dac0f45652599e2ce695ed314a3600280166a76ee71186647d906d8",
        "txlist_hash": "0a3a3d4cdedcc08f4b416c477c2b0c0139121fcbf17aa01ded4a7edc96570f90",
    },
    812000: {
        "ledger_hash": "adff6d34efb6eb8efef8032f5894399e8b21dab8da18e29a8ad229d60d6b3548",
        "txlist_hash": "a3593531bd6fac32c6be57f10f22e716c6057028b3645da8d5ff4d29db2b53bd",
    },
    812500: {
        "ledger_hash": "daeac2a78cd464b8e6a2e3306b2d91e7e747d760c2672246db666b4d914f1900",
        "txlist_hash": "f9c4b3c585987aac5d7fd97a5cc937404de6142e5592a36d28fcd22e3a5a8f74",
    },
    813000: {
        "ledger_hash": "0eb4799faaf9e38ba3f225ad9dff690f5d519a4220bbfecc0b307602e7ef8c70",
        "txlist_hash": "551ef3f97b4d928ccc261ab93afd70be7cd4d66df9f0fc134bd5267a0f0f031b",
    },
    813500: {
        "ledger_hash": "717f77faf0e9e4c787587af50ed6e1b604e043e08a668a40a890a302cb0c89e2",
        "txlist_hash": "a9b488c54c1ba46eac7aecac3cde36bb2a918c40fe3e2e01aced2da44f67048b",
    },
    814000: {
        "ledger_hash": "65a2f7eccb13df22e9ee1966f19ccfe392de42d3c976afdfa6920cd891bfe2d8",
        "txlist_hash": "dccb050fa6eb5b34fd32989af5a3a5b4805a9e96b14c53f0e55ee58b96fb1d9e",
    },
    814500: {
        "ledger_hash": "a427946132700a9d41f20edca086e6f3339bb144437f5be55afa9d6362dec454",
        "txlist_hash": "63b2c1b603de93f79fdf8130befd3a5ae7cdac649d502525a7ed07aa15d86f5b",
    },
    815000: {
        "ledger_hash": "ac10892cd249931504091928cc043904ea4156c564236bc1c365834d2613b446",
        "txlist_hash": "11304355f180fb6df6bdbb4c29dd5773571fbb895db005eed7eaadf801db60cd",
    },
    815500: {
        "ledger_hash": "19e3eed1dc8ed3c9658d8fa192ee4ee93b26d73fe90a088cf4d981681d4af665",
        "txlist_hash": "4d987a6c22f64ef88b5981cdbaeb1e6aa5c50414d092f9af8e473160a921203c",
    },
    816000: {
        "ledger_hash": "db5349986ffcad8de88c4775336df7b69aabe1e7eb6d8da59f19177a925fcf5a",
        "txlist_hash": "813959903d405d88f335ca5c5584fef830928f644a4a0c9323d6a58e380e2c72",
    },
    816500: {
        "ledger_hash": "6dc7e6b3448f0a81f9567ecb5bd677f40f9b3090f7d2bd1b45197b2f09341744",
        "txlist_hash": "8e875380f228a058d1adbabf83c53f4bf336fab9feb338eb7c0d6fd6f0fa61ef",
    },
    817000: {
        "ledger_hash": "583ba6a5bd70fd6a8991b2d4fb01256e6f88f53a08db4a1e31d777f40f112d61",
        "txlist_hash": "cd7e37a897dc03468321c41990f947f74de9d0df5dd28ef76b36252fff04df00",
    },
    817500: {
        "ledger_hash": "13dbce4e7beae630c3d8bf6d9ea05d9802311e603e97c9eba2df6193944cba32",
        "txlist_hash": "c1e95697cd94a206eb8a88e686264982fa73066d58a14a3738f1788a244ad3f0",
    },
    818000: {
        "ledger_hash": "36bb5b07c13d0646c6aed798c02d5013f837f35c8632749fa9b1fce88a112751",
        "txlist_hash": "90400654cb90116f5c0d80c687bb85a81bacfc05ff835d2259f992d890e93ac7",
    },
    818500: {
        "ledger_hash": "3fdecb9031a108b308eab7334ddf77f534c41c757837f821a23cffd5cc2eb70a",
        "txlist_hash": "4b19e461f08062a3de1284f5f2901afecb48a74b4043efa2289260f60102fa28",
    },
    819000: {
        "ledger_hash": "5f3baea09970bd53634728e4779d458c5049b95ddaea668f91defb7dd50d7a83",
        "txlist_hash": "de4fc83c68d3fcdfb36218136f7913b741163240f86b798aacfe0dc0a2be0747",
    },
    819500: {
        "ledger_hash": "d0a504dd3205594c711a8a2ff1c8e13631a32d522e3870ceb9abcd75d223bbb5",
        "txlist_hash": "a58eeb487b7cfefb1ba9a582005abe088fae36eaffcc8934e1958d64b76d0397",
    },
    820000: {
        "ledger_hash": "fa663ed80c1ac185162cb3d4101c9c5c0023e8b2ff3b4837b7378765b75bc472",
        "txlist_hash": "e9ddc32575d88d3db4bab405e93375a36ac94c7c4e0f517a05042030a910bd24",
    },
    820500: {
        "ledger_hash": "d68ab258478c3276cd46976e79b3db924800847055879ec3c7727836432a37ab",
        "txlist_hash": "1d88f2d94977f0f8b48b4a33e8169597aad971c0951575fc74a48b97afb2080f",
    },
    821000: {
        "ledger_hash": "b32609efcf007d51e253a3f03c25f47941022493380c593a2c2477914cd4439c",
        "txlist_hash": "ee5640c80b46fb9641b94cf65cdbd293a417ce250183110088df1173926acad0",
    },
    821500: {
        "ledger_hash": "d5448768cbcc354da578c52658dfc2fc946cd7c15fb469bdd371187ab4a9141b",
        "txlist_hash": "089c3ab0af5dd54abd5310d222772aac19bb78d99d26bd5308df75281762a59b",
    },
    822000: {
        "ledger_hash": "a4dd55cd4a838ca5a0b0e985b58813b63722770020942e12763acc94f6789178",
        "txlist_hash": "1fad6af3b0661de06077bdbe8e33ac587891421c34860411842dabe25ba8b240",
    },
    822500: {
        "ledger_hash": "62b3ef907776ea6fe8793b8d7ff343c2355b767fd192b11885fb7575597cd0b2",
        "txlist_hash": "8738084248b99a68688d10c977de0a8e41016727098480e8b4a991b98f6e54c8",
    },
    823000: {
        "ledger_hash": "48e8b707c1da708fec90068fadbdccb3add79842fbf6b4e0c58da2e1fef00821",
        "txlist_hash": "53dd28b40d7ba794794458570fb880b108f9bc255f77721da128ac06f2e96e94",
    },
    823500: {
        "ledger_hash": "472a198e035ac2c16c0037a9dd4390218673afb27fca333b566299ff610166b4",
        "txlist_hash": "6ba608ca2d916ff04ff9e207b55a0dc683c90d5254594ca17d733894a2c3957c",
    },
    824000: {
        "ledger_hash": "81e2a32544239f6666da01eef71c1731d9227eb18dfab906bd3b2ccc2513ab97",
        "txlist_hash": "98b89c19185b6dea7942048efa40e995c51f9621c67a57d9a1d32061a5da0282",
    },
    824500: {
        "ledger_hash": "a9b6586bcc48db135fdb05fd723a9440116da83de8b150e0cc65201e8790a42a",
        "txlist_hash": "2f14438fbf9174dfd0e92e8d8f20aa856b4fbdb0ab1051064e5edde10a228e29",
    },
    825000: {
        "ledger_hash": "6215c84352544cb6f48033b98b10ed8d54dffda01572406b26e4be4654ebbcaf",
        "txlist_hash": "543433ff913bf701b426cdd96ac472825b517c2b22973985bde6bc2dd3d7fc24",
    },
    826000: {
        "ledger_hash": "07a2324c96f132f7479c9d7aa304e2cc8422bde146c49966b28c3e8080ee3c9a",
        "txlist_hash": "6cb181cc35022b08a1cb43610c8eec6af5b0e05b5d600b3225a6108c00e2987d",
    },
    827000: {
        "ledger_hash": "85d492ff08c659d0e7a5b32b05baac5be115a84190466dd8b5b715c61411207d",
        "txlist_hash": "08173eda8b7189a29a33c83059e92f4968e78ac883c516b7be566d03f28ca75a",
    },
    828000: {
        "ledger_hash": "82d59a5980543caf10d538e110bd78e391a6a7f906566b6a1db7ee485d0d0380",
        "txlist_hash": "13c17d1cf50f75d7c09b4ae72861af3712239475a6e2b3bbf0aca6b339d46601",
    },
    829000: {
        "ledger_hash": "a19efdab4c157e82ef428051437c90621fa164278a7626f76cc85efe473e458b",
        "txlist_hash": "b326e64ec807702354ff0e1bb191893cbde2b73a03c7e2684a6602de2f994050",
    },
    830000: {
        "ledger_hash": "dd5d454d490cdb1b08bf4a6358065972bc9960f56fdbff43a00957373c1a39ae",
        "txlist_hash": "92b7d7f0bc59e1e867e8d5e7c408f93d051288e6192c2a8fb204d80993c6ae57",
    },
    831000: {
        "ledger_hash": "cbba4f45cc4697c6d6b5c076e0ce8b4db6acb3667954f079fcb9feb907673e4c",
        "txlist_hash": "68667fb10b61c713326e22142e26d1fa7b0b2924b8d790b0400e836dbfc8b100",
    },
    832000: {
        "ledger_hash": "56607511952b91c76f13e3f4615d59aa17a8da4f96062b4c8ecf8e2200dd0c6e",
        "txlist_hash": "65cab78d55fc5f7b8b03e7a4dcda9d764813d87b780066ef1f60ea243721337d",
    },
    833000: {
        "ledger_hash": "d3864ffc35caba41917e0caf49d1d30367837cb82cbf03eb97efa54a9879c42f",
        "txlist_hash": "7b18037abeb8190d753f22682d5493f1de1c4b7c4ed6ef592f421b5a2b4d91e3",
    },
    834000: {
        "ledger_hash": "3dd8b91827082d0143728ddff37d17e6ab91029f34836a2c316ad9ef5d494ecf",
        "txlist_hash": "09f21ff2a847de4a1fe823c6161810c684702956d53cb2602d31d27bef47466b",
    },
    834500: {
        "ledger_hash": "33737a3dc13d9e01e488869a951724f40b6e30e52966905434ee228d3d2cf0f3",
        "txlist_hash": "df88725c205fef2ab157c93ec3894d6b8ee96ecd8b442fa6faede4db9641ed47",
    },
    835515: {
        "ledger_hash": "110ef9801c7ff27aa68d81226f60009a7a5f087228a97ce2af1b1df6be210689",
        "txlist_hash": "33753e3a1917d1c9b506de152aa5e19de3ee8d65ed086214d9838372d0618039",
    },
    838863: {
        "ledger_hash": "af0a56fcb6fd0da3c007c311f063e256060997a0658ea1128ea08763eaa95383",
        "txlist_hash": "7735e7b52d2e2bca4ef76de0a5a543a910a2bfe41f2e189236f04aa09a455340",
    },
    839910: {
        "ledger_hash": "e41bae2ddd431d1ddfeb9403b1b2f04e2ea75baeb991636e1a7fc5b4302605f4",
        "txlist_hash": "76ff941f15588a41124839acc80cc655407242154ba452285a348f17146807b7",
    },
    842208: {
        "ledger_hash": "6440b7d750fd29c2e9714df93989859cac1adef2b6098a7e1ef6d5ca7bb4f366",
        "txlist_hash": "6e49153c8042f20227ffc52b4df7a450a8f8416230081e373dabf11e9aceb63d",
    },
    847469: {
        "ledger_hash": "60dad3b667c237ef4430e703863048b949ba1f62a13e895a64b4ba9381b959f9",
        "txlist_hash": "b59af166c3300e2e0f53951fa2663d6d717c69610bc0fa86b8d7b4675398870d",
    },
    850500: {
        "ledger_hash": "0e594ca2b3b36b66475b1c53d9b02d9fe4726e28f6f61db8fdf8103a787e6c3e",
        "txlist_hash": "993c980296307d38656b4458a9b3913a8028adc02630fb6a8c55bea009008dd7",
    },
    861500: {
        "ledger_hash": "76ca4415a24ae04579b05b517f41441b7cb45eb881db71d1b59de5d373a4bc28",
        "txlist_hash": "b05b906391cf96d5b4b5893c5fda13fb64635d26785ee3ad1330fe701eb41cb4",
    },
    866000: {
        "ledger_hash": "5bfa1fef4356b1326c8edfe1af582911461d86132dd768028511d20ed2d9e3f5",
        "txlist_hash": "19d1621ea05abd741e05e361ce96708e8dc1b442fb89079af370abd2698549db",
    },
    866330: {
        "ledger_hash": "1c5f82ee5009fbc3d94bb8ff88d644aa0b2ec42f21409b315f555f1006bca6fc",
        "txlist_hash": "1f5db508a80205eaaa6d915402c7833a0851bb369bea54a600e2fdda7e1d7ff5",
    },
    866750: {
        "ledger_hash": "1c5164faca831bb726666eb6c63e5d8fd4070b382706c30f839ed407526c7de4",
        "txlist_hash": "a536d8a1b2b3cf6164b9a2cd70edd2efaea615340e11291eebb6201c762aaaf5",
    },
    867290: {
        "ledger_hash": "4b5c0ab384408c9e7268c24887f3d2265a0b045f5a161e3343d15cf861b7d07c",
        "txlist_hash": "b32df1c46cde54f9eb1075652634276d5fb997a85ca7394c6566810475b30c00",
    },
    869836: {
        "ledger_hash": "cffb619abf5cbf297d3bf837369cae8e80eafb047bc26db9698d2ea6fd7cb9b9",
        "txlist_hash": "58786555420ed0e1aa160d572adf33bf622842069212fd3f3aaf2889ff5b968f",
    },
    871781: {
        "ledger_hash": "f214d9ed443e0034e1d3508f016086a841fb89036baae1aae857d273ef2a0b76",
        "txlist_hash": "f378bfec19139f0210808ef8d6c548452cca9e631e5742786d2af7595534106c",
    },
    872500: {
        "ledger_hash": "33e10cb33cdc65e8fc2e048410e093f452af6a38c58d1e1dc813ae1c7f4e266c",
        "txlist_hash": "2f4cf3574a61a7575445dc9ad6f8650750bc0f93a03e586d65ec1c69322009a3",
    },
    873000: {
        "ledger_hash": "73afdb48583a746c524e6459df8e2f208c15487055cc72a8186415ca7a65b077",
        "txlist_hash": "a52eee6dc316f3fac4c19c48b6b52c3018ba1ba44a6dcf34c52303e9031ec300",
    },
    873500: {
        "ledger_hash": "94b33eaca19f90e99a5a624dacc774d88ed91def33be25526cdfab705cae3b89",
        "txlist_hash": "e085948ac68caf6b0718373ca80e8fbee5436e88c3c95c3a8fec39d08db8e646",
    },
    874548: {
        "ledger_hash": "8e55b64d0dfd85a58e3a9dd27ce49efd98559d96f16f53beb66a10b7671ea857",
        "txlist_hash": "b3f549168f56702287c7b06c0348c4ac0adffcd219bab386d2f19326c0cd491c",
    },
    874883: {
        "ledger_hash": "4c4d6b660af23bb03a04bbf93ddd0a4b8e615dd7b883ecf827274cabe658bfc2",
        "txlist_hash": "f6a99d60337c33c1822c048f56e241455cd7e45bb5a9515096f1ac609d50f669",
    },
    879058: {
        "ledger_hash": "e6bf730a18c148adbd2cce9bd0f361e595e44d53fa98a9d9bdbf4c944f6c233b",
        "txlist_hash": "e9946ac128405885f251fbb98a952ed554ea6cc25973261da9f40eabf4f3b429",
    },
}

CONSENSUS_HASH_VERSION_TESTNET3 = 7
CHECKPOINTS_TESTNET = {
    config.BLOCK_FIRST_TESTNET: {
        "ledger_hash": "63f0fef31d02da85fa779e9a0e1b585b1a6a4e59e14564249e288e074e91c223",
        "txlist_hash": "63f0fef31d02da85fa779e9a0e1b585b1a6a4e59e14564249e288e074e91c223",
    },
    316000: {
        "ledger_hash": "f645e6877da416b8b91670ac927df686c5ea6fc1158c150ae49d594222ed504c",
        "txlist_hash": "3e29bcbf3873326097024cc26e9296f0164f552dd79c2ee7cfc344e6d64fa87d",
    },
    319000: {
        "ledger_hash": "384ca28ac56976bc24a6ab7572b41bc61474e6b87fdee814135701d6a8f5c8a2",
        "txlist_hash": "6c05c98418a6daa6de82dd59e000d3f3f5407c5432d4ab7d76047873a38e4d4b",
    },
    322000: {
        "ledger_hash": "f4015c37eb4f31ac42083fd0389cde4868acb5353d3f3abfe2f3a88aba8cae72",
        "txlist_hash": "18f278154e9bc3bbcc39da905ab4ad3023742ab7723b55b0fd1c58c36cd3e9bf",
    },
    325000: {
        "ledger_hash": "d7f70a927f5aeed38e559ddc0bc4697601477ea43cde928ad228fefc195b02da",
        "txlist_hash": "1a60e38664b39e0f501b3e5a60c6fc0bd4ed311b74872922c2dde4cb2267fd3e",
    },
    329000: {
        "ledger_hash": "96637b4400cbe084c2c4f139f59b5bc16770815e96306423aaeb2b2677a9a657",
        "txlist_hash": "79d577d8fbba0ad6ae67829dfa5824f758286ccd429d65b7d1d42989134d5b57",
    },
    350000: {
        "ledger_hash": "cae8fec787bba3d5c968a8f4b6fb22a54c96d5acbeadd0425f6b20c3a8813ea3",
        "txlist_hash": "097df9c3079df4d96f59518df72492dfd7a79716462e3a4a30d62a37aec6fc16",
    },
    400000: {
        "ledger_hash": "94abfd9c00c8462c155f64011e71af141b7d524e17de5aeda26b7469fe79b5f0",
        "txlist_hash": "a9fc42b69f80ec69f3f98e8a3cd81f4f946544fd0561a62a0891254c16970a87",
    },
    450000: {
        "ledger_hash": "09eb9f2aa605ce77225362b4b556284acdd9f6d3bc273372dfae4a5be9e9b035",
        "txlist_hash": "05af651c1de49d0728834991e50000fbf2286d7928961b71917f682a0f2b7171",
    },
    500000: {
        "ledger_hash": "85f3bca8c88246ddfa1a5ec327e71f0696c182ed2a5fedf3712cd2e87e2661ac",
        "txlist_hash": "663b34955116a96501e0c1c27f27d24bad7d45995913367553c5cfe4b8b9d0a9",
    },
    550000: {
        "ledger_hash": "c143026133af2d83bc49ef205b4623194466ca3e7c79f95da2ad565359ccb5ad",
        "txlist_hash": "097b8bca7a243e0b9bdf089f34de15bd2dcd4727fb4e88aae7bfd96302250326",
    },
    600000: {
        "ledger_hash": "82caf720967d0e43a1c49a6c75f255d9056ed1bffe3f96d962478faccdaba8ff",
        "txlist_hash": "0d99f42184233426d70102d5ac3c80aaecf804d441a8a0d0ef26038d333ab7a7",
    },
    650000: {
        "ledger_hash": "bef100ae7d5027a8b3f32416c4f26e1f16b21cee2a986c57be1466a3ba338051",
        "txlist_hash": "409ed86e4274b511193d187df92e433c734dcc890bf93496e7a7dee770e7035e",
    },
    700000: {
        "ledger_hash": "afe5e9c3f3a8c6f19c4f9feaf09df051c28202c6bae64f3563a09ffea9e79a6e",
        "txlist_hash": "4f9765158855d24950c7e076615b0ad5b72738d4d579decfd3b93c998edf4fcb",
    },
    750000: {
        "ledger_hash": "e7c7969a6156facb193b77ef71b5e3fac49c6998e5a94ec3b90292be10ece9cc",
        "txlist_hash": "6e511790656d3ffec0c912d697e5d1c2a4e401a1606203c77ab5a5855891bc2c",
    },
    800000: {
        "ledger_hash": "42a7c679e51e5e8d38df26b67673b4850e8e6f72723aa19673b3219fcc02b77b",
        "txlist_hash": "885ae1e6c21f5fb3645231aaa6bb6910fc21a0ae0ca5dbe9a4011f3b5295b3e7",
    },
    850000: {
        "ledger_hash": "35b2a2ab4a8bfbc321d4545292887b4ccaea73415c7674f795aefa6e240890eb",
        "txlist_hash": "72d5cfe1e729a22da9eacd4d7752c881c43a191904556b65a0fae82b770dcdf3",
    },
    900000: {
        "ledger_hash": "a5552b4998d2e5a516b9310d6592e7368771c1ad3b6e6330f6bc0baa3db31643",
        "txlist_hash": "5a2e9fbd9b52ee32b8e8bfff993ed92dc22510aa7448277a704176cf01e55b04",
    },
    950000: {
        "ledger_hash": "5a5e78b55ac294690229abff7ff8f74f390f3a47dc4d08a0bac40e2e89a5bed2",
        "txlist_hash": "f4fa9838fb38d3e5beffb760fae022dcc59c61c506dd28ac83ee48ba814d04b2",
    },
    1000000: {
        "ledger_hash": "eafca6700b9fd8f3992f8a18316e9ad59480ef74a4e7737793c101878aba8e1a",
        "txlist_hash": "03deb626e031f30acd394bf49c35e11a487cb11e55dff5ba9a3f6d04b460c7de",
    },
    1050000: {
        "ledger_hash": "8012ebaf4c6638173e88ecd3e7bb2242ab88a9bdf877fc32c42dbcd7d2d3bab1",
        "txlist_hash": "896274fdba957961083b07b80634126bc9f0434b67d723ed1fa83157ce5cd9a7",
    },
    1100000: {
        "ledger_hash": "76357f917235daa180c904cdf5c44366eef3e33539b7b0ba6a38f89582e82d22",
        "txlist_hash": "36ecfd4b07f23176cd6960bc0adef97472c13793e53ac3df0eea0dd2e718a570",
    },
    1150000: {
        "ledger_hash": "5924f004bfdc3be449401c764808ebced542d2e06ba30c5984830292d1a926aa",
        "txlist_hash": "9ff139dacf4b04293074e962153b972d25fa16d862dae05f7f3acc15e83c4fe8",
    },
    1200000: {
        "ledger_hash": "a3d009bd2e0b838c185b8866233d7b4edaff87e5ec4cc4719578d1a8f9f8fe34",
        "txlist_hash": "11dcf3a0ab714f05004a4e6c77fe425eb2a6427e4c98b7032412ab29363ffbb2",
    },
    1250000: {
        "ledger_hash": "37244453b4eac67d1dbfc0f60116cac90dab7b814d756653ad3d9a072fbac61a",
        "txlist_hash": "c01ed3113f8fd3a6b54f5cefafd842ebf7c314ce82922e36236414d820c5277a",
    },
    1300000: {
        "ledger_hash": "a83c1cd582604130fd46f1304560caf0f4e3300f3ce7c3a89824b8901f13027f",
        "txlist_hash": "67e663b75a80940941b8370ada4985be583edaa7ba454d49db9a864a7bb7979c",
    },
    1350000: {
        "ledger_hash": "f96e6aff578896a4568fb69f72aa0a8b52eb9ebffefca4bd7368790341cd821d",
        "txlist_hash": "83e7d31217af274b13889bd8b9f8f61afcd7996c2c8913e9b53b1d575f54b7c1",
    },
    1400000: {
        "ledger_hash": "85a23f6fee9ce9c80fa335729312183ff014920bbf297095ac77c4105fb67e17",
        "txlist_hash": "eee762f34a3f82e6332c58e0c256757d97ca308719323af78bf5924f08463e12",
    },
    1600000: {
        "ledger_hash": "f2d54a74ca0974e3d22d4499f10579bb9afbf761178a0a127832f59496c8c24a",
        "txlist_hash": "f720b44719e01a1dbcffe572947a88d943c4841365bea744debc7d26007611c9",
    },
    1700000: {
        "ledger_hash": "afb9f59bd6ffa51e847ec4495eedb182e449bac341b1bf2b9ccfacaec15ef4b6",
        "txlist_hash": "473eab0cf9c07dd869d57839d886efca0b03769672cbb659dc542d748cf77711",
    },
    1800000: {
        "ledger_hash": "09060e590d936f67e6248b60496d1bdd94143cfa935be6a16246d2edec59da9b",
        "txlist_hash": "bc26c44d4ce55be408b38fe14e4659fa655a8386e2d389fe3b7bfb25b4364bd3",
    },
    1900000: {
        "ledger_hash": "357da2e773cab15472419cba2deec47462003a64bf416970ebf47e91b4fac85a",
        "txlist_hash": "2b4d321495f04a3065bdd4f0987fd86a54669fb85426152eb1b4a1b8fd11d799",
    },
    2000000: {
        "ledger_hash": "a2575c20d58a4e69a1d19ceb2e1d615b3b1052e92d5a34c61b03bbab4cc4efc0",
        "txlist_hash": "79249281e49719805533be84006c2c48be7ea0c3d14048c1205458c90e7b3158",
    },
    2200000: {
        "ledger_hash": "c74b27600be79479bf4be3f4499e05283381a6996f3151db69bff10b29b95a10",
        "txlist_hash": "8f4ffacc471fd80c8327d163ebe7ff26a0d00ec03672acaff911d16eb37547fd",
    },
    2400000: {
        "ledger_hash": "5c0606e2729d9b2a2181388231fd816ce3279c4183137bf62e9c699dbdc2f140",
        "txlist_hash": "36bbd14c69e5fc17cb1e69303affcb808909757395d28e3e3da83394260bf0dd",
    },
    2500000: {
        "ledger_hash": "76262b272c47b5a17f19ffa0ba72256617bd18e51fad4c3c5b3c776cb3a1037b",
        "txlist_hash": "26567e5c45a59426b2bcdeb177167a92c5fc21e8fd2000ae9a24eb09e3945f70",
    },
    2540000: {
        "ledger_hash": "6d3e77f1c059b062f4eb131cc8eb1d8355598de756905d83803df0009a514f48",
        "txlist_hash": "45e134cb4196bc5cfb4ef9b356e02025f752a9bc0ae635bc9ced2c471ecfcb6c",
    },
    2580000: {
        "ledger_hash": "f84878f8e1293cd5365fc66ec7acbc24b4201b79ab3125d7e60e26624f49037a",
        "txlist_hash": "dc1f037beb8a632c5277fa0e6fd52866f0370d1f93de024420a7c31ce956c812",
    },
    2586067: {
        "ledger_hash": "104b61a4d22d793674a4c869ebdcc3030dc49794f36d270c4e51126cfd969135",
        "txlist_hash": "1bfe60296102f50272abc664ee42f4fb70818b7211e36dafa6e6bad6194fc833",
    },
    2820893: {
        "ledger_hash": "83feb31ce5edf67250c01f5cca4dbec91a32e5189a9b14d23ad2348bafaadaaf",
        "txlist_hash": "5db6363332cee5ccd16370af747050bad438a6bcf52f2004b3b9db1c8b8ef8ee",
    },
}

CONSENSUS_HASH_VERSION_REGTEST = 1
CHECKPOINTS_REGTEST = {
    config.BLOCK_FIRST_REGTEST: {
        "ledger_hash": "33cf0669a0d309d7e6b1bf79494613b69262b58c0ea03c9c221d955eb4c84fe5",
        "txlist_hash": "33cf0669a0d309d7e6b1bf79494613b69262b58c0ea03c9c221d955eb4c84fe5",
    },
}

CONSENSUS_HASH_VERSION_TESTNET4 = 1
CHECKPOINTS_TESTNET4 = {
    config.BLOCK_FIRST_TESTNET4: {
        "ledger_hash": "33cf0669a0d309d7e6b1bf79494613b69262b58c0ea03c9c221d955eb4c84fe5",
        "txlist_hash": "33cf0669a0d309d7e6b1bf79494613b69262b58c0ea03c9c221d955eb4c84fe5",
    },
    64493: {
        "ledger_hash": "af481088fb9303d0f61543fb3646110fcd27d5ebd3ac40e04397000320216699",
        "txlist_hash": "4b610518a76f59e8f98922f37434be9bb5567040afebabda6ee69b4f92b80434",
    },
}


class ConsensusError(Exception):
    pass


def consensus_hash(db, field, previous_consensus_hash, content):
    assert field in ("ledger_hash", "txlist_hash", "messages_hash")

    cursor = db.cursor()
    block_index = util.CURRENT_BLOCK_INDEX

    # Initialise previous hash on first block.
    if block_index <= config.BLOCK_FIRST:
        assert not previous_consensus_hash
        previous_consensus_hash = util.dhash_string(CONSENSUS_HASH_SEED)

    # Get previous hash.
    if not previous_consensus_hash:
        try:
            previous_consensus_hash = list(
                cursor.execute("""SELECT * FROM blocks WHERE block_index = ?""", (block_index - 1,))
            )[0][field]
        except IndexError:
            previous_consensus_hash = None
        if not previous_consensus_hash:
            raise ConsensusError(
                f"Empty previous {field} for block {block_index}. Please launch a `rollback`."
            )

    # Calculate current hash.
    if config.TESTNET3:
        consensus_hash_version = CONSENSUS_HASH_VERSION_TESTNET3
    elif config.TESTNET4:
        consensus_hash_version = CONSENSUS_HASH_VERSION_TESTNET4
    elif config.REGTEST:
        consensus_hash_version = CONSENSUS_HASH_VERSION_REGTEST
    else:
        consensus_hash_version = CONSENSUS_HASH_VERSION_MAINNET

    calculated_hash = util.dhash_string(
        previous_consensus_hash + f"{consensus_hash_version}{''.join(content)}"
    )

    # Verify hash (if already in database) or save hash (if not).
    # NOTE: do not enforce this for messages_hashes, those are more informational (for now at least)
    found_hash = (
        list(cursor.execute("""SELECT * FROM blocks WHERE block_index = ?""", (block_index,)))[0][
            field
        ]
        or None
    )
    if found_hash and field != "messages_hash":
        # Check against existing value.
        if calculated_hash != found_hash:
            raise ConsensusError(
                f"Inconsistent {field} for block {block_index} (calculated {calculated_hash}, vs {found_hash} in database)."
            )

    # Check against checkpoints.
    if config.TESTNET3:
        checkpoints = CHECKPOINTS_TESTNET
    elif config.TESTNET4:
        checkpoints = CHECKPOINTS_TESTNET4
    elif config.REGTEST:
        checkpoints = CHECKPOINTS_REGTEST
    else:
        checkpoints = CHECKPOINTS_MAINNET

    if (
        field != "messages_hash"
        and block_index in checkpoints
        and checkpoints[block_index][field] != calculated_hash
    ):
        error_message = f"Incorrect {field} hash for block {block_index}.  Calculated {calculated_hash} but expected {checkpoints[block_index][field]}"
        raise ConsensusError(error_message)

    return calculated_hash, found_hash


class SanityError(Exception):
    pass


def asset_conservation(db, stop_event=None):
    logger.debug("Checking for conservation of assets.")
    with db:
        supplies = ledger.supplies(db)
        held = ledger.held(db)
        for asset in supplies.keys():
            if stop_event is not None and stop_event.is_set():
                logger.debug("Stop event received. Exiting asset conservation check...")
                return
            asset_issued = supplies[asset]
            asset_held = held[asset] if asset in held and held[asset] != None else 0  # noqa: E711
            if asset_issued != asset_held:
                raise SanityError(
                    "{} {} issued ≠ {} {} held".format(
                        ledger.value_out(db, asset_issued, asset),
                        asset,
                        ledger.value_out(db, asset_held, asset),
                        asset,
                    )
                )
            logger.trace(
                "{} has been conserved ({} {} both issued and held)".format(
                    asset, ledger.value_out(db, asset_issued, asset), asset
                )
            )
    logger.debug("All assets have been conserved.")


class VersionError(Exception):
    pass


class VersionUpdateRequiredError(VersionError):
    pass


def check_change(protocol_change, change_name):
    # Check client version.
    passed = True
    if config.VERSION_MAJOR < protocol_change["minimum_version_major"]:
        passed = False
    elif config.VERSION_MAJOR == protocol_change["minimum_version_major"]:
        if config.VERSION_MINOR < protocol_change["minimum_version_minor"]:
            passed = False
        elif config.VERSION_MINOR == protocol_change["minimum_version_minor"]:
            if config.VERSION_REVISION < protocol_change["minimum_version_revision"]:
                passed = False

    if not passed:
        explanation = f"Your version of {config.APP_NAME} is v{config.VERSION_STRING}, but, "
        explanation += f"as of block {protocol_change['block_index']}, the minimum version is "
        explanation += f"v{protocol_change['minimum_version_major']}.{protocol_change['minimum_version_minor']}.{protocol_change['minimum_version_revision']}. "
        explanation += f"Reason: ' {change_name} '. Please upgrade to the latest version and restart the server."
        if util.CURRENT_BLOCK_INDEX >= protocol_change["block_index"]:
            raise VersionUpdateRequiredError(explanation)
        else:
            warnings.warn(explanation)  # noqa: B028


def software_version():
    if config.FORCE:
        return
    logger.debug("Checking Counterparty version...")

    try:
        response = requests.get(
            config.PROTOCOL_CHANGES_URL, headers={"cache-control": "no-cache"}, timeout=10
        )
        versions = json.loads(response.text)
    except (
        requests.exceptions.ConnectionError,
        ConnectionRefusedError,
        ValueError,
        requests.exceptions.ReadTimeout,
        TimeoutError,
    ):
        logger.warning("Unable to check Counterparty version.")
        return False

    for change_name in versions:
        protocol_change = versions[change_name]
        try:
            check_change(protocol_change, change_name)
        except VersionUpdateRequiredError:  # noqa: F841
            logger.error("Version Update Required")
            sys.exit(config.EXITCODE_UPDATE_REQUIRED)

    logger.debug("Version check passed.")
    return True


class DatabaseVersionError(Exception):
    def __init__(self, message, required_action, from_block_index=None):
        super(DatabaseVersionError, self).__init__(message)
        self.required_action = required_action
        self.from_block_index = from_block_index


def check_need_reparse(version_minor, message):
    if config.FORCE:
        return
    if config.TESTNET4:
        need_reparse_from = config.NEED_REPARSE_IF_MINOR_IS_LESS_THAN_TESTNET4
    elif config.TESTNET3:
        need_reparse_from = config.NEED_REPARSE_IF_MINOR_IS_LESS_THAN_TESTNET3
    else:
        need_reparse_from = config.NEED_REPARSE_IF_MINOR_IS_LESS_THAN
    if need_reparse_from is not None:
        for min_version_minor, min_version_block_index in need_reparse_from:
            if version_minor < min_version_minor:
                raise DatabaseVersionError(
                    message=message,
                    required_action="reparse",
                    from_block_index=min_version_block_index,
                )


def check_need_rollback(version_minor, message):
    if config.FORCE:
        return
    if config.TESTNET4:
        need_rollback_from = config.NEED_ROLLBACK_IF_MINOR_IS_LESS_THAN_TESTNET4
    elif config.TESTNET3:
        need_rollback_from = config.NEED_ROLLBACK_IF_MINOR_IS_LESS_THAN_TESTNET3
    else:
        need_rollback_from = config.NEED_ROLLBACK_IF_MINOR_IS_LESS_THAN
    if need_rollback_from is not None:
        for min_version_minor, min_version_block_index in need_rollback_from:
            if version_minor < min_version_minor:
                raise DatabaseVersionError(
                    message=message,
                    required_action="rollback",
                    from_block_index=min_version_block_index,
                )


def database_version(db):
    if config.FORCE:
        return
    logger.debug("Checking database version...")

    version_major, version_minor = database.version(db)
    if version_major != config.VERSION_MAJOR:
        # Rollback database if major version has changed.
        raise DatabaseVersionError(
            message=f"Client major version number mismatch: {version_major} ≠ {config.VERSION_MAJOR}.",
            required_action="rollback",
            from_block_index=config.BLOCK_FIRST,
        )
    elif version_minor != config.VERSION_MINOR:
        # Reparse transactions from the vesion block if minor version has changed.
        message = (
            f"Client minor version number mismatch: {version_minor} ≠ {config.VERSION_MINOR}. "
        )
        message += "Checking if a rollback or a reparse is needed..."
        check_need_rollback(version_minor, message)
        check_need_reparse(version_minor, message)
        raise DatabaseVersionError(message=message, required_action=None)
    else:
        version_string = database.get_config_value(db, "VERSION_STRING")
        if version_string:
            version_pre_release = "-".join(version_string.split("-")[1:])
        else:
            # if version_string is not set, that mean we are on a version before 10.5.0 and after 10.4.8
            # let's assume it's a pre-release version
            # and set an arbitrary value different from config.VERSION_PRE_RELEASE
            version_pre_release = "xxxx"
        if version_pre_release != config.VERSION_PRE_RELEASE:
            if version_pre_release == "xxxx":
                message = "`VERSION_STRING` not found in dataase. "
            else:
                message = f"Client pre-release version number mismatch: {version_pre_release} ≠ {config.VERSION_PRE_RELEASE}. "
            message += "Checking if a rollback or a reparse is needed..."
            check_need_rollback(version_minor, message)
            check_need_reparse(version_minor, message)
