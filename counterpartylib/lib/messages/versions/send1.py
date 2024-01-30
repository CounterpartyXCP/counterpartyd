#! /usr/bin/python3

"""Create and parse 'send'-type messages."""

import struct
import json
import logging
logger = logging.getLogger(__name__)

from ... import (config, exceptions, util, message_type, ledger)

FORMAT = '>QQ'
LENGTH = 8 + 8
ID = 0

def unpack(db, message, block_index):
    # Only used for `unpack` API call at the moment.
    try:
        asset_id, quantity = struct.unpack(FORMAT, message)
        asset = ledger.get_asset_name(db, asset_id, block_index)

    except struct.error:
        raise exceptions.UnpackError('could not unpack')

    except exceptions.AssetNameError:
        raise exceptions.UnpackError('asset id invalid')

    unpacked = {
                'asset': asset,
                'quantity': quantity
               }
    return unpacked

def validate (db, source, destination, asset, quantity, block_index):
    problems = []

    if asset == config.BTC: problems.append('cannot send bitcoins')  # Only for parsing.

    if not isinstance(quantity, int):
        problems.append('quantity must be in satoshis')
        return problems

    if quantity < 0:
        problems.append('negative quantity')

    # For SQLite3
    if quantity > config.MAX_INT:
        problems.append('integer overflow')

    if ledger.enabled('send_destination_required'):  # Protocol change.
        if not destination:
            problems.append('destination is required')

    if ledger.enabled('options_require_memo'):
        # Check destination address options

        cursor = db.cursor()
        results = cursor.execute('SELECT options FROM addresses WHERE address=?', (destination,))
        if results:
            result = results.fetchone()
            if result and util.active_options(result['options'], config.ADDRESS_OPTION_REQUIRE_MEMO):
                problems.append('destination requires memo')
        cursor.close()

    return problems

def compose (db, source, destination, asset, quantity):
    cursor = db.cursor()

    # Just send BTC?
    if asset == config.BTC:
        return (source, [(destination, quantity)], None)

    # resolve subassets
    asset = ledger.resolve_subasset_longname(db, asset)

    #quantity must be in int satoshi (not float, string, etc)
    if not isinstance(quantity, int):
        raise exceptions.ComposeError('quantity must be an int (in satoshi)')

    # Only for outgoing (incoming will overburn).
    balance = ledger.get_balance(db, source, asset)
    if balance < quantity:
        raise exceptions.ComposeError('insufficient funds')

    block_index = ledger.CURRENT_BLOCK_INDEX

    problems = validate(db, source, destination, asset, quantity, block_index)
    if problems: raise exceptions.ComposeError(problems)

    asset_id = ledger.get_asset_id(db, asset, block_index)
    data = message_type.pack(ID)
    data += struct.pack(FORMAT, asset_id, quantity)

    cursor.close()
    return (source, [(destination, None)], data)

def parse (db, tx, message):
    cursor = db.cursor()

    # Unpack message.
    try:
        if len(message) != LENGTH:
            raise exceptions.UnpackError
        asset_id, quantity = struct.unpack(FORMAT, message)
        asset = ledger.get_asset_name(db, asset_id, tx['block_index'])
        status = 'valid'
    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:
        asset, quantity = None, None
        status = 'invalid: could not unpack'

    if status == 'valid':
        # Oversend
        # doesn't make sense (0 and no balance should be the same) but let's not break the protocol
        try:
            balance = ledger.get_balance(db, tx['source'], asset, raise_error_if_no_balance=True)
            if balance < quantity:
                quantity = min(balance, quantity)
        except exceptions.BalanceError:
            status = 'invalid: insufficient funds'
       

    # For SQLite3
    if quantity:
        quantity = min(quantity, config.MAX_INT)

    if status == 'valid':
        problems = validate(db, tx['source'], tx['destination'], asset, quantity, tx['block_index'])
        if problems: status = 'invalid: ' + '; '.join(problems)

    if status == 'valid':
        ledger.debit(db, tx['source'], asset, quantity, tx['tx_index'], action='send', event=tx['tx_hash'])
        ledger.credit(db, tx['destination'], asset, quantity, tx['tx_index'], action='send', event=tx['tx_hash'])

    # Add parsed transaction to message-type–specific table.
    bindings = {
        'tx_index': tx['tx_index'],
        'tx_hash': tx['tx_hash'],
        'block_index': tx['block_index'],
        'source': tx['source'],
        'destination': tx['destination'],
        'asset': asset,
        'quantity': quantity,
        'status': status,
    }
    if "integer overflow" not in status and "quantity must be in satoshis" not in status:
        sql = 'insert into sends (tx_index, tx_hash, block_index, source, destination, asset, quantity, status, memo) values(:tx_index, :tx_hash, :block_index, :source, :destination, :asset, :quantity, :status, NULL)'
        cursor.execute(sql, bindings)
    else:
        logger.warning("Not storing [send] tx [%s]: %s" % (tx['tx_hash'], status))
        logger.debug("Bindings: %s" % (json.dumps(bindings), ))


    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
