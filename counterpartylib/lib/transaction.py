"""
Construct and serialize the Bitcoin transactions that are Counterparty transactions.

This module contains no consensus‐critical code.
"""

import os
import sys
import binascii
import json
import hashlib
import re
import time
import decimal
import logging
logger = logging.getLogger(__name__)
import requests
from bitcoin.core.script import CScript
from bitcoin.core import x
from bitcoin.core import b2lx
import cachetools

from counterpartylib.lib import config
from counterpartylib.lib import exceptions
from counterpartylib.lib import util
from counterpartylib.lib import script
from counterpartylib.lib import backend
from counterpartylib.lib import arc4
from counterpartylib.lib.transaction_helper import serializer

# Constants
OP_RETURN = b'\x6a'
OP_PUSHDATA1 = b'\x4c'
OP_DUP = b'\x76'
OP_HASH160 = b'\xa9'
OP_EQUALVERIFY = b'\x88'
OP_CHECKSIG = b'\xac'
OP_1 = b'\x51'
OP_2 = b'\x52'
OP_3 = b'\x53'
OP_CHECKMULTISIG = b'\xae'
OP_EQUAL = b'\x87'

D = decimal.Decimal
UTXO_LOCKS = None
UTXO_LOCKS_PER_ADDRESS_MAXSIZE = 5000  # set higher than the max number of UTXOs we should expect to
                                       # manage in an aging cache for any one source address, at any one period


def print_coin(coin):
    return 'amount: {:.8f}; txid: {}; vout: {}; confirmations: {}'.format(coin['amount'], coin['txid'], coin['vout'], coin.get('confirmations', '?')) # simplify and make deterministic


def chunks(l, n):
    """ Yield successive n‐sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]


def make_outkey(output):
    return '{}{}'.format(output['txid'], output['vout'])


def get_dust_return_pubkey(source, provided_pubkeys, encoding):
    """Return the pubkey to which dust from data outputs will be sent.

    This pubkey is used in multi-sig data outputs (as the only real pubkey) to
    make those the outputs spendable. It is derived from the source address, so
    that the dust is spendable by the creator of the transaction.
    """
    # Get hex dust return pubkey.
    if script.is_multisig(source):
        a, self_pubkeys, b = script.extract_array(backend.multisig_pubkeyhashes_to_pubkeys(source, provided_pubkeys))
        dust_return_pubkey_hex = self_pubkeys[0]
    else:
        dust_return_pubkey_hex = backend.pubkeyhash_to_pubkey(source, provided_pubkeys)

    # Convert hex public key into the (binary) dust return pubkey.
    try:
        dust_return_pubkey = binascii.unhexlify(dust_return_pubkey_hex)
    except binascii.Error:
        raise script.InputError('Invalid private key.')

    return dust_return_pubkey


def construct (db, tx_info, encoding='auto',
               fee_per_kb=config.DEFAULT_FEE_PER_KB,
               estimate_fee_per_kb=None, estimate_fee_per_kb_nblocks=config.ESTIMATE_FEE_NBLOCKS,
               regular_dust_size=config.DEFAULT_REGULAR_DUST_SIZE,
               multisig_dust_size=config.DEFAULT_MULTISIG_DUST_SIZE,
               op_return_value=config.DEFAULT_OP_RETURN_VALUE,
               exact_fee=None, fee_provided=0, provided_pubkeys=None, dust_return_pubkey=None,
               allow_unconfirmed_inputs=False, unspent_tx_hash=None, custom_inputs=None, disable_utxo_locks=False, extended_tx_info=False):

    if estimate_fee_per_kb is None:
        estimate_fee_per_kb = config.ESTIMATE_FEE_PER_KB

    global UTXO_LOCKS

    desired_encoding = encoding
    (source, destination_outputs, data) = tx_info

    if dust_return_pubkey:
        dust_return_pubkey = binascii.unhexlify(dust_return_pubkey)

    # Source.
        # If public key is necessary for construction of (unsigned)
        # transaction, use the public key provided, or find it from the
        # blockchain.
    if source:
        script.validate(source)

    source_is_p2sh = script.is_p2sh(source)

    # Sanity checks.
    if exact_fee and not isinstance(exact_fee, int):
        raise exceptions.TransactionError('Exact fees must be in satoshis.')
    if not isinstance(fee_provided, int):
        raise exceptions.TransactionError('Fee provided must be in satoshis.')

    if UTXO_LOCKS is None and config.UTXO_LOCKS_MAX_ADDRESSES > 0:  # initialize if configured
        UTXO_LOCKS = util.DictCache(size=config.UTXO_LOCKS_MAX_ADDRESSES)

    '''Destinations'''

    # Destination outputs.
        # Replace multi‐sig addresses with multi‐sig pubkeys. Check that the
        # destination output isn’t a dust output. Set null values to dust size.
    destination_outputs_new = []
    for (address, value) in destination_outputs:

        # Value.
        if script.is_multisig(address):
            dust_size = multisig_dust_size
        else:
            dust_size = regular_dust_size
        if value == None:
            value = dust_size
        elif value < dust_size:
            raise exceptions.TransactionError('Destination output is dust.')

        # Address.
        script.validate(address)
        if script.is_multisig(address):
            destination_outputs_new.append((backend.multisig_pubkeyhashes_to_pubkeys(address, provided_pubkeys), value))
        else:
            destination_outputs_new.append((address, value))

    destination_outputs = destination_outputs_new
    destination_btc_out = sum([value for address, value in destination_outputs])


    '''Data'''

    if data:
        # Data encoding methods (choose and validate).
        if encoding == 'auto':
            if len(data) + len(config.PREFIX) <= config.OP_RETURN_MAX_SIZE:
                encoding = 'opreturn'
            else:
                encoding = 'multisig'

        elif encoding not in ('pubkeyhash', 'multisig', 'opreturn'):
            raise exceptions.TransactionError('Unknown encoding‐scheme.')


        if encoding == 'multisig':
            # dust_return_pubkey should be set or explicitly set to False to use the default configured for the node
            #  the default for the node is optional so could fail
            if (source_is_p2sh and dust_return_pubkey is None) or (dust_return_pubkey is False and config.P2SH_DUST_RETURN_PUBKEY is None):
                raise exceptions.TransactionError("Can't use multisig encoding when source is P2SH and no dust_return_pubkey is provided.")
            elif dust_return_pubkey is False:
                dust_return_pubkey = binascii.unhexlify(config.P2SH_DUST_RETURN_PUBKEY)

        # Divide data into chunks.
        if encoding == 'pubkeyhash':
            # Prefix is also a suffix here.
            chunk_size = 20 - 1 - 8
        elif encoding == 'multisig':
            # Two pubkeys, minus length byte, minus prefix, minus two nonces,
            # minus two sign bytes.
            chunk_size = (33 * 2) - 1 - 8 - 2 - 2
        elif encoding == 'opreturn':
            chunk_size = config.OP_RETURN_MAX_SIZE
            if len(data) + len(config.PREFIX) > chunk_size:
                raise exceptions.TransactionError('One `OP_RETURN` output per transaction.')
        data_array = list(chunks(data, chunk_size))

        # Data outputs.
        if encoding == 'multisig':
            data_value = multisig_dust_size
        elif encoding == 'opreturn':
            data_value = op_return_value
        else:
            # Pay‐to‐PubKeyHash, e.g.
            data_value = regular_dust_size
        data_output = (data_array, data_value)

        if not dust_return_pubkey:
            if encoding == 'multisig':
                dust_return_pubkey = get_dust_return_pubkey(source, provided_pubkeys, encoding)
            else:
                dust_return_pubkey = None
    else:
        data_array = []
        data_output = None
        dust_return_pubkey = None

    data_btc_out = sum([data_value for data_chunk in data_array])

    '''Inputs'''

    # Calculate collective size of outputs, for fee calculation.
    p2pkhsize = 25 + 9
    if encoding == 'multisig':
        data_output_size = 81       # 71 for the data
    elif encoding == 'opreturn':
        # prefix + data + 10 bytes script overhead
        data_output_size = len(config.PREFIX) + 10
        if data is not None:
            data_output_size = data_output_size + len(data)
    else:
        data_output_size = p2pkhsize   # Pay‐to‐PubKeyHash (25 for the data?)
    outputs_size = (p2pkhsize * len(destination_outputs)) + (len(data_array) * data_output_size)

    # Array of UTXOs, as retrieved by listunspent function from bitcoind
    if custom_inputs:
        use_inputs = unspent = custom_inputs
    else:
        if unspent_tx_hash is not None:
            unspent = backend.get_unspent_txouts(source, unconfirmed=allow_unconfirmed_inputs, unspent_tx_hash=unspent_tx_hash)
        else:
            unspent = backend.get_unspent_txouts(source, unconfirmed=allow_unconfirmed_inputs)

        # filter out any locked UTXOs to prevent creating transactions that spend the same UTXO when they're created at the same time
        if UTXO_LOCKS is not None and source in UTXO_LOCKS:
            unspentkeys = set(make_outkey(output) for output in unspent)
            filtered_unspentkeys = unspentkeys - set(UTXO_LOCKS[source].keys())
            unspent = [output for output in unspent if make_outkey(output) in filtered_unspentkeys]

        unspent = backend.sort_unspent_txouts(unspent)
        logger.debug('Sorted candidate UTXOs: {}'.format([print_coin(coin) for coin in unspent]))
        use_inputs = unspent

    # use backend estimated fee_per_kb
    if estimate_fee_per_kb:
        estimated_fee_per_kb = backend.fee_per_kb(estimate_fee_per_kb_nblocks)
        if estimated_fee_per_kb is not None:
            fee_per_kb = max(estimated_fee_per_kb, fee_per_kb)  # never drop below the default fee_per_kb

    logger.debug('Fee/KB {:.8f}'.format(fee_per_kb / config.UNIT))

    inputs = []
    btc_in = 0
    change_quantity = 0
    sufficient_funds = False
    final_fee = fee_per_kb
    desired_input_count = 1

    if encoding == 'multisig' and data_array and util.enabled('bytespersigop'):
        desired_input_count = len(data_array) * 2

    for coin in use_inputs:
        logger.debug('New input: {}'.format(print_coin(coin)))
        inputs.append(coin)
        btc_in += round(coin['amount'] * config.UNIT)

        size = 181 * len(inputs) + outputs_size + 10
        necessary_fee = int(size / 1000 * fee_per_kb)

        # If exact fee is specified, use that. Otherwise, calculate size of tx
        # and base fee on that (plus provide a minimum fee for selling BTC).
        if exact_fee:
            final_fee = exact_fee
        else:
            final_fee = max(fee_provided, necessary_fee)

        # Check if good.
        btc_out = destination_btc_out + data_btc_out
        change_quantity = btc_in - (btc_out + final_fee)
        logger.debug('Size: {} Fee: {:.8f} Change quantity: {:.8f} BTC'.format(size, final_fee / config.UNIT, change_quantity / config.UNIT))
        # If change is necessary, must not be a dust output.
        if change_quantity == 0 or change_quantity >= regular_dust_size:
            sufficient_funds = True
            if len(inputs) >= desired_input_count:
                break

    if not sufficient_funds:
        # Approximate needed change, fee by with most recently calculated
        # quantities.
        btc_out = destination_btc_out + data_btc_out
        total_btc_out = btc_out + max(change_quantity, 0) + final_fee
        raise exceptions.BalanceError('Insufficient {} at address {}. (Need approximately {} {}.) To spend unconfirmed coins, use the flag `--unconfirmed`. (Unconfirmed coins cannot be spent from multi‐sig addresses.)'.format(config.BTC, source, total_btc_out / config.UNIT, config.BTC))

    # Lock the source's inputs (UTXOs) chosen for this transaction
    if UTXO_LOCKS is not None and not disable_utxo_locks:
        if source not in UTXO_LOCKS:
            UTXO_LOCKS[source] = cachetools.TTLCache(
                UTXO_LOCKS_PER_ADDRESS_MAXSIZE, config.UTXO_LOCKS_MAX_AGE)

        for input in inputs:
            UTXO_LOCKS[source][make_outkey(input)] = input

        logger.debug("UTXO locks: Potentials ({}): {}, Used: {}, locked UTXOs: {}".format(
            len(unspent), [make_outkey(coin) for coin in unspent],
            [make_outkey(input) for input in inputs], list(UTXO_LOCKS[source].keys())))

    '''Finish'''

    # Change output.
    if change_quantity:
        if script.is_multisig(source):
            change_address = backend.multisig_pubkeyhashes_to_pubkeys(source, provided_pubkeys)
        else:
            change_address = source
        change_output = (change_address, change_quantity)
    else:
        change_output = None

    # Serialise inputs and outputs.
    unsigned_tx = serializer.serialise(encoding, inputs, destination_outputs,
                            data_output, change_output,
                            dust_return_pubkey=dust_return_pubkey)
    unsigned_tx_hex = binascii.hexlify(unsigned_tx).decode('utf-8')


    '''Sanity Check'''

    from counterpartylib.lib import blocks

    # Desired transaction info.
    (desired_source, desired_destination_outputs, desired_data) = tx_info
    desired_source = script.make_canonical(desired_source)
    desired_destination = script.make_canonical(desired_destination_outputs[0][0]) if desired_destination_outputs else ''
    # NOTE: Include change in destinations for BTC transactions.
    # if change_output and not desired_data and desired_destination != config.UNSPENDABLE:
    #    if desired_destination == '':
    #        desired_destination = desired_source
    #    else:
    #        desired_destination += '-{}'.format(desired_source)
    # NOTE
    if desired_data == None:
        desired_data = b''

    # Parsed transaction info.
    try:
        parsed_source, parsed_destination, x, y, parsed_data = blocks._get_tx_info(unsigned_tx_hex)
    except exceptions.BTCOnlyError:
        # Skip BTC‐only transactions.
        if extended_tx_info:
            return {
                'btc_in': btc_in,
                'btc_out': destination_btc_out + data_btc_out,
                'btc_change': change_quantity,
                'btc_fee': final_fee,
                'tx_hex': unsigned_tx_hex,
            }
        return unsigned_tx_hex
    desired_source = script.make_canonical(desired_source)

    # Check desired info against parsed info.
    desired = (desired_source, desired_destination, desired_data)
    parsed = (parsed_source, parsed_destination, parsed_data)
    if desired != parsed:
        # Unlock (revert) UTXO locks
        if UTXO_LOCKS is not None:
            for input in inputs:
                UTXO_LOCKS[source].pop(make_outkey(input), None)

        raise exceptions.TransactionError('Constructed transaction does not parse correctly: {} ≠ {}'.format(desired, parsed))

    if extended_tx_info:
        return {
            'btc_in': btc_in,
            'btc_out': destination_btc_out + data_btc_out,
            'btc_change': change_quantity,
            'btc_fee': final_fee,
            'tx_hex': unsigned_tx_hex,
        }
    return unsigned_tx_hex

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
