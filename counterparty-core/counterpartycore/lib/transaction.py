"""
Construct and serialize the Bitcoin transactions that are Counterparty transactions.

This module contains no consensus‐critical code.
"""

import binascii
import decimal
import hashlib
import inspect
import io
import json
import logging
import sys
import threading

import bitcoin as bitcoinlib
import cachetools
import varint
from bitcoin.core import CTransaction

from counterpartycore.lib import (
    arc4,  # noqa: F401 # TODO: need for test: clean that up
    backend,
    config,
    deserialize,
    exceptions,
    gettxinfo,
    message_type,
    messages,
    script,
    util,
)
from counterpartycore.lib.backend import addrindexrs
from counterpartycore.lib.messages import dispense  # noqa: F401
from counterpartycore.lib.transaction_helper import p2sh_encoding, serializer

# Constants
OP_RETURN = b"\x6a"
OP_PUSHDATA1 = b"\x4c"
OP_DUP = b"\x76"
OP_HASH160 = b"\xa9"
OP_EQUALVERIFY = b"\x88"
OP_CHECKSIG = b"\xac"
OP_0 = b"\x00"
OP_1 = b"\x51"
OP_2 = b"\x52"
OP_3 = b"\x53"
OP_CHECKMULTISIG = b"\xae"
OP_EQUAL = b"\x87"

D = decimal.Decimal


# FILE AS SINGLETON API
#
# We eventually neet to rip this out and just instantiate the TransactionService
# when we explcitly build up a dependency tree.

TRANSACTION_SERVICE_SINGLETON = None


def initialise(force=False):
    global TRANSACTION_SERVICE_SINGLETON  # noqa: PLW0603

    if not force and TRANSACTION_SERVICE_SINGLETON:
        return TRANSACTION_SERVICE_SINGLETON

    utxo_locks = None
    if config.UTXO_LOCKS_MAX_ADDRESSES > 0:
        utxo_locks = util.DictCache(size=config.UTXO_LOCKS_MAX_ADDRESSES)

    TRANSACTION_SERVICE_SINGLETON = TransactionService(
        backend=backend,
        prefix=util.prefix(util.CURRENT_BLOCK_INDEX),
        ps2h_dust_return_pubkey=config.P2SH_DUST_RETURN_PUBKEY,
        utxo_locks_max_age=config.UTXO_LOCKS_MAX_AGE,
        utxo_locks_max_addresses=config.UTXO_LOCKS_MAX_ADDRESSES,
        default_regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
        default_multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
        estimate_fee_mode=config.ESTIMATE_FEE_MODE,
        op_return_max_size=config.OP_RETURN_MAX_SIZE,
        utxo_locks=utxo_locks,
        utxo_p2sh_encoding_locks=ThreadSafeTTLCache(10000, 180),
        utxo_p2sh_encoding_locks_cache=ThreadSafeTTLCache(1000, 600),
    )


def construct(
    db,
    tx_info,
    encoding="auto",
    fee_per_kb=config.DEFAULT_FEE_PER_KB,
    estimate_fee_per_kb=None,
    estimate_fee_per_kb_nblocks=config.ESTIMATE_FEE_CONF_TARGET,
    regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
    multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
    op_return_value=config.DEFAULT_OP_RETURN_VALUE,
    exact_fee=None,
    fee_provided=0,
    provided_pubkeys=None,
    dust_return_pubkey=None,
    allow_unconfirmed_inputs=False,
    unspent_tx_hash=None,
    custom_inputs=None,
    disable_utxo_locks=False,
    extended_tx_info=False,
    old_style_api=None,
    segwit=False,
    p2sh_source_multisig_pubkeys=None,
    p2sh_source_multisig_pubkeys_required=None,
    p2sh_pretx_txid=None,
    exclude_utxos="",
):
    if TRANSACTION_SERVICE_SINGLETON is None:
        raise Exception("Transaction not initialized")

    return TRANSACTION_SERVICE_SINGLETON.construct(
        db,
        tx_info,
        encoding,
        fee_per_kb,
        estimate_fee_per_kb,
        estimate_fee_per_kb_nblocks,
        regular_dust_size,
        multisig_dust_size,
        op_return_value,
        exact_fee,
        fee_provided,
        provided_pubkeys,
        dust_return_pubkey,
        allow_unconfirmed_inputs,
        unspent_tx_hash,
        custom_inputs,
        disable_utxo_locks,
        extended_tx_info,
        old_style_api,
        segwit,
        p2sh_source_multisig_pubkeys,
        p2sh_source_multisig_pubkeys_required,
        p2sh_pretx_txid,
        exclude_utxos,
    )


class BaseThreadSafeCache:
    def __init__(self, *args, **kwargs):
        # Note: reading is thread safe out of the box
        self.lock = threading.Lock()
        self.__cache = self.create_cache(*args, **kwargs)

    def create_cache(self, *args, **kwargs):
        raise NotImplementedError

    def get(self, key, default=None):
        return self.__cache.get(key, default)

    def pop(self, key, default=None):
        with self.lock:
            return self.__cache.pop(key, default)

    def delete(self, key):
        with self.lock:
            try:
                del self.__cache[key]
            except KeyError:
                pass

    def _get_cache(self):
        return self.__cache

    def set(self, key, value):
        with self.lock:
            try:
                self.__cache[key] = value
            except KeyError:
                pass

    def keys(self):
        return self.__cache.keys()

    def __len__(self):
        return len(self.__cache)

    def __iter__(self):
        return iter(self.__cache)

    def __contains__(self, key):
        return key in self.__cache


class ThreadSafeTTLCache(BaseThreadSafeCache):
    def create_cache(self, *args, **kwargs):
        return cachetools.TTLCache(*args, **kwargs)


def sort_unspent_txouts(unspent, dust_size=config.DEFAULT_REGULAR_DUST_SIZE):
    # Filter out all dust amounts to avoid bloating the resultant transaction
    unspent = list(filter(lambda x: x["value"] > dust_size, unspent))
    # Sort by amount, using the largest UTXOs available
    if config.REGTEST:
        # REGTEST has a lot of coinbase inputs that can't be spent due to maturity
        # this doesn't usually happens on mainnet or testnet because most fednodes aren't mining
        unspent = sorted(unspent, key=lambda x: (x["confirmations"], x["value"]), reverse=True)
    else:
        unspent = sorted(unspent, key=lambda x: x["value"], reverse=True)

    return unspent


def pubkeyhash_to_pubkey(pubkeyhash, provided_pubkeys=None):
    # Search provided pubkeys.
    if provided_pubkeys:
        if type(provided_pubkeys) != list:  # noqa: E721
            provided_pubkeys = [provided_pubkeys]
        for pubkey in provided_pubkeys:
            if pubkeyhash == script.pubkey_to_pubkeyhash(util.unhexlify(pubkey)):
                return pubkey
            elif pubkeyhash == script.pubkey_to_p2whash(util.unhexlify(pubkey)):
                return pubkey

    # Search blockchain.
    raw_transactions = addrindexrs.search_raw_transactions(pubkeyhash, unconfirmed=True)
    for tx_id in raw_transactions:
        tx = raw_transactions[tx_id]
        for vin in tx["vin"]:
            if "txinwitness" in vin:
                if len(vin["txinwitness"]) >= 2:
                    # catch unhexlify errs for when txinwitness[1] isn't a witness program (eg; for P2W)
                    try:
                        pubkey = vin["txinwitness"][1]
                        if pubkeyhash == script.pubkey_to_p2whash(util.unhexlify(pubkey)):
                            return pubkey
                    except binascii.Error:
                        pass
            elif "coinbase" not in vin:
                scriptsig = vin["scriptSig"]
                asm = scriptsig["asm"].split(" ")
                if len(asm) >= 2:
                    # catch unhexlify errs for when asm[1] isn't a pubkey (eg; for P2SH)
                    try:
                        pubkey = asm[1]
                        if pubkeyhash == script.pubkey_to_pubkeyhash(util.unhexlify(pubkey)):
                            return pubkey
                    except binascii.Error:
                        pass

    raise exceptions.UnknownPubKeyError(
        "Public key was neither provided nor published in blockchain."
    )


def multisig_pubkeyhashes_to_pubkeys(address, provided_pubkeys=None):
    signatures_required, pubkeyhashes, signatures_possible = script.extract_array(address)
    pubkeys = [pubkeyhash_to_pubkey(pubkeyhash, provided_pubkeys) for pubkeyhash in pubkeyhashes]
    return script.construct_array(signatures_required, pubkeys, signatures_possible)


# set higher than the max number of UTXOs we should expect to
# manage in an aging cache for any one source address, at any one period
# UTXO_P2SH_ENCODING_LOCKS is TTLCache for UTXOs that are used for chaining p2sh encoding
#  instead of a simple (txid, vout) key we use [(vin.prevout.hash, vin.prevout.n) for vin tx1.vin]
# we cache the make_outkey_vin to avoid having to fetch raw txs too often


class TransactionService:
    def __init__(
        self,
        backend,
        prefix,
        ps2h_dust_return_pubkey,
        utxo_locks_max_age=3.0,
        utxo_locks_max_addresses=1000,
        utxo_locks_per_address_maxsize=5000,
        default_regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
        default_multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
        estimate_fee_mode=config.ESTIMATE_FEE_MODE,
        op_return_max_size=config.OP_RETURN_MAX_SIZE,
        utxo_p2sh_encoding_locks=None,
        utxo_p2sh_encoding_locks_cache=None,
        utxo_locks=None,
    ):
        self.logger = logging.getLogger(
            config.LOGGER_NAME
        )  # has to be config.LOGGER_NAME or integration tests fail
        self.backend = backend

        self.utxo_p2sh_encoding_locks = utxo_p2sh_encoding_locks or ThreadSafeTTLCache(10000, 180)
        self.utxo_p2sh_encoding_locks_cache = utxo_p2sh_encoding_locks_cache or ThreadSafeTTLCache(
            1000, 600
        )
        self.utxo_locks = utxo_locks

        self.utxo_locks_max_age = utxo_locks_max_age
        self.utxo_locks_max_addresses = utxo_locks_max_addresses
        self.utxo_locks_per_address_maxsize = utxo_locks_per_address_maxsize

        self.default_regular_dust_size = default_regular_dust_size
        self.default_multisig_dust_size = default_multisig_dust_size
        self.estimate_fee_mode = estimate_fee_mode

        self.prefix = prefix
        self.op_return_max_size = op_return_max_size
        self.ps2h_dust_return_pubkey = ps2h_dust_return_pubkey

    def get_dust_return_pubkey(self, source, provided_pubkeys, encoding):
        """Return the pubkey to which dust from data outputs will be sent.

        This pubkey is used in multi-sig data outputs (as the only real pubkey) to
        make those the outputs spendable. It is derived from the source address, so
        that the dust is spendable by the creator of the transaction.
        """
        # Get hex dust return pubkey.
        # inject `script`
        if script.is_multisig(source):
            a, self_pubkeys, b = script.extract_array(
                multisig_pubkeyhashes_to_pubkeys(source, provided_pubkeys)
            )
            dust_return_pubkey_hex = self_pubkeys[0]
        else:
            dust_return_pubkey_hex = pubkeyhash_to_pubkey(source, provided_pubkeys)

        # Convert hex public key into the (binary) dust return pubkey.
        try:
            dust_return_pubkey = binascii.unhexlify(dust_return_pubkey_hex)
        except binascii.Error:
            raise script.InputError("Invalid private key.")  # noqa: B904

        return dust_return_pubkey

    def make_outkey_vin_txid(self, txid, vout):
        if (txid, vout) not in self.utxo_p2sh_encoding_locks_cache:
            txhex = self.backend.bitcoind.getrawtransaction(txid, verbose=False)
            self.utxo_p2sh_encoding_locks_cache.set((txid, vout), make_outkey_vin(txhex, vout))

        return self.utxo_p2sh_encoding_locks_cache.get((txid, vout))

    def construct_coin_selection(
        self,
        encoding,
        data_array,
        source,
        allow_unconfirmed_inputs,
        unspent_tx_hash,
        custom_inputs,
        fee_per_kb,
        estimate_fee_per_kb,
        estimate_fee_per_kb_nblocks,
        exact_fee,
        size_for_fee,
        fee_provided,
        destination_btc_out,
        data_btc_out,
        regular_dust_size,
        disable_utxo_locks,
        exclude_utxos,
    ):
        # Array of UTXOs, as retrieved by listunspent function from bitcoind
        if custom_inputs:
            use_inputs = unspent = custom_inputs
        else:
            if unspent_tx_hash is not None:
                unspent = self.backend.addrindexrs.get_unspent_txouts(
                    source,
                    unconfirmed=allow_unconfirmed_inputs,
                    unspent_tx_hash=unspent_tx_hash,
                )
            else:
                unspent = self.backend.addrindexrs.get_unspent_txouts(
                    source, unconfirmed=allow_unconfirmed_inputs
                )
            self.logger.trace(
                f"TX Construct - Unspent UTXOs: {[print_coin(coin) for coin in unspent]}"
            )
            if len(unspent) == 0:
                raise exceptions.BalanceError(
                    f"Insufficient {config.BTC} at address {source}: no unspent outputs."
                )

            filter_unspents_utxo_locks = []
            if self.utxo_locks is not None and source in self.utxo_locks:
                filter_unspents_utxo_locks = self.utxo_locks[source].keys()
            filter_unspents_p2sh_locks = self.utxo_p2sh_encoding_locks.keys()  # filter out any locked UTXOs to prevent creating transactions that spend the same UTXO when they're created at the same time
            filtered_unspent = []
            for output in unspent:
                if (
                    make_outkey(output) not in filter_unspents_utxo_locks
                    and self.make_outkey_vin_txid(output["txid"], output["vout"])
                    not in filter_unspents_p2sh_locks
                    and f"{output['txid']}:{output['vout']}" not in exclude_utxos.split(",")
                ):
                    filtered_unspent.append(output)
            unspent = filtered_unspent

            if encoding == "multisig":
                dust = self.default_multisig_dust_size
            else:
                dust = self.default_regular_dust_size

            unspent = sort_unspent_txouts(unspent, dust_size=dust)
            # self.logger.debug(f"Sorted candidate UTXOs: {[print_coin(coin) for coin in unspent]}")
            use_inputs = unspent

        # use backend estimated fee_per_kb
        if estimate_fee_per_kb:
            estimated_fee_per_kb = self.backend.bitcoind.fee_per_kb(
                estimate_fee_per_kb_nblocks, config.ESTIMATE_FEE_MODE
            )
            if estimated_fee_per_kb is not None:
                fee_per_kb = max(
                    estimated_fee_per_kb, fee_per_kb
                )  # never drop below the default fee_per_kb

        self.logger.trace(f"TX Construct - Fee/KB {fee_per_kb / config.UNIT:.8f}")

        inputs = []
        btc_in = 0
        change_quantity = 0
        sufficient_funds = False
        final_fee = fee_per_kb
        desired_input_count = 1

        if encoding == "multisig" and data_array and util.enabled("bytespersigop"):
            desired_input_count = len(data_array) * 2

        # pop inputs until we can pay for the fee
        use_inputs_index = 0
        for coin in use_inputs:
            self.logger.trace(f"TX Construct - New input: {print_coin(coin)}")
            inputs.append(coin)
            btc_in += round(coin["amount"] * config.UNIT)

            # If exact fee is specified, use that. Otherwise, calculate size of tx
            # and base fee on that (plus provide a minimum fee for selling BTC).
            size = 181 * len(inputs) + size_for_fee + 10
            if exact_fee:
                final_fee = exact_fee
            else:
                necessary_fee = int(size / 1000 * fee_per_kb)
                final_fee = max(fee_provided, necessary_fee)
                self.logger.trace(
                    f"TX Construct - final_fee inputs: {len(inputs)} size: {size} final_fee {final_fee}"
                )

            # Check if good.
            btc_out = destination_btc_out + data_btc_out
            change_quantity = btc_in - (btc_out + final_fee)
            self.logger.trace(
                f"TX Construct - Size: {size} Fee: {final_fee / config.UNIT:.8f} Change quantity: {change_quantity / config.UNIT:.8f} BTC"
            )

            # If after the sum of all the utxos the change is dust, then it will be added to the miners instead of returning an error
            if (
                (use_inputs_index == len(use_inputs) - 1)
                and (change_quantity > 0)
                and (change_quantity < regular_dust_size)
            ):
                sufficient_funds = True
                final_fee = final_fee + change_quantity
                change_quantity = 0
            # If change is necessary, must not be a dust output.
            elif change_quantity == 0 or change_quantity >= regular_dust_size:
                sufficient_funds = True
                if len(inputs) >= desired_input_count:
                    break

            use_inputs_index = use_inputs_index + 1

        if not sufficient_funds:
            # Approximate needed change, fee by with most recently calculated
            # quantities.
            btc_out = destination_btc_out + data_btc_out
            total_btc_out = btc_out + max(change_quantity, 0) + final_fee

            need = f"{D(total_btc_out) / D(config.UNIT)} {config.BTC}"
            include_fee = f"{D(final_fee) / D(config.UNIT)} {config.BTC}"
            available = f"{D(btc_in) / D(config.UNIT)} {config.BTC}"
            error_message = f"Insufficient {config.BTC} at address {source}. Need: {need} (Including fee: {include_fee}), available: {available}."
            error_message += f" These fees are estimated for a confirmation target of {estimate_fee_per_kb_nblocks} blocks, you can reduce them by using the `confirmation_target` parameter with a higher value or by manually setting the fees with the `fee` parameter."

            if not allow_unconfirmed_inputs:
                error_message += " To spend unconfirmed coins, use the flag `--unconfirmed`. (Unconfirmed coins cannot be spent from multi‐sig addresses.)"

            raise exceptions.BalanceError(error_message)

        # Lock the source's inputs (UTXOs) chosen for this transaction
        if self.utxo_locks is not None and not disable_utxo_locks:
            if source not in self.utxo_locks:
                self.utxo_locks[source] = ThreadSafeTTLCache(
                    self.utxo_locks_per_address_maxsize, self.utxo_locks_max_age
                )

            for input in inputs:
                self.utxo_locks[source].set(make_outkey(input), input)

            # list_unspent = [make_outkey(coin) for coin in unspent]
            # list_used = [make_outkey(input) for input in inputs]
            # list_locked = list(self.utxo_locks[source].keys())
            # self.logger.debug(
            #     f"UTXO locks: Potentials ({len(unspent)}): {list_unspent}, Used: {list_used}, locked UTXOs: {list_locked}"
            # )

        # ensure inputs have scriptPubKey
        #   this is not provided by indexd
        inputs = script.ensure_script_pub_key_for_inputs(inputs)

        return inputs, change_quantity, btc_in, final_fee

    def select_any_coin_from_source(
        self, source, allow_unconfirmed_inputs=True, disable_utxo_locks=False
    ):
        """Get the first (biggest) input from the source address"""

        # Array of UTXOs, as retrieved by listunspent function from bitcoind
        unspent = self.backend.addrindexrs.get_unspent_txouts(
            source, unconfirmed=allow_unconfirmed_inputs
        )

        filter_unspents_utxo_locks = []
        if self.utxo_locks is not None and source in self.utxo_locks:
            filter_unspents_utxo_locks = self.utxo_locks[source].keys()

        # filter out any locked UTXOs to prevent creating transactions that spend the same UTXO when they're created at the same time
        filtered_unspent = []
        for output in unspent:
            if make_outkey(output) not in filter_unspents_utxo_locks:
                filtered_unspent.append(output)
        unspent = filtered_unspent

        # sort
        unspent = sort_unspent_txouts(unspent, dust_size=config.DEFAULT_REGULAR_DUST_SIZE)

        # use the first input
        input = unspent[0]
        if input is None:
            return None

        # Lock the source's inputs (UTXOs) chosen for this transaction
        if self.utxo_locks is not None and not disable_utxo_locks:
            if source not in self.utxo_locks:
                # TODO: dont ref cache tools directly
                self.utxo_locks[source] = cachetools.TTLCache(
                    self.utxo_locks_per_address_maxsize, self.utxo_locks_max_age
                )

            self.utxo_locks[source].set(make_outkey(input), input)

        return input

    def construct(
        self,
        db,
        tx_info,
        encoding="auto",
        fee_per_kb=config.DEFAULT_FEE_PER_KB,
        estimate_fee_per_kb=None,
        estimate_fee_per_kb_nblocks=config.ESTIMATE_FEE_CONF_TARGET,
        regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
        multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
        op_return_value=config.DEFAULT_OP_RETURN_VALUE,
        exact_fee=None,
        fee_provided=0,
        provided_pubkeys=None,
        dust_return_pubkey=None,
        allow_unconfirmed_inputs=False,
        unspent_tx_hash=None,
        custom_inputs=None,
        disable_utxo_locks=False,
        extended_tx_info=False,
        old_style_api=None,
        segwit=False,
        p2sh_source_multisig_pubkeys=None,
        p2sh_source_multisig_pubkeys_required=None,
        p2sh_pretx_txid=None,
        exclude_utxos="",
    ):
        if estimate_fee_per_kb is None:
            estimate_fee_per_kb = config.ESTIMATE_FEE_PER_KB

        # lazy assign from config, because when set as default it's evaluated before it's configured
        if old_style_api is None:
            old_style_api = config.OLD_STYLE_API

        (source, destination_outputs, data) = tx_info

        if dust_return_pubkey:
            dust_return_pubkey = binascii.unhexlify(dust_return_pubkey)

        if p2sh_source_multisig_pubkeys:
            p2sh_source_multisig_pubkeys = [
                binascii.unhexlify(p) for p in p2sh_source_multisig_pubkeys
            ]

        # Source.
        # If public key is necessary for construction of (unsigned)
        # transaction, use the public key provided, or find it from the
        # blockchain.
        if source:
            script.validate(source)

        source_is_p2sh = script.is_p2sh(source)

        # Normalize source
        if script.is_multisig(source):
            source_address = multisig_pubkeyhashes_to_pubkeys(source, provided_pubkeys)
        else:
            source_address = source

        # Sanity checks.
        if exact_fee and not isinstance(exact_fee, int):
            raise exceptions.TransactionError("Exact fees must be in satoshis.")
        if not isinstance(fee_provided, int):
            raise exceptions.TransactionError("Fee provided must be in satoshis.")

        """Determine encoding method"""

        if data:
            desired_encoding = encoding
            # Data encoding methods (choose and validate).
            if desired_encoding == "auto":
                if len(data) + len(self.prefix) <= self.op_return_max_size:
                    encoding = "opreturn"
                else:
                    encoding = (
                        "p2sh"
                        if not old_style_api and util.enabled("p2sh_encoding")
                        else "multisig"
                    )  # p2sh is not possible with old_style_api

            elif desired_encoding == "p2sh" and not util.enabled("p2sh_encoding"):
                raise exceptions.TransactionError("P2SH encoding not enabled yet")

            elif encoding not in ("pubkeyhash", "multisig", "opreturn", "p2sh"):
                raise exceptions.TransactionError("Unknown encoding‐scheme.")
        else:
            # no data
            encoding = None
        if encoding:
            self.logger.debug(
                f"TX Construct - Constructing `{encoding.upper()}` transaction from {source}."
            )
        else:
            self.logger.debug(f"TX Construct - Constructing transaction from {source}.")

        """Destinations"""

        # Destination outputs.
        # Replace multi‐sig addresses with multi‐sig pubkeys. Check that the
        # destination output isn’t a dust output. Set null values to dust size.
        destination_outputs_new = []
        if encoding != "p2sh":
            for address, value in destination_outputs:
                # Value.
                if script.is_multisig(address):
                    dust_size = multisig_dust_size
                else:
                    dust_size = regular_dust_size
                if value == None:  # noqa: E711
                    value = dust_size  # noqa: PLW2901
                elif value < dust_size:
                    raise exceptions.TransactionError("Destination output is dust.")

                # Address.
                script.validate(address)
                if script.is_multisig(address):
                    destination_outputs_new.append(
                        (
                            multisig_pubkeyhashes_to_pubkeys(address, provided_pubkeys),
                            value,
                        )
                    )
                else:
                    destination_outputs_new.append((address, value))

        destination_outputs = destination_outputs_new
        destination_btc_out = sum([value for address, value in destination_outputs])

        """Data"""

        if data:
            # @TODO: p2sh encoding require signable dust key
            if encoding == "multisig":
                # dust_return_pubkey should be set or explicitly set to False to use the default configured for the node
                #  the default for the node is optional so could fail
                if (source_is_p2sh and dust_return_pubkey is None) or (
                    dust_return_pubkey is False and self.ps2h_dust_return_pubkey is None
                ):
                    raise exceptions.TransactionError(
                        "Can't use multisig encoding when source is P2SH and no dust_return_pubkey is provided."
                    )
                elif dust_return_pubkey is False:
                    dust_return_pubkey = binascii.unhexlify(self.ps2h_dust_return_pubkey)

            if not dust_return_pubkey:
                if encoding == "multisig" or encoding == "p2sh" and not source_is_p2sh:
                    dust_return_pubkey = self.get_dust_return_pubkey(
                        source, provided_pubkeys, encoding
                    )
                else:
                    dust_return_pubkey = None

            # Divide data into chunks.
            if encoding == "pubkeyhash":
                # Prefix is also a suffix here.
                chunk_size = 20 - 1 - 8
            elif encoding == "multisig":
                # Two pubkeys, minus length byte, minus prefix, minus two nonces,
                # minus two sign bytes.
                chunk_size = (33 * 2) - 1 - 8 - 2 - 2
            elif encoding == "p2sh":
                pubkeylength = -1
                if dust_return_pubkey is not None:
                    pubkeylength = len(dust_return_pubkey)

                chunk_size = p2sh_encoding.maximum_data_chunk_size(
                    pubkeylength, util.CURRENT_BLOCK_INDEX
                )
            elif encoding == "opreturn":
                chunk_size = config.OP_RETURN_MAX_SIZE
                if len(data) + len(self.prefix) > chunk_size:
                    raise exceptions.TransactionError("One `OP_RETURN` output per transaction.")
            data_array = list(chunks(data, chunk_size))

            # Data outputs.
            if encoding == "multisig":
                data_value = multisig_dust_size
            elif encoding == "p2sh":
                data_value = 0  # this will be calculated later
            elif encoding == "opreturn":
                data_value = op_return_value
            else:
                # Pay‐to‐PubKeyHash, e.g.
                data_value = regular_dust_size
            data_output = (data_array, data_value)

        else:
            data_value = 0
            data_array = []
            data_output = None
            dust_return_pubkey = None

        data_btc_out = data_value * len(data_array)
        self.logger.trace(
            f"TX Construct - data_btc_out={data_btc_out} (data_value={data_value} len(data_array)={len(data_array)})"
        )

        """Inputs"""
        btc_in = 0
        final_fee = 0
        # Calculate collective size of outputs, for fee calculation.
        p2pkhsize = 25 + 9
        if encoding == "multisig":
            data_output_size = 81  # 71 for the data
        elif encoding == "opreturn":
            # prefix + data + 10 bytes script overhead
            data_output_size = len(self.prefix) + 10
            if data is not None:
                data_output_size = data_output_size + len(data)
        else:
            data_output_size = p2pkhsize  # Pay‐to‐PubKeyHash (25 for the data?)

        if encoding == "p2sh":
            # calculate all the p2sh outputs
            size_for_fee, datatx_necessary_fee, data_value, data_btc_out = (
                p2sh_encoding.calculate_outputs(
                    destination_outputs, data_array, fee_per_kb, exact_fee
                )
            )
            # replace the data value
            data_output = (data_array, data_value)
        else:
            sum_data_output_size = len(data_array) * data_output_size
            size_for_fee = ((25 + 9) * len(destination_outputs)) + sum_data_output_size

        if not (encoding == "p2sh" and p2sh_pretx_txid):
            inputs, change_quantity, n_btc_in, n_final_fee = self.construct_coin_selection(
                encoding,
                data_array,
                source,
                allow_unconfirmed_inputs,
                unspent_tx_hash,
                custom_inputs,
                fee_per_kb,
                estimate_fee_per_kb,
                estimate_fee_per_kb_nblocks,
                exact_fee,
                size_for_fee,
                fee_provided,
                destination_btc_out,
                data_btc_out,
                regular_dust_size,
                disable_utxo_locks,
                exclude_utxos,
            )
            btc_in = n_btc_in
            final_fee = n_final_fee
        else:
            # when encoding is P2SH and the pretx txid is passed we can skip coinselection
            inputs, change_quantity = None, None

        """Finish"""

        if change_quantity:
            change_output = (source_address, change_quantity)
        else:
            change_output = None

        unsigned_pretx_hex = None
        unsigned_tx_hex = None

        pretx_txid = None
        if encoding == "p2sh":
            assert not (segwit and p2sh_pretx_txid)  # shouldn't do old style with segwit enabled

            if p2sh_pretx_txid:
                pretx_txid = (
                    p2sh_pretx_txid
                    if isinstance(p2sh_pretx_txid, bytes)
                    else binascii.unhexlify(p2sh_pretx_txid)
                )
                unsigned_pretx = None
            else:
                destination_value_sum = sum([value for (destination, value) in destination_outputs])
                source_value = destination_value_sum

                if change_output:
                    # add the difference between source and destination to the change
                    change_value = change_output[1] + (destination_value_sum - source_value)
                    change_output = (change_output[0], change_value)

                unsigned_pretx = serializer.serialise_p2sh_pretx(
                    inputs,
                    source=source_address,
                    source_value=source_value,
                    data_output=data_output,
                    block_index=util.CURRENT_BLOCK_INDEX,
                    change_output=change_output,
                    pubkey=dust_return_pubkey,
                    multisig_pubkeys=p2sh_source_multisig_pubkeys,
                    multisig_pubkeys_required=p2sh_source_multisig_pubkeys_required,
                )
                unsigned_pretx_hex = binascii.hexlify(unsigned_pretx).decode("utf-8")

            # with segwit we already know the txid and can return both
            if segwit:
                # pretx_txid = hashlib.sha256(unsigned_pretx).digest()  # this should be segwit txid
                ptx = CTransaction.stream_deserialize(
                    io.BytesIO(unsigned_pretx)
                )  # could be a non-segwit tx anyways
                txid_ba = bytearray(ptx.GetTxid())
                txid_ba.reverse()
                pretx_txid = bytes(txid_ba)  # gonna leave the malleability problem to upstream
                self.logger.debug(f"pretx_txid {pretx_txid}")

            if unsigned_pretx:
                # we set a long lock on this, don't want other TXs to spend from it
                self.utxo_p2sh_encoding_locks.set(make_outkey_vin(unsigned_pretx, 0), True)

            # only generate the data TX if we have the pretx txId
            if pretx_txid:
                source_input = None
                if script.is_p2sh(source):
                    source_input = self.select_any_coin_from_source(source)
                    if not source_input:
                        raise exceptions.TransactionError(
                            "Unable to select source input for p2sh source address"
                        )

                unsigned_datatx = serializer.serialise_p2sh_datatx(
                    pretx_txid,
                    source=source_address,
                    source_input=source_input,
                    destination_outputs=destination_outputs,
                    data_output=data_output,
                    block_index=util.CURRENT_BLOCK_INDEX,
                    pubkey=dust_return_pubkey,
                    multisig_pubkeys=p2sh_source_multisig_pubkeys,
                    multisig_pubkeys_required=p2sh_source_multisig_pubkeys_required,
                )
                unsigned_datatx_hex = binascii.hexlify(unsigned_datatx).decode("utf-8")

                # let the rest of the code work it's magic on the data tx
                unsigned_tx_hex = unsigned_datatx_hex
            else:
                # we're just gonna return the pretx, it doesn't require any of the further checks
                self.logger.warning(f"old_style_api = {old_style_api}")
                return return_result([unsigned_pretx_hex], old_style_api=old_style_api)

        else:
            # Serialise inputs and outputs.
            unsigned_tx = serializer.serialise(
                encoding,
                inputs,
                destination_outputs,
                util.CURRENT_BLOCK_INDEX,
                data_output,
                change_output,
                dust_return_pubkey=dust_return_pubkey,
            )
            unsigned_tx_hex = binascii.hexlify(unsigned_tx).decode("utf-8")

        """Sanity Check"""

        # Desired transaction info.
        (desired_source, desired_destination_outputs, desired_data) = tx_info
        desired_source = script.make_canonical(desired_source)
        desired_destination = (
            script.make_canonical(desired_destination_outputs[0][0])
            if desired_destination_outputs
            else ""
        )
        # NOTE: Include change in destinations for BTC transactions.
        # if change_output and not desired_data and desired_destination != config.UNSPENDABLE:
        #    if desired_destination == '':
        #        desired_destination = desired_source
        #    else:
        #        desired_destination += f'-{desired_source}'
        # NOTE
        if desired_data == None:  # noqa: E711
            desired_data = b""

        # Parsed transaction info.
        try:
            parsed_source, parsed_destination, x, y, parsed_data, extra = (
                # TODO: inject
                gettxinfo.get_tx_info_new(
                    db,
                    deserialize.deserialize_tx(unsigned_tx_hex, use_txid=True),
                    util.CURRENT_BLOCK_INDEX,
                    p2sh_is_segwit=script.is_bech32(desired_source),
                    composing=True,
                )
            )

            if encoding == "p2sh":
                # make_canonical can't determine the address, so we blindly change the desired to the parsed
                desired_source = parsed_source
        except exceptions.BTCOnlyError:
            # Skip BTC‐only transactions.
            if extended_tx_info:
                return {
                    "btc_in": btc_in,
                    "btc_out": destination_btc_out + data_btc_out,
                    "btc_change": change_quantity,
                    "btc_fee": final_fee,
                    "tx_hex": unsigned_tx_hex,
                }
            self.logger.trace("TX Construct - Skip BTC‐only transactions")
            return return_result([unsigned_pretx_hex, unsigned_tx_hex], old_style_api=old_style_api)
        desired_source = script.make_canonical(desired_source)

        # Check desired info against parsed info.
        if util.enabled("new_tx_format") and desired_data:
            flags = desired_data[0]  # noqa F841
            desired_data = desired_data[1:]
        desired = (desired_source, desired_destination, desired_data)
        parsed = (parsed_source, parsed_destination, parsed_data)
        if desired != parsed:
            # Unlock (revert) UTXO locks
            if self.utxo_locks is not None and inputs:
                for input in inputs:
                    self.utxo_locks[source].pop(make_outkey(input), None)

            raise exceptions.TransactionError(
                f"Constructed transaction does not parse correctly: {desired} ≠ {parsed}"
            )

        if extended_tx_info:
            return {
                "btc_in": btc_in,
                "btc_out": destination_btc_out + data_btc_out,
                "btc_change": change_quantity,
                "btc_fee": final_fee,
                "tx_hex": unsigned_tx_hex,
            }

        self.logger.debug("TX Construct - Transaction constructed.")
        return return_result([unsigned_pretx_hex, unsigned_tx_hex], old_style_api=old_style_api)


# UTILS


def print_coin(coin):
    return f"amount: {coin['amount']:.8f}; txid: {coin['txid']}; vout: {coin['vout']}; confirmations: {coin.get('confirmations', '?')}"  # simplify and make deterministic


def chunks(l, n):  # noqa: E741
    """Yield successive n‐sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def make_outkey(output):
    return f"{output['txid']}{output['vout']}"


def make_outkey_vin(txhex, vout):
    txbin = binascii.unhexlify(txhex) if isinstance(txhex, str) else txhex
    assert isinstance(vout, int)

    tx = bitcoinlib.core.CTransaction.deserialize(txbin)
    outkey = [(vin.prevout.hash, vin.prevout.n) for vin in tx.vin]
    outkey = hashlib.sha256((f"{outkey}{vout}").encode("ascii")).digest()

    return outkey


def return_result(tx_hexes, old_style_api):
    tx_hexes = list(filter(None, tx_hexes))  # filter out None

    if old_style_api:
        if len(tx_hexes) != 1:
            raise Exception("Can't do 2 TXs with old_style_api")

        return tx_hexes[0]
    else:
        if len(tx_hexes) == 1:
            return tx_hexes[0]
        else:
            return tx_hexes


# TODO: this should be lifted
def get_dust_return_pubkey(source, provided_pubkeys, encoding):
    """Return the pubkey to which dust from data outputs will be sent.

    This pubkey is used in multi-sig data outputs (as the only real pubkey) to
    make those the outputs spendable. It is derived from the source address, so
    that the dust is spendable by the creator of the transaction.
    """
    # Get hex dust return pubkey.
    if script.is_multisig(source):
        a, self_pubkeys, b = script.extract_array(
            multisig_pubkeyhashes_to_pubkeys(source, provided_pubkeys)
        )
        dust_return_pubkey_hex = self_pubkeys[0]
    else:
        dust_return_pubkey_hex = pubkeyhash_to_pubkey(source, provided_pubkeys)

    # Convert hex public key into the (binary) dust return pubkey.
    try:
        dust_return_pubkey = binascii.unhexlify(dust_return_pubkey_hex)
    except binascii.Error:
        raise script.InputError("Invalid private key.")  # noqa: B904

    return dust_return_pubkey


COMPOSE_COMMONS_ARGS = {
    "encoding": (str, "auto", "The encoding method to use"),
    "fee_per_kb": (
        int,
        None,
        "The fee per kilobyte of transaction data constant that the server uses when deciding on the dynamic fee to use (in satoshis)",
    ),
    "regular_dust_size": (
        int,
        config.DEFAULT_REGULAR_DUST_SIZE,
        "Specify (in satoshis) to override the (dust) amount of BTC used for each non-(bare) multisig output.",
    ),
    "multisig_dust_size": (
        int,
        config.DEFAULT_MULTISIG_DUST_SIZE,
        "Specify (in satoshis) to override the (dust) amount of BTC used for each (bare) multisig output",
    ),
    "pubkey": (
        str,
        None,
        "The hexadecimal public key of the source address (or a list of the keys, if multi-sig). Required when using encoding parameter values of multisig or pubkeyhash.",
    ),
    "allow_unconfirmed_inputs": (
        bool,
        False,
        "Set to true to allow this transaction to utilize unconfirmed UTXOs as inputs",
    ),
    "fee": (
        int,
        None,
        "If you'd like to specify a custom miners' fee, specify it here (in satoshis). Leave as default for the server to automatically choose",
    ),
    "fee_provided": (
        int,
        0,
        "If you would like to specify a maximum fee (up to and including which may be used as the transaction fee), specify it here (in satoshis). This differs from fee in that this is an upper bound value, which fee is an exact value",
    ),
    "unspent_tx_hash": (
        str,
        None,
        "When compiling the UTXOs to use as inputs for the transaction being created, only consider unspent outputs from this specific transaction hash. Defaults to null to consider all UTXOs for the address. Do not use this parameter if you are specifying custom_inputs",
    ),
    "dust_return_pubkey": (
        str,
        None,
        "The dust return pubkey is used in multi-sig data outputs (as the only real pubkey) to make those the outputs spendable. By default, this pubkey is taken from the pubkey used in the first transaction input. However, it can be overridden here (and is required to be specified if a P2SH input is used and multisig is used as the data output encoding.) If specified, specify the public key (in hex format) where dust will be returned to so that it can be reclaimed. Only valid/useful when used with transactions that utilize multisig data encoding. Note that if this value is set to false, this instructs counterparty-server to use the default dust return pubkey configured at the node level. If this default is not set at the node level, the call will generate an exception",
    ),
    "disable_utxo_locks": (
        bool,
        False,
        "By default, UTXOs utilized when creating a transaction are 'locked' for a few seconds, to prevent a case where rapidly generating create_ calls reuse UTXOs due to their spent status not being updated in bitcoind yet. Specify true for this parameter to disable this behavior, and not temporarily lock UTXOs",
    ),
    "extended_tx_info": (
        bool,
        False,
        "When this is not specified or false, the create_ calls return only a hex-encoded string. If this is true, the create_ calls return a data object with the following keys: tx_hex, btc_in, btc_out, btc_change, and btc_fee",
    ),
    "p2sh_pretx_txid": (
        str,
        None,
        "The previous transaction txid for a two part P2SH message. This txid must be taken from the signed transaction",
    ),
    "segwit": (bool, False, "Use segwit"),
    "confirmation_target": (
        int,
        config.ESTIMATE_FEE_CONF_TARGET,
        "The number of blocks to target for confirmation",
    ),
    "return_psbt": (
        bool,
        False,
        "Construct a PSBT instead of a raw transaction hex",
    ),
    "exclude_utxos": (
        str,
        "",
        "A comma-separated list of UTXO txids to exclude when selecting UTXOs to use as inputs for the transaction being created",
    ),
    "return_only_data": (
        bool,
        False,
        "Return only the data part of the transaction, not the full transaction",
    ),
    "no_validate": (
        bool,
        False,
        "Do not validate parameters",
    ),
}


def split_compose_params(**kwargs):
    transaction_args = {}
    common_args = {}
    private_key_wif = None
    for key, value in kwargs.items():
        if key in COMPOSE_COMMONS_ARGS:
            common_args[key] = value
        elif key == "privkey":
            private_key_wif = value
        else:
            transaction_args[key] = value
    return transaction_args, common_args, private_key_wif


def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def compose_transaction(
    db,
    name,
    params,
    encoding="auto",
    fee_per_kb=None,
    estimate_fee_per_kb=None,
    regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
    multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
    op_return_value=config.DEFAULT_OP_RETURN_VALUE,
    confirmation_target=config.ESTIMATE_FEE_CONF_TARGET,
    pubkey=None,
    allow_unconfirmed_inputs=False,
    fee=None,
    fee_provided=0,
    unspent_tx_hash=None,
    custom_inputs=None,
    dust_return_pubkey=None,
    disable_utxo_locks=False,
    extended_tx_info=False,
    p2sh_source_multisig_pubkeys=None,
    p2sh_source_multisig_pubkeys_required=None,
    p2sh_pretx_txid=None,
    old_style_api=True,
    segwit=False,
    api_v1=False,
    return_psbt=False,
    exclude_utxos="",
    return_only_data=False,
    compose_data=None,
    no_validate=False,
    data_signer=None,
    data_signature=None,
):
    """Create and return a transaction."""

    # Get provided pubkeys.
    if isinstance(pubkey, str):
        provided_pubkeys = [pubkey]
    elif isinstance(pubkey, list):
        provided_pubkeys = pubkey
    elif pubkey is None:
        provided_pubkeys = []
    else:
        raise exceptions.TransactionError("Invalid pubkey.")

    # Get additional pubkeys from `source` and `destination` params.
    # Convert `source` and `destination` to pubkeyhash form.
    for address_name in ["source", "destination"]:
        if address_name in params:
            address = params[address_name]
            if isinstance(address, list) or address is None or util.is_utxo_format(address):
                # pkhshs = []
                # for addr in address:
                #    provided_pubkeys += script.extract_pubkeys(addr)
                #    pkhshs.append(script.make_pubkeyhash(addr))
                # params[address_name] = pkhshs
                pass
            else:
                provided_pubkeys += script.extract_pubkeys(address)
                params[address_name] = script.make_pubkeyhash(address)

    # Check validity of collected pubkeys.
    for pubkey in provided_pubkeys:
        if not script.is_fully_valid(binascii.unhexlify(pubkey)):
            raise script.AddressError(f"invalid public key: {pubkey}")

    if compose_data is None:
        compose_method = sys.modules[f"counterpartycore.lib.messages.{name}"].compose
        compose_params = inspect.getfullargspec(compose_method)[0]
        missing_params = [p for p in compose_params if p not in params and p != "db"]
        if api_v1:
            for param in missing_params:
                params[param] = None
        else:
            if len(missing_params) > 0:
                default_values = get_default_args(compose_method)
                for param in missing_params:
                    if param in default_values:
                        params[param] = default_values[param]
                    else:
                        raise exceptions.ComposeError(
                            f"missing parameters: {', '.join(missing_params)}"
                        )

    # dont override fee_per_kb if specified
    if fee_per_kb is not None:
        estimate_fee_per_kb = False
    else:
        fee_per_kb = config.DEFAULT_FEE_PER_KB

    if "extended_tx_info" in params:
        extended_tx_info = params["extended_tx_info"]
        del params["extended_tx_info"]

    if "old_style_api" in params:
        old_style_api = params["old_style_api"]
        del params["old_style_api"]

    if "segwit" in params:
        segwit = params["segwit"]
        del params["segwit"]

    params["no_validate"] = no_validate

    if compose_data is None:
        tx_info = compose_method(db, **params)
        if util.enabled("new_tx_format"):
            # add flags and message length to the message
            if tx_info[2]:
                flags = util.gen_flags(signed=False, compressed=False)
                message_length = varint.encode(len(tx_info[2]))
                message = flags + message_length + tx_info[2]
                tx_info = (tx_info[0], tx_info[1], message)
    else:
        if util.enabled("new_tx_format") and data_signer and data_signature:
            source_length = varint.encode(len(data_signer))
            signature_length = varint.encode(len(data_signature))
            compose_data = (
                source_length + data_signer + signature_length + data_signature + compose_data
            )
        tx_info = compose_data

    if return_only_data:
        return tx_info

    raw_transaction = construct(
        db,
        tx_info,
        encoding=encoding,
        fee_per_kb=fee_per_kb,
        estimate_fee_per_kb=estimate_fee_per_kb,
        regular_dust_size=regular_dust_size,
        multisig_dust_size=multisig_dust_size,
        op_return_value=op_return_value,
        provided_pubkeys=provided_pubkeys,
        allow_unconfirmed_inputs=allow_unconfirmed_inputs,
        exact_fee=fee,
        fee_provided=fee_provided,
        unspent_tx_hash=unspent_tx_hash,
        custom_inputs=custom_inputs,
        dust_return_pubkey=dust_return_pubkey,
        disable_utxo_locks=disable_utxo_locks,
        extended_tx_info=extended_tx_info,
        p2sh_source_multisig_pubkeys=p2sh_source_multisig_pubkeys,
        p2sh_source_multisig_pubkeys_required=p2sh_source_multisig_pubkeys_required,
        p2sh_pretx_txid=p2sh_pretx_txid,
        old_style_api=old_style_api,
        segwit=segwit,
        estimate_fee_per_kb_nblocks=confirmation_target,
        exclude_utxos=exclude_utxos,
    )
    if return_psbt:
        psbt = backend.bitcoind.convert_to_psbt(raw_transaction)
        return psbt
    return raw_transaction


COMPOSABLE_TRANSACTIONS = [
    "bet",
    "broadcast",
    "btcpay",
    "burn",
    "cancel",
    "destroy",
    "dispenser",
    "dividend",
    "issuance",
    "mpma",
    "order",
    "send",
    "sweep",
    "fairminter",
    "fairmint",
    "attach",
    "detach",
]


def compose(db, source, transaction_name, api_v1=False, **kwargs):
    if transaction_name not in COMPOSABLE_TRANSACTIONS:
        raise exceptions.TransactionError("Transaction type not composable.")
    transaction_args, common_args, _ = split_compose_params(**kwargs)
    transaction_args["source"] = source
    return compose_transaction(
        db, name=transaction_name, params=transaction_args, api_v1=api_v1, **common_args
    )


def compose_bet(
    db,
    address: str,
    feed_address: str,
    bet_type: int,
    deadline: int,
    wager_quantity: int,
    counterwager_quantity: int,
    expiration: int,
    leverage: int = 5040,
    target_value: int = None,
    **construct_args,
):
    """
    Composes a transaction to issue a bet against a feed.
    :param address: The address that will make the bet (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param feed_address: The address that hosts the feed to be bet on (e.g. 1JDogZS6tQcSxwfxhv6XKKjcyicYA4Feev)
    :param bet_type: Bet 0 for Bullish CFD (deprecated), 1 for Bearish CFD (deprecated), 2 for Equal, 3 for NotEqual (e.g. 2)
    :param deadline: The time at which the bet should be decided/settled, in Unix time (seconds since epoch) (e.g. 3000000000)
    :param wager_quantity: The quantities of XCP to wager (in satoshis, hence integer) (e.g. 1000)
    :param counterwager_quantity: The minimum quantities of XCP to be wagered against, for the bets to match (in satoshis, hence integer) (e.g. 1000)
    :param expiration: The number of blocks after which the bet expires if it remains unmatched (e.g. 100)
    :param leverage: Leverage, as a fraction of 5040
    :param target_value: Target value for Equal/NotEqual bet (e.g. 1000)
    """
    params = {
        "source": address,
        "feed_address": feed_address,
        "bet_type": bet_type,
        "deadline": deadline,
        "wager_quantity": wager_quantity,
        "counterwager_quantity": counterwager_quantity,
        "target_value": target_value,
        "leverage": leverage,
        "expiration": expiration,
    }
    rawtransaction = compose_transaction(
        db,
        name="bet",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "bet",
    }


def compose_broadcast(
    db, address: str, timestamp: int, value: float, fee_fraction: float, text: str, **construct_args
):
    """
    Composes a transaction to broadcast textual and numerical information to the network.
    :param address: The address that will be sending (must have the necessary quantity of the specified asset) (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param timestamp: The timestamp of the broadcast, in Unix time (e.g. 4003903983)
    :param value: Numerical value of the broadcast (e.g. 100)
    :param fee_fraction: How much of every bet on this feed should go to its operator; a fraction of 1, (i.e. 0.05 is five percent) (e.g. 0.05)
    :param text: The textual part of the broadcast (e.g. "Hello, world!")
    """
    params = {
        "source": address,
        "timestamp": timestamp,
        "value": value,
        "fee_fraction": fee_fraction,
        "text": text,
    }
    rawtransaction = compose_transaction(
        db,
        name="broadcast",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "broadcast",
    }


def compose_btcpay(db, address: str, order_match_id: str, **construct_args):
    """
    Composes a transaction to pay for a BTC order match.
    :param address: The address that will be sending the payment (e.g. bc1qsteve3tfxfg9pcmvzw645sr9zy7es5rx645p6l)
    :param order_match_id: The ID of the order match to pay for (e.g. e470416a9500fb046835192da013f48e6468a07dba1bede4a0b68e666ed23c8d_4953bde3d9417b103615c2d3d4b284d4fcf7cbd820e5dd19ac0084e9ebd090b2)
    """
    params = {"source": address, "order_match_id": order_match_id}
    rawtransaction = compose_transaction(
        db,
        name="btcpay",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "btcpay",
    }


def compose_burn(db, address: str, quantity: int, overburn: bool = False, **construct_args):
    """
    Composes a transaction to burn a given quantity of BTC for XCP (on mainnet, possible between blocks 278310 and 283810; on testnet it is still available).
    :param address: The address with the BTC to burn (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param quantity: The quantities of BTC to burn (in satoshis, hence integer) (1 BTC maximum burn per address) (e.g. 1000)
    :param overburn: Whether to allow the burn to exceed 1 BTC for the address
    """
    params = {"source": address, "quantity": quantity, "overburn": overburn}
    rawtransaction = compose_transaction(
        db,
        name="burn",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "burn",
    }


def compose_cancel(db, address: str, offer_hash: str, **construct_args):
    """
    Composes a transaction to cancel an open order or bet.
    :param address: The address that placed the order/bet to be cancelled (e.g. 15e15ua6A3FJqjMevtrWcFSzKn9k6bMQeA)
    :param offer_hash: The hash of the order/bet to be cancelled (e.g. 8ce3335391bf71f8f12c0573b4f85b9adc4882a9955d9f8e5ababfdd0060279a)
    """
    params = {"source": address, "offer_hash": offer_hash}
    rawtransaction = compose_transaction(
        db,
        name="cancel",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "cancel",
    }


def compose_destroy(db, address: str, asset: str, quantity: int, tag: str, **construct_args):
    """
    Composes a transaction to destroy a quantity of an asset.
    :param address: The address that will be sending the asset to be destroyed (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param asset: The asset to be destroyed (e.g. XCP)
    :param quantity: The quantity of the asset to be destroyed (in satoshis, hence integer) (e.g. 1000)
    :param tag: A tag for the destruction (e.g. "bugs!")
    """
    params = {"source": address, "asset": asset, "quantity": quantity, "tag": tag}
    rawtransaction = compose_transaction(
        db,
        name="destroy",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "destroy",
    }


def compose_dispenser(
    db,
    address: str,
    asset: str,
    give_quantity: int,
    escrow_quantity: int,
    mainchainrate: int,
    status: int,
    open_address: str = None,
    oracle_address: str = None,
    **construct_args,
):
    """
    Opens or closes a dispenser for a given asset at a given rate of main chain asset (BTC). Escrowed quantity on open must be equal or greater than give_quantity. It is suggested that you escrow multiples of give_quantity to ease dispenser operation.
    :param address: The address that will be dispensing (must have the necessary escrow_quantity of the specified asset) (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param asset: The asset or subasset to dispense (e.g. XCP)
    :param give_quantity: The quantity of the asset to dispense (in satoshis, hence integer) (e.g. 1000)
    :param escrow_quantity: The quantity of the asset to reserve for this dispenser (in satoshis, hence integer) (e.g. 1000)
    :param mainchainrate: The quantity of the main chain asset (BTC) per dispensed portion (in satoshis, hence integer) (e.g. 100)
    :param status: The state of the dispenser. 0 for open, 1 for open using open_address, 10 for closed (e.g. 0)
    :param open_address: The address that you would like to open the dispenser on; MUST be equal to `address` from block 900000 onwards
    :param oracle_address: The address that you would like to use as a price oracle for this dispenser
    """
    params = {
        "source": address,
        "asset": asset,
        "give_quantity": give_quantity,
        "escrow_quantity": escrow_quantity,
        "mainchainrate": mainchainrate,
        "status": status,
        "open_address": open_address,
        "oracle_address": oracle_address,
    }
    rawtransaction = compose_transaction(
        db,
        name="dispenser",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "dispenser",
    }


def compose_dividend(
    db, address: str, quantity_per_unit: int, asset: str, dividend_asset: str, **construct_args
):
    """
    Composes a transaction to issue a dividend to holders of a given asset.
    :param address: The address that will be issuing the dividend (must have the ownership of the asset which the dividend is being issued on) (e.g. 1GQhaWqejcGJ4GhQar7SjcCfadxvf5DNBD)
    :param quantity_per_unit: The amount of dividend_asset rewarded (in satoshis, hence integer) (e.g. 1)
    :param asset: The asset or subasset that the dividends are being rewarded on (e.g. PEPECASH)
    :param dividend_asset: The asset or subasset that the dividends are paid in (e.g. XCP)
    """
    params = {
        "source": address,
        "quantity_per_unit": quantity_per_unit,
        "asset": asset,
        "dividend_asset": dividend_asset,
    }
    rawtransaction = compose_transaction(
        db,
        name="dividend",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "dividend",
    }


def compose_issuance(
    db,
    address: str,
    asset: str,
    quantity: int,
    transfer_destination: str = None,
    divisible: bool = True,
    lock: bool = False,
    reset: bool = False,
    description: str = None,
    **construct_args,
):
    """
    Composes a transaction to Issue a new asset, issue more of an existing asset, lock an asset, reset existing supply, or transfer the ownership of an asset.
    :param address: The address that will be issuing or transfering the asset (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param asset: The assets to issue or transfer. This can also be a subasset longname for new subasset issuances (e.g. XCPTEST)
    :param quantity: The quantity of the asset to issue (set to 0 if transferring an asset) (in satoshis, hence integer) (e.g. 1000)
    :param transfer_destination: The address to receive the asset (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param divisible: Whether this asset is divisible or not (if a transfer, this value must match the value specified when the asset was originally issued)
    :param lock: Whether this issuance should lock supply of this asset forever
    :param reset: Wether this issuance should reset any existing supply
    :param description: A textual description for the asset
    """
    params = {
        "source": address,
        "asset": asset,
        "quantity": quantity,
        "transfer_destination": transfer_destination,
        "divisible": divisible,
        "lock": lock,
        "reset": reset,
        "description": description,
    }
    rawtransaction = compose_transaction(
        db,
        name="issuance",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "issuance",
    }


def compose_mpma(
    db,
    address: str,
    assets: str,
    destinations: str,
    quantities: str,
    memo: str,
    memo_is_hex: bool,
    **construct_args,
):
    """
    Composes a transaction to send multiple payments to multiple addresses.
    :param address: The address that will be sending (must have the necessary quantity of the specified asset) (e.g. 1Fv87qmdtjQDP9d4p9E5ncBQvYB4a3Rhy6)
    :param assets: comma-separated list of assets to send (e.g. BAABAABLKSHP,BADHAIRDAY,BADWOJAK)
    :param destinations: comma-separated list of addresses to send to (e.g. 1JDogZS6tQcSxwfxhv6XKKjcyicYA4Feev,1GQhaWqejcGJ4GhQar7SjcCfadxvf5DNBD,1C3uGcoSGzKVgFqyZ3kM2DBq9CYttTMAVs)
    :param quantities: comma-separated list of quantities to send (in satoshis, hence integer) (e.g. 1,2,3)
    :param memo: The Memo associated with this transaction (e.g. "Hello, world!")
    :param memo_is_hex: Whether the memo field is a hexadecimal string (e.g. False)
    """
    asset_list = assets.split(",")
    destination_list = destinations.split(",")
    quantity_list = quantities.split(",")
    if len(asset_list) != len(destination_list) or len(asset_list) != len(quantity_list):
        raise exceptions.ComposeError(
            "The number of assets, destinations, and quantities must be equal"
        )
    for quantity in quantity_list:
        if not quantity.isdigit():
            raise exceptions.ComposeError("Quantity must be an integer")
    quantity_list = [int(quantity) for quantity in quantity_list]
    asset_dest_quant_list = list(zip(asset_list, destination_list, quantity_list))

    params = {
        "source": address,
        "asset_dest_quant_list": asset_dest_quant_list,
        "memo": memo,
        "memo_is_hex": memo_is_hex,
    }

    rawtransaction = compose_transaction(
        db,
        name="versions.mpma",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "mpma",
    }


def compose_order(
    db,
    address: str,
    give_asset: str,
    give_quantity: int,
    get_asset: str,
    get_quantity: int,
    expiration: int,
    fee_required: int,
    **construct_args,
):
    """
    Composes a transaction to place an order on the distributed exchange.
    :param address: The address that will be issuing the order request (must have the necessary quantity of the specified asset to give) (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param give_asset: The asset that will be given in the trade (e.g. XCP)
    :param give_quantity: The quantity of the asset that will be given (in satoshis, hence integer) (e.g. 1000)
    :param get_asset: The asset that will be received in the trade (e.g. PEPECASH)
    :param get_quantity: The quantity of the asset that will be received (in satoshis, hence integer) (e.g. 1000)
    :param expiration: The number of blocks for which the order should be valid (e.g. 100)
    :param fee_required: The miners’ fee required to be paid by orders for them to match this one; in BTC; required only if buying BTC (may be zero, though) (e.g. 100)
    """
    params = {
        "source": address,
        "give_asset": give_asset,
        "give_quantity": give_quantity,
        "get_asset": get_asset,
        "get_quantity": get_quantity,
        "expiration": expiration,
        "fee_required": fee_required,
    }
    rawtransaction = compose_transaction(
        db,
        name="order",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "order",
    }


def compose_send(
    db,
    address: str,
    destination: str,
    asset: str,
    quantity: int,
    memo: str = None,
    memo_is_hex: bool = False,
    use_enhanced_send: bool = True,
    **construct_args,
):
    """
    Composes a transaction to send a quantity of an asset to another address.
    :param address: The address that will be sending (must have the necessary quantity of the specified asset) (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param destination: The address that will be receiving the asset (e.g. 1JDogZS6tQcSxwfxhv6XKKjcyicYA4Feev)
    :param asset: The asset or subasset to send (e.g. XCP)
    :param quantity: The quantity of the asset to send (in satoshis, hence integer) (e.g. 1000)
    :param memo: The Memo associated with this transaction
    :param memo_is_hex: Whether the memo field is a hexadecimal string
    :param use_enhanced_send: If this is false, the construct a legacy transaction sending bitcoin dust
    """
    params = {
        "source": address,
        "destination": destination,
        "asset": asset,
        "quantity": quantity,
        "memo": memo,
        "memo_is_hex": memo_is_hex,
        "use_enhanced_send": use_enhanced_send,
    }
    rawtransaction = compose_transaction(
        db,
        name="send",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "send",
    }


def compose_dispense(
    db,
    address: str,
    dispenser: str,
    quantity: int,
    **construct_args,
):
    """
    Composes a transaction to send BTC to a dispenser.
    :param address: The address that will be sending (must have the necessary quantity of BTC) (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param dispenser: The dispenser that will be receiving the asset (e.g. 17SDWBrEVyJ2nisHDmozgw35R9Bgu8ewqo)
    :param quantity: The quantity of BTC to send (in satoshis, hence integer) (e.g. 1000)
    """
    params = {
        "source": address,
        "destination": dispenser,
        "quantity": quantity,
    }
    rawtransaction = compose_transaction(
        db,
        name="dispense",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "dispense",
    }


def compose_sweep(db, address: str, destination: str, flags: int, memo: str, **construct_args):
    """
    Composes a transaction to Sends all assets and/or transfer ownerships to a destination address.
    :param address: The address that will be sending (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param destination: The address to receive the assets and/or ownerships (e.g. 1JDogZS6tQcSxwfxhv6XKKjcyicYA4Feev)
    :param flags: An OR mask of flags indicating how the sweep should be processed. Possible flags are:
                    - FLAG_BALANCES: (integer) 1, specifies that all balances should be transferred.
                    - FLAG_OWNERSHIP: (integer) 2, specifies that all ownerships should be transferred.
                    - FLAG_BINARY_MEMO: (integer) 4, specifies that the memo is in binary/hex form.
                    (e.g. 7)
    :param memo: The Memo associated with this transaction in hex format (e.g. FFFF)
    """
    params = {
        "source": address,
        "destination": destination,
        "flags": flags,
        "memo": memo,
    }
    rawtransaction = compose_transaction(
        db,
        name="sweep",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "sweep",
    }


def compose_fairminter(
    db,
    address: str,
    asset: str,
    asset_parent: str = "",
    price: int = 0,
    max_mint_per_tx: int = 0,
    hard_cap: int = 0,
    premint_quantity: int = 0,
    start_block: int = 0,
    end_block: int = 0,
    soft_cap: int = 0,
    soft_cap_deadline_block: int = 0,
    minted_asset_commission: float = 0.0,
    burn_payment: bool = False,
    lock_description: bool = False,
    lock_quantity: bool = False,
    divisible: bool = True,
    description: str = "",
    **construct_args,
):
    """
    Composes a transaction to issue a new asset using the FairMinter protocol.
    :param address: The address that will be issuing the asset (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param asset: The asset to issue (e.g. MYASSET)
    :param asset_parent: The parent asset of the asset to issue
    :param price: The price in XCP of the asset to issue
    :param max_mint_per_tx: Amount minted if price is equal to 0; otherwise, maximum amount of asset that can be minted in a single transaction; if 0, there is no limit
    :param hard_cap: The maximum amount of asset that can be minted; if 0 there is no limit
    :param premint_quantity: Amount of asset to be minted when the sale starts, if 0, no premint; preminted assets are sent to the source of the transaction
    :param start_block: The block at which the sale starts
    :param end_block: The block at which the sale ends
    :param soft_cap: Minimum amount of asset to be minted, if None, no minimum; if the soft cap is not reached by the soft_cap_deadline_block, the sale is canceled, asset is revoked from all minters and all payments are refunded
    :param soft_cap_deadline_block: The block at which the soft cap must be reached
    :param minted_asset_commission: Commission to be paid in minted asset, a fraction of 1 (i.e., 0.05 is five percent); the commission is deducted from the asset received by the minter and sent to the Fair Minter owner
    :param burn_payment: If True, the payment asset is burned, otherwise it is sent to the source
    :param lock_description: If True, the description of the asset is locked
    :param lock_quantity: If True, the quantity of the asset cannot be changed after the minting
    :param divisible: If True, the asset is divisible
    :param description: The description of the asset
    """
    params = {
        "source": address,
        "asset": asset,
        "asset_parent": asset_parent,
        "price": price,
        "max_mint_per_tx": max_mint_per_tx,
        "hard_cap": hard_cap,
        "premint_quantity": premint_quantity,
        "start_block": start_block,
        "end_block": end_block,
        "soft_cap": soft_cap,
        "soft_cap_deadline_block": soft_cap_deadline_block,
        "minted_asset_commission": minted_asset_commission,
        "burn_payment": burn_payment,
        "lock_description": lock_description,
        "lock_quantity": lock_quantity,
        "divisible": divisible,
        "description": description,
    }
    rawtransaction = compose_transaction(
        db,
        name="fairminter",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "fairminter",
    }


def compose_fairmint(db, address: str, asset: str, quantity: int = 0, **construct_args):
    """
    Composes a transaction to mint a quantity of an asset using the FairMinter protocol.
    :param address: The address that will be minting the asset (e.g. 1CounterpartyXXXXXXXXXXXXXXXUWLpVr)
    :param asset: The asset to mint (e.g. MYASSET)
    :param quantity: The quantity of the asset to mint (in satoshis, hence integer) (e.g. 1000)
    """
    params = {"source": address, "asset": asset, "quantity": quantity}
    rawtransaction = compose_transaction(
        db,
        name="fairmint",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "fairmint",
    }


def compose_utxo(
    db,
    source: str,
    destination: str,
    asset: str,
    quantity: int,
    **construct_args,
):
    params = {
        "source": source,
        "destination": destination,
        "asset": asset,
        "quantity": quantity,
    }
    rawtransaction = compose_transaction(
        db,
        name="utxo",
        params=params,
        **construct_args,
    )
    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": params,
        "name": "utxo",
    }


def compose_attach(
    db,
    address: str,
    asset: str,
    quantity: int,
    destination: str = None,
    **construct_args,
):
    """
    Attach assets from an address to UTXO.
    :param address: The address from which the assets are attached
    :param destination: The utxo to attach the assets to
    :param asset: The asset or subasset to attach (e.g. XCP)
    :param quantity: The quantity of the asset to attach (in satoshis, hence integer) (e.g. 1000)
    """
    return compose_utxo(
        db,
        source=address,
        destination=destination,
        asset=asset,
        quantity=quantity,
        **construct_args,
    )


def compose_detach(
    db,
    utxo: str,
    destination: str,
    asset: str,
    quantity: int,
    **construct_args,
):
    """
    Detach assets from UTXO to an address.
    :param utxo: The utxo from which the assets are detached
    :param destination: The address to detach the assets to
    :param asset: The asset or subasset to detach (e.g. XCP)
    :param quantity: The quantity of the asset to detach (in satoshis, hence integer) (e.g. 1000)
    """
    return compose_utxo(
        db,
        source=utxo,
        destination=destination,
        asset=asset,
        quantity=quantity,
        **construct_args,
    )


def compose_movetoutxo(db, utxo: str, destination: str, more_utxos: str = ""):
    """
    Move assets from UTXO to another UTXO.
    :param utxo: The utxo from which the assets are moved
    :param destination: The address to move the assets to
    :param more_utxos: The additional utxos to fund the transaction
    """
    decimal.getcontext().prec = 8

    more_utxos_list = []
    input_count = 1
    total_value = D("0")
    try:
        source_address, source_value = backend.bitcoind.get_utxo_address_and_value(utxo)
        total_value += D(source_value)
        for more_utxo in more_utxos.split(","):
            if more_utxo == "":
                continue
            _more_utxo_address, more_utxo_value = backend.bitcoind.get_utxo_address_and_value(
                more_utxo
            )
            more_utxo_tx_hash, more_utxo_vout = more_utxo.split(":")
            more_utxos_list.append({"txid": more_utxo_tx_hash, "vout": int(more_utxo_vout)})
            input_count += 1
            total_value += D(more_utxo_value)
    except exceptions.InvalidUTXOError as e:
        raise exceptions.ComposeError("Invalid UTXO for source") from e

    try:
        script.validate(destination)
    except Exception as e:
        raise exceptions.ComposeError("Invalid address for destination") from e

    tx_hash, vout = utxo.split(":")

    fee_per_kb = backend.bitcoind.fee_per_kb()
    # Transaction Size (in bytes) = (Number of Inputs x 148) + (Number of Outputs x 34) + 10
    tx_size = (input_count * 148) + (2 * 34) + 10
    fee = (D(fee_per_kb) / config.UNIT) * (D(tx_size) / 1024)

    dust = D("0.0000546")
    change = D(total_value) - dust - fee

    if change < 0:
        raise exceptions.ComposeError("Insufficient funds for fee")

    inputs = [{"txid": tx_hash, "vout": int(vout)}] + more_utxos_list
    outputs = [{destination: str(dust)}, {source_address: str(change)}]
    rawtransaction = backend.bitcoind.createrawtransaction(inputs, outputs)

    return {
        "rawtransaction": rawtransaction,
        "params": {
            "source": utxo,
            "destination": destination,
        },
        "name": "movetoutxo",
    }


def compose_multiple(db, json_txs: str):
    try:
        txs = json.loads(json_txs)
    except json.JSONDecodeError as e:
        raise exceptions.ComposeError("Invalid JSON") from e
    if not isinstance(txs, dict) or "transactions" not in txs:
        raise exceptions.ComposeError("Invalid JSON: must contain a 'transactions' key")

    tx_info = []
    source = None
    destination = []
    data = b""
    for tx in txs["transactions"]:
        if "name" not in tx or "params" not in tx:
            raise exceptions.ComposeError(
                "Invalid JSON: each transaction must have a 'name' and 'params' key"
            )
        if tx["name"] not in COMPOSABLE_TRANSACTIONS:
            raise exceptions.ComposeError(
                f"Invalid JSON: '{tx['name']}' is not a valid transaction"
            )
        if not isinstance(tx["params"], dict):
            raise exceptions.ComposeError("Invalid JSON: 'params' must be a dictionary")

        construct_args = txs.get("construct_args", {})

        tx_name = tx["name"]
        tx_params = tx["params"]
        tx_params["return_only_data"] = True
        this_module = sys.modules[__name__]
        func = getattr(this_module, f"compose_{tx_name}")
        tx_info = func(db, **tx_params, **construct_args)

        if source is None:
            source = tx_info[0]
        elif source != tx_info[0]:
            raise exceptions.ComposeError("All transactions must have the same source")

        if not len(destination) and len(tx_info[1]):
            destination = tx_info[1]
        elif len(tx_info[1]) and len(destination) and destination != tx_info[1]:
            raise exceptions.ComposeError("All transactions must have the same destination")

        data += tx_info[2][1:]  # skip the first flags byte

    # add first flags byte
    data = util.gen_flags(signed=False, compressed=False) + data

    compose_data = (source, destination, data)

    # print("COMPOSE DATA", compose_data)

    construct_args["compose_data"] = compose_data

    rawtransaction = compose_transaction(
        db,
        name="",
        params={},
        **construct_args,
    )

    if "return_only_data" in construct_args and construct_args["return_only_data"]:
        return rawtransaction
    return {
        "rawtransaction": rawtransaction,
        "params": txs,
        "name": "utxo",
    }


def compose_presigned(
    db, address: str, inputs: str, data: str, signature: str, destination: str, btc_amount: int
):
    """
    Composes a transaction from presigned inputs.
    :param address: The signer of the data
    :param inputs: The inputs to the transaction, first input is used to determine the source address
    :param data: The data to include in the transaction
    :param signature: The signature of the data
    :param destination: The destination of the transaction
    :param btc_amount: The amount of BTC to send
    """
    custom_inputs = []
    for input in inputs.split(","):
        tx_hash, vout = input.split(":")
        custom_inputs.append({"txid": tx_hash, "vout": int(vout)})

    first_input_address = backend.bitcoind.safe_get_utxo_address(inputs[0])
    if first_input_address is None:
        raise exceptions.ComposeError(f"Invalid UTXO: {inputs[0]}")

    rawtransaction = compose_transaction(
        db,
        name="",
        params={},
        custom_inputs=custom_inputs,
        compose_data=(first_input_address, destination, data),
        data_signature=signature,
        data_signer=address,
    )

    return {
        "rawtransaction": rawtransaction,
        "params": {
            "inputs": inputs,
            "data": data,
            "address": address,
            "signature": signature,
            "destination": destination,
            "btc_amount": btc_amount,
        },
        "name": "presigned",
    }


def info(db, rawtransaction: str, block_index: int = None):
    """
    Returns Counterparty information from a raw transaction in hex format.
    :param rawtransaction: Raw transaction in hex format (e.g. 01000000017828697743c03aef6a3a8ba54b22bf579ffcab8161faf20e7b20c4ecd75cc986010000006b483045022100d1bd0531bb1ed2dd2cbf77d6933273e792a3dbfa84327d419169850ddd5976f502205d1ab0f7bcbf1a0cc183f0520c9aa8f711d41cb790c0c4ac39da6da4a093d798012103d3b1f711e907acb556e239f6cafb6a4f7fe40d8dd809b0e06e739c2afd73f202ffffffff0200000000000000004d6a4bf29880b93b0711524c7ef9c76835752088db8bd4113a3daf41fc45ffdc8867ebdbf26817fae377696f36790e52f51005806e9399a427172fedf348cf798ed86e548002ee96909eef0775ec3c2b0100000000001976a91443434cf159cc585fbd74daa9c4b833235b19761b88ac00000000)
    :param block_index: Block index mandatory for transactions before block 335000
    """
    decoded_tx = deserialize.deserialize_tx(
        rawtransaction, use_txid=util.enabled("correct_segwit_txids", block_index)
    )
    source, destination, btc_amount, fee, data, _extra = gettxinfo.get_tx_info(
        db,
        decoded_tx,
        block_index=block_index,
    )
    del decoded_tx["__data__"]
    result = {
        "source": source,
        "destination": destination if destination else None,
        "btc_amount": btc_amount,
        "fee": fee,
        "data": util.hexlify(data) if data else "",
        "decoded_tx": decoded_tx,
    }
    if data:
        result["data"] = util.hexlify(data)
        result["unpacked_data"] = unpack(db, result["data"], block_index)
    return result


def unpack(db, datahex: str, block_index: int = None):
    """
    Unpacks Counterparty data in hex format and returns the message type and data.
    :param datahex: Data in hex format (e.g. 16010b9142801429a60000000000000001000000554e4e45474f544941424c45205745204d555354204245434f4d4520554e4e45474f544941424c4520574520415245)
    :param block_index: Block index of the transaction containing this data
    """
    data = binascii.unhexlify(datahex)
    message_type_id, message = message_type.unpack(data)[0]
    block_index = block_index or util.CURRENT_BLOCK_INDEX

    issuance_ids = [
        messages.issuance.ID,
        messages.issuance.LR_ISSUANCE_ID,
        messages.issuance.SUBASSET_ID,
        messages.issuance.LR_SUBASSET_ID,
    ]

    # Unknown message type
    message_data = {"error": "Unknown message type"}
    message_type_name = "unknown"
    try:
        # Bet
        if message_type_id == messages.bet.ID:
            message_type_name = "bet"
            message_data = messages.bet.unpack(message, return_dict=True)
        # Broadcast
        elif message_type_id == messages.broadcast.ID:
            message_type_name = "broadcast"
            message_data = messages.broadcast.unpack(message, block_index, return_dict=True)
        # BTCPay
        elif message_type_id == messages.btcpay.ID:
            message_type_name = "btcpay"
            message_data = messages.btcpay.unpack(message, return_dict=True)
        # Cancel
        elif message_type_id == messages.cancel.ID:
            message_type_name = "cancel"
            message_data = messages.cancel.unpack(message, return_dict=True)
        # Destroy
        elif message_type_id == messages.destroy.ID:
            message_type_name = "destroy"
            message_data = messages.destroy.unpack(db, message, return_dict=True)
        # Dispenser
        elif message_type_id == messages.dispenser.ID:
            message_type_name = "dispenser"
            message_data = messages.dispenser.unpack(message, return_dict=True)
        elif message_type_id == messages.dispenser.DISPENSE_ID:
            message_type_name = "dispense"
            message_data = messages.dispense.unpack(message, return_dict=True)
        # Dividend
        elif message_type_id == messages.dividend.ID:
            message_type_name = "dividend"
            message_data = messages.dividend.unpack(db, message, block_index, return_dict=True)
        # Issuance
        elif message_type_id in issuance_ids:
            message_type_name = "issuance"
            message_data = messages.issuance.unpack(
                db, message, message_type_id, block_index, return_dict=True
            )
        # Order
        elif message_type_id == messages.order.ID:
            message_type_name = "order"
            message_data = messages.order.unpack(db, message, block_index, return_dict=True)
        # Send
        elif message_type_id == messages.send.ID:
            message_type_name = "send"
            message_data = messages.send.unpack(db, message, block_index)
        # Enhanced send
        elif message_type_id == messages.versions.enhanced_send.ID:
            message_type_name = "enhanced_send"
            message_data = messages.versions.enhanced_send.unpack(message, block_index)
        # MPMA send
        elif message_type_id == messages.versions.mpma.ID:
            message_type_name = "mpma_send"
            mpma_message_data = messages.versions.mpma.unpack(message, block_index)
            message_data = []
            for asset_name, send_info in mpma_message_data.items():
                message_data.append(
                    {
                        "asset": asset_name,
                        "destination": send_info[0][0],
                        "quantity": send_info[0][1],
                        "memo": send_info[0][2] if len(send_info[0]) > 2 else None,
                        "memo_is_hex": send_info[0][3] if len(send_info[0]) > 3 else None,
                    }
                )
        # RPS
        elif message_type_id == messages.rps.ID:
            message_type_name = "rps"
            message_data = messages.rps.unpack(message, return_dict=True)
        # RPS Resolve
        elif message_type_id == messages.rpsresolve.ID:
            message_type_name = "rpsresolve"
            message_data = messages.rpsresolve.unpack(message, return_dict=True)
        # Sweep
        elif message_type_id == messages.sweep.ID:
            message_type_name = "sweep"
            message_data = messages.sweep.unpack(message)
        # Fair Minter
        elif message_type_id == messages.fairminter.ID:
            message_type_name = "fairminter"
            message_data = messages.fairminter.unpack(message)
        # Fair Mint
        elif message_type_id == messages.fairmint.ID:
            message_type_name = "fairmint"
            message_data = messages.fairmint.unpack(message)
    except (exceptions.UnpackError, UnicodeDecodeError) as e:
        message_data = {"error": str(e)}

    return {
        "message_type": message_type_name,
        "message_type_id": message_type_id,
        "message_data": message_data,
    }
