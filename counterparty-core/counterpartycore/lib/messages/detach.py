import logging
import struct

from counterpartycore.lib import config, exceptions, ledger, script, util

logger = logging.getLogger(config.LOGGER_NAME)

ID = 102


def validate(source, destination=None):
    problems = []

    # check if source is a UTXO
    if not util.is_utxo_format(source):
        problems.append("source must be a UTXO")

    # check if destination is an address
    if destination is not None:
        try:
            script.validate(destination)
        except script.AddressError:
            problems.append("destination must be an address")

    return problems


def compose(db, source, destination=None):
    problems = validate(source, destination)
    if problems:
        raise exceptions.ComposeError(problems)

    # create message
    data = struct.pack(config.SHORT_TXTYPE_FORMAT, ID)
    # only the destination is needed
    if destination is not None:
        data_content = destination.encode("utf-8")
    else:
        data_content = b"0"  # not empty to avoid a protocol change in `message_type.unpack()`
    data += struct.pack(f">{len(data_content)}s", data_content)

    return (source, [], data)


def unpack(message, return_dict=False):
    try:
        if message == b"0":  # no destination
            destination = None
        else:
            destination = struct.unpack(f">{len(message)}s", message)[0].decode("utf-8")

        if return_dict:
            return {
                "destination": destination,
            }
        return destination
    except Exception as e:
        raise exceptions.UnpackError(f"Cannot unpack utxo message: {e}") from e


def detach_assets(db, tx, source, destination):
    problems = validate(source, destination)

    status = "valid"
    if problems:
        status = "invalid: " + "; ".join(problems)
        # store the invalid transaction without potentially invalid parameters
        bindings = {
            "tx_index": tx["tx_index"],
            "tx_hash": tx["tx_hash"],
            "msg_index": ledger.get_send_msg_index(db, tx["tx_hash"]),
            "block_index": tx["block_index"],
            "status": status,
        }
        ledger.insert_record(db, "sends", bindings, "DETACH_FROM_UTXO")
        # stop here to avoid further processing
        return

    # we detach all the assets from the source UTXO
    balances = ledger.get_utxo_balances(db, source)
    for balance in balances:
        if balance["quantity"] == 0:
            continue
        # debit asset from source and credit to recipient
        action = "detach from utxo"

        # if no destination is provided, we credit the asset to utxo_address
        if destination is None:
            destination = balance["utxo_address"]

        ledger.debit(
            db,
            source,
            balance["asset"],
            balance["quantity"],
            tx["tx_index"],
            action=action,
            event=tx["tx_hash"],
        )
        ledger.credit(
            db,
            destination,
            balance["asset"],
            balance["quantity"],
            tx["tx_index"],
            action=action,
            event=tx["tx_hash"],
        )
        bindings = {
            "tx_index": tx["tx_index"],
            "tx_hash": tx["tx_hash"],
            "msg_index": ledger.get_send_msg_index(db, tx["tx_hash"]),
            "block_index": tx["block_index"],
            "status": "valid",
            "source": source,
            "destination": destination,
            "asset": balance["asset"],
            "quantity": balance["quantity"],
            "fee_paid": 0,
        }
        ledger.insert_record(db, "sends", bindings, "DETACH_FROM_UTXO")

    logger.info(
        "Detach assets from %(source)s to address: %(destination)s (%(tx_hash)s) [%(status)s]",
        {
            "source": source,
            "destination": destination,
            "tx_hash": tx["tx_hash"],
            "status": status,
        },
    )


def parse(db, tx, message):
    destination = unpack(message)

    # get all inputs with balances
    sources = util.get_sources_from_utxos_info(tx["utxos_info"])

    # detach assets from all the sources
    # IMPORTANT: that's mean we can't detach assets and move utxo in th same transaction
    for source in sources:
        detach_assets(db, tx, source, destination)