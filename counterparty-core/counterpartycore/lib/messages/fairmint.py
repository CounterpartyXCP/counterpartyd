import decimal
import logging
import struct

from counterpartycore.lib import config, database, exceptions, ledger
from counterpartycore.lib.messages import fairminter as fairminter_mod

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

ID = 91


def initialise(db):
    cursor = db.cursor()

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS fairmints (
            tx_hash TEXT PRIMARY KEY,
            tx_index INTEGER,
            block_index INTEGER,
            source TEXT,
            fairminter_tx_hash TEXT,
            asset TEXT,
            earn_quantity INTEGER,
            paid_quantity INTEGER,
            commission INTEGER,
            status TEXT
        )
    """

    cursor.execute(create_table_sql)

    database.create_indexes(
        cursor,
        "fairmints",
        [
            ["tx_hash"],
            ["block_index"],
            ["fairminter_tx_hash"],
            ["asset"],
            ["source"],
            ["status"],
        ],
    )


def validate(
    db,
    source,
    asset,
    quantity=0,
):
    problems = []

    if not isinstance(quantity, int):
        problems.append("quantity must be an integer")

    fairminter = ledger.get_fairminter_by_asset(db, asset)
    if not fairminter:
        problems.append(f"fairminter not found for asset: `{asset}`")
        return problems

    if fairminter["status"] != "open":
        problems.append(f"fairminter is not open for asset: `{asset}`")

    asset_supply = ledger.asset_supply(db, fairminter["asset"])

    if fairminter["price"] > 0:
        # if the fairminter is not free the quantity is mandatory
        if quantity <= 0:
            problems.append("Quantity must be greater than 0")
            return problems
        if fairminter["max_mint_per_tx"] > 0 and quantity > fairminter["max_mint_per_tx"]:
            problems.append("Quantity exceeds maximum allowed per transaction")
            return problems
        if quantity > config.MAX_INT:
            problems.append("quantity exceeds maximum allowed value")
            return problems
        # check id we don't exceed the hard cap
        if fairminter["hard_cap"] > 0 and asset_supply + quantity > fairminter["hard_cap"]:
            problems.append("asset supply quantity exceeds hard cap")
        # check if the user has enough XCP
        xcp_total_price = quantity * fairminter["price"]
        balance = ledger.get_balance(db, source, config.XCP)
        if balance < xcp_total_price:
            problems.append("insufficient XCP balance")
    else:
        # check id we don't exceed the hard cap
        if (
            fairminter["hard_cap"] > 0
            and asset_supply + fairminter["max_mint_per_tx"] > fairminter["hard_cap"]
        ):
            problems.append("asset supply quantity exceeds hard cap")

    return problems


def compose(
    db,
    source,
    asset,
    quantity=0,
    no_validate=False,
):
    problems = validate(db, source, asset, quantity)
    if len(problems) > 0 and not no_validate:
        raise exceptions.ComposeError(problems)

    # create message
    data = struct.pack(config.SHORT_TXTYPE_FORMAT, ID)
    # to optimize the data size (avoiding fixed sizes per parameter) we use a simple
    # string of characters separated by `|`.
    data_content = "|".join(
        [
            str(value)
            for value in [
                asset,
                quantity,
            ]
        ]
    ).encode("utf-8")
    data += struct.pack(f">{len(data_content)}s", data_content)
    return (source, [], data)


def unpack(message, return_dict=False):
    try:
        data_content = struct.unpack(f">{len(message)}s", message)[0].decode("utf-8").split("|")
        (asset, quantity) = data_content
        if return_dict:
            return {"asset": asset, "quantity": int(quantity)}

        return (asset, int(quantity))
    except Exception as e:
        raise exceptions.UnpackError(f"Cannot unpack fair mint message: {e}") from e


def parse(db, tx, message):
    (asset, quantity) = unpack(message)
    problems = validate(db, tx["source"], asset, quantity)

    # if problems, insert into fairmints table with status invalid and return
    status = "valid"
    if problems:
        status = "invalid: " + "; ".join(problems)
        bindings = {
            "tx_hash": tx["tx_hash"],
            "tx_index": tx["tx_index"],
            "block_index": tx["block_index"],
            "source": tx["source"],
            "status": status,
        }
        ledger.insert_record(db, "fairmints", bindings, "NEW_FAIRMINT")
        logger.info(f"Fairmint {tx['tx_hash']} is invalid: {status}")
        return

    # get corresponding fairminter
    fairminter = ledger.get_fairminter_by_asset(db, asset)

    # determine if the soft cap has been reached
    soft_cap_not_reached = (
        fairminter["soft_cap"] > 0 and fairminter["soft_cap_deadline_block"] >= tx["block_index"]
    )

    # we determine who to send the payment and assets to
    # By default the assets are sent to the minter
    # and the payment to the issuer
    xcp_action = "fairmint payment"
    xcp_destination = fairminter["source"]
    asset_action = "fairmint"
    asset_destination = tx["source"]

    # if the soft cap is not reached we escrow the assets and payments
    # which will be distributed in the `fairminters.check_soft_cap()` function.
    if soft_cap_not_reached:
        xcp_action = "escrowed fairmint"
        xcp_destination = config.UNSPENDABLE
        asset_action = "escrowed fairmint"
        asset_destination = config.UNSPENDABLE
    # if the soft cap is reached but the payment must
    # be burned there is no destination.
    elif fairminter["burn_payment"]:
        xcp_action = "burn fairmint payment"
        xcp_destination = None
    # we determine how many assets we need to send
    # and the price paid by the user
    if fairminter["price"] > 0:
        paid_quantity = quantity * fairminter["price"]
        earn_quantity = quantity
    else:
        paid_quantity = 0
        earn_quantity = fairminter["max_mint_per_tx"]
    # we determine the commission to be paid to the issuer
    # and we subtract it from the assets to be sent to the user
    commission = 0
    if fairminter["minted_asset_commission_int"] > 0:
        commission = int((D(fairminter["minted_asset_commission_int"]) / D(1e8)) * D(earn_quantity))
        earn_quantity -= commission

    if paid_quantity > 0:
        # we debit the user
        ledger.debit(
            db, tx["source"], config.XCP, paid_quantity, tx["tx_index"], xcp_action, tx["tx_hash"]
        )
        if xcp_destination:
            # we credit the destination if it exists (issuer or escrow)
            ledger.credit(
                db,
                xcp_destination,
                config.XCP,
                paid_quantity,
                tx["tx_index"],
                xcp_action,
                tx["tx_hash"],
            )
        else:
            # else we burn the payment
            bindings = {
                "tx_index": tx["tx_index"],
                "tx_hash": tx["tx_hash"],
                "block_index": tx["block_index"],
                "source": tx["source"],
                "asset": config.XCP,
                "quantity": paid_quantity,
                "tag": xcp_action,
                "status": "valid",
            }
            ledger.insert_record(db, "destructions", bindings, "ASSET_DESTRUCTION")

    if asset_destination == config.UNSPENDABLE:
        # the minted amount and commission are escrowed
        ledger.credit(
            db,
            asset_destination,
            asset,
            earn_quantity + commission,
            tx["tx_index"],
            asset_action,
            tx["tx_hash"],
        )
    else:
        # the minted amount is sent to the user
        ledger.credit(
            db, asset_destination, asset, earn_quantity, tx["tx_index"], asset_action, tx["tx_hash"]
        )
        if commission > 0:
            # the commission is sent to the issuer
            ledger.credit(
                db,
                fairminter["source"],
                asset,
                commission,
                tx["tx_index"],
                "fairmint commission",
                tx["tx_hash"],
            )

    # we insert the fairmint record
    bindings = {
        "tx_hash": tx["tx_hash"],
        "tx_index": tx["tx_index"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "fairminter_tx_hash": fairminter["tx_hash"],
        "asset": fairminter["asset"],
        "earn_quantity": earn_quantity,
        "paid_quantity": paid_quantity,
        "commission": commission,
        "status": status,
    }
    ledger.insert_record(db, "fairmints", bindings, "NEW_FAIRMINT")

    # we prepare the new issuance
    last_issuance = ledger.get_asset(db, asset)
    bindings = last_issuance | {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "quantity": earn_quantity + commission,
        "source": tx["source"],
        "status": "valid",
        "fee_paid": 0,
    }

    # we check if the hard cap is reached and in this case...
    if fairminter["hard_cap"] > 0:
        asset_supply = ledger.asset_supply(db, fairminter["asset"])
        if asset_supply + quantity == fairminter["hard_cap"]:
            # ...we unlock the issuances for this assets
            bindings["fair_minting"] = False
            # we check if we need to lock the assets
            if fairminter["lock_quantity"]:
                bindings["locked"] = True
            if fairminter["lock_description"]:
                bindings["description_locked"] = True
            # and we close the fairminter
            if (
                fairminter["soft_cap"] > 0
                and fairminter["soft_cap_deadline_block"] >= tx["block_index"]
            ):
                fairminter_mod.check_fairminter_soft_cap(db, fairminter, tx["block_index"])
            ledger.update_fairminter(db, fairminter["tx_hash"], {"status": "closed"})

    # we insert the new issuance
    del bindings["supply"]
    ledger.insert_record(db, "issuances", bindings, "ASSET_ISSUANCE")

    # log
    logger.info(
        f"{earn_quantity + commission} {asset} minted for {paid_quantity} XCP by {tx['source']}"
    )
