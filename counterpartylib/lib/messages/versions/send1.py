#! /usr/bin/python3

"""Create and parse 'send'-type messages."""

import struct
import json
import logging
logger = logging.getLogger(__name__)

from ... import (config, exceptions, util)

FORMAT = '>QQ'
LENGTH = 8 + 8
ID = 0

def unpack(db, message, block_index):
    # Only used for `unpack` API call at the moment.
    try:
        asset_id, quantity = struct.unpack(FORMAT, message)
        asset = util.get_asset_name(db, asset_id, block_index)

    except struct.error:
        raise UnpackError('could not unpack')

    except AssetNameError:
        raise UnpackError('asset id invalid')

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

    if util.enabled('send_destination_required'):  # Protocol change.
        if not destination:
            problems.append('destination is required')

    return problems

def compose (db, source, destination, asset, quantity):
    cursor = db.cursor()

    # Just send BTC?
    if asset == config.BTC:
        return (source, [(destination, quantity)], None)

    # resolve subassets
    asset = util.resolve_subasset_longname(db, asset)

    #quantity must be in int satoshi (not float, string, etc)
    if not isinstance(quantity, int):
        raise exceptions.ComposeError('quantity must be an int (in satoshi)')

    # Only for outgoing (incoming will overburn).
    balances = list(cursor.execute('''SELECT * FROM balances WHERE (address = ? AND asset = ?)''', (source, asset)))
    if not balances or balances[0]['quantity'] < quantity:
        raise exceptions.ComposeError('insufficient funds')

    block_index = util.CURRENT_BLOCK_INDEX

    problems = validate(db, source, destination, asset, quantity, block_index)
    if problems: raise exceptions.ComposeError(problems)

    asset_id = util.get_asset_id(db, asset, block_index)
    data = struct.pack(config.TXTYPE_FORMAT, ID)
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
        asset = util.get_asset_name(db, asset_id, tx['block_index'])
        status = 'valid'
    except (exceptions.UnpackError, exceptions.AssetNameError, struct.error) as e:
        asset, quantity = None, None
        status = 'invalid: could not unpack'

    if status == 'valid':
        # Oversend
        cursor.execute('''SELECT * FROM balances \
                                     WHERE (address = ? AND asset = ?)''', (tx['source'], asset))
        balances = cursor.fetchall()
        if not balances:
            status = 'invalid: insufficient funds'
        elif balances[0]['quantity'] < quantity:
            quantity = min(balances[0]['quantity'], quantity)

    # For SQLite3
    if quantity:
        quantity = min(quantity, config.MAX_INT)

    if status == 'valid':
        problems = validate(db, tx['source'], tx['destination'], asset, quantity, tx['block_index'])
        if problems: status = 'invalid: ' + '; '.join(problems)

    if status == 'valid':
        util.debit(db, tx['source'], asset, quantity, action='send', event=tx['tx_hash'])
        
        if util.enabled('burn_assets'):
            if config.TESTNET: 
                unspendable = config.UNSPENDABLE_TESTNET
            else:
                unspendable = config.UNSPENDABLE_MAINNET
                
            if tx['destination'] != unspendable:
                util.credit(db, tx['destination'], asset, quantity, action='send', event=tx['tx_hash'])
            else:
                quantity = -quantity
                
                #get asset issuance info
                issuance_cursor = db.cursor()
                issuances = list(issuance_cursor.execute('''SELECT * FROM issuances \
                                                            WHERE (status = ? AND asset = ?)
                                                            ORDER BY tx_index ASC''', ('valid', asset)))
                issuance_cursor.close()
                description = issuances[-1]['description']  # Use last 
                locked = issuances[-1]['locked']  # Use last
                divisible = issuances[-1]['divisible']  # Use last 
                issuer = issuances[-1]['issuer']  # Use last 

                bindings= {
                    'tx_index': tx['tx_index'],
                    'tx_hash': tx['tx_hash'],
                    'block_index': tx['block_index'],
                    'asset': asset,
                    'quantity': quantity,
                    'divisible': divisible,
                    'source': tx['source'], 
                    'issuer': issuer, 
                    'transfer': 0,
                    'callable': 0,
                    'call_date': 0,
                    'call_price': 0,
                    'description': description, 
                    'fee_paid': 0,
                    'locked': lock, 
                    'status': status,
                }
                sql='insert into issuances values(:tx_index, :tx_hash, :block_index, :asset, :quantity, :divisible, :source, :issuer, :transfer, :callable, :call_date, :call_price, :description, :fee_paid, :locked, :status)'
                issuance_cursor.execute(sql, bindings)
        else:
            util.credit(db, tx['destination'], asset, quantity, action='send', event=tx['tx_hash'])
   

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
        sql = 'insert into sends values(:tx_index, :tx_hash, :block_index, :source, :destination, :asset, :quantity, :status)'
        cursor.execute(sql, bindings)
    else:
        logger.warn("Not storing [send] tx [%s]: %s" % (tx['tx_hash'], status))
        logger.debug("Bindings: %s" % (json.dumps(bindings), ))


    cursor.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
