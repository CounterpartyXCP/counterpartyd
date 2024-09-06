import decimal
import logging
import struct

from counterpartycore.lib import config, database, exceptions, ledger, util

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

ID = 90


def initialise(db):
    cursor = db.cursor()

    create_table_sql = """
        CREATE TABLE IF NOT EXISTS fairminters (
            tx_hash TEXT,
            tx_index INTEGER,
            block_index INTEGER,
            source TEXT,
            asset TEXT,
            asset_parent TEXT,
            asset_longname TEXT,
            description TEXT,
            price INTEGER,
            hard_cap INTEGER,
            burn_payment BOOL,
            max_mint_per_tx INTEGER,
            premint_quantity INTEGER,
            start_block INTEGER,
            end_block INTEGER,
            minted_asset_commission_int INTEGER,
            soft_cap INTEGER,
            soft_cap_deadline_block INTEGER,
            lock_description BOOL,
            lock_quantity BOOL,
            divisible BOOL,
            pre_minted BOOL DEFAULT 0,
            status TEXT
        )
    """
    cursor.execute(create_table_sql)

    database.create_indexes(
        cursor,
        "fairminters",
        [
            ["tx_hash"],
            ["block_index"],
            ["asset"],
            ["asset_longname"],
            ["asset_parent"],
            ["source"],
            ["status"],
        ],
    )


def validate(
    db,
    source,
    asset,
    asset_parent="",
    price=0,
    max_mint_per_tx=0,
    hard_cap=0,
    premint_quantity=0,
    start_block=0,
    end_block=0,
    soft_cap=0,
    soft_cap_deadline_block=0,
    minted_asset_commission=0.0,
    burn_payment=False,
    lock_description=False,
    lock_quantity=False,
    divisible=True,
    description="",
):
    problems = []

    # check integer parameters
    for param_name, param_value in {
        "price": price,
        "max_mint_per_tx": max_mint_per_tx,
        "hard_cap": hard_cap,
        "premint_quantity": premint_quantity,
        "start_block": start_block,
        "end_block": end_block,
        "soft_cap": soft_cap,
        "soft_cap_deadline_block": soft_cap_deadline_block,
    }.items():
        if param_value != 0:
            if not isinstance(param_value, int):
                problems.append(f"`{param_name}` must be an integer")
            elif param_value < 0:
                problems.append(f"`{param_name}` must be >= 0.")
            elif param_value > config.MAX_INT:
                problems.append(f"`{param_name}` exceeds maximum value")
    # check boolean parameters
    for param_name, param_value in {
        "burn_payment": burn_payment,
        "lock_description": lock_description,
        "lock_quantity": lock_quantity,
        "divisible": divisible,
    }.items():
        if not isinstance(param_value, bool):
            problems.append(f"`{param_name}` must be a boolean.")
    # check minted_asset_commission
    if minted_asset_commission is not None:
        if not isinstance(minted_asset_commission, (float, D)):
            problems.append("minted_asset_commission must be a float")
        elif minted_asset_commission < 0 or minted_asset_commission >= 1:
            problems.append(
                "`minted_asset_commission` must be less than 0 or greater than or equal to 1"
            )

    # check asset name format
    try:
        ledger.generate_asset_id(asset, util.CURRENT_BLOCK_INDEX)
        if asset_parent != "":
            ledger.generate_asset_id(asset_parent, util.CURRENT_BLOCK_INDEX)
    except exceptions.AssetNameError as e:
        problems.append(f"Invalid asset name: {e}")

    asset_name = asset
    # is subasset ?
    if asset_parent != "":
        asset_name = f"{asset_parent}.{asset}"

    # check if asset exists
    existing_asset = ledger.get_asset(db, asset_name)

    if existing_asset:
        # check if a fair minter is already opened for this asset
        if existing_asset["fair_minting"]:
            problems.append(f"Fair minter already opened for `{asset_name}`.")
        # check if asset is locked
        if existing_asset["locked"]:
            problems.append(f"Asset `{asset_name}` is locked.")
        # check if source is the issuer
        if existing_asset["issuer"] != source:
            problems.append(f"Asset `{asset_name}` is not issued by `{source}`.")
        # check if description is locked
        # TODO
        # if description != "" and existing_asset["description_locked"]:
        #    problems.append(f"Description of asset `{asset_name}` is locked.")
        # check if hard cap is already reached
        if hard_cap and existing_asset["supply"] + premint_quantity >= hard_cap:
            problems.append(f"Hard cap of asset `{asset_name}` is already reached.")
    else:
        if premint_quantity > 0 and premint_quantity >= hard_cap:
            problems.append("Premint quantity must be < hard cap.")

    if existing_asset is None and asset_parent != "":
        # if the asset does not exist its parent must exist
        existing_parent = ledger.get_asset(db, asset_parent)
        if existing_parent is None:
            problems.append("Asset parent does not exist")

    if price == 0 and max_mint_per_tx == 0:
        problems.append("Price or max_mint_per_tx must be > 0.")

    if end_block < 0:
        problems.append("end block must be greater than or equal to 0")

    if start_block > end_block > 0:
        problems.append("Start block must be <= end block.")  # could be one block fair minter

    if soft_cap >= hard_cap > 0:
        problems.append("Soft cap must be < hard cap.")
    if soft_cap > 0:
        if not soft_cap_deadline_block:
            problems.append("Soft cap deadline block must be specified if soft cap is specified.")
        elif soft_cap_deadline_block >= end_block > 0:
            problems.append("Soft cap deadline block must be < end block.")

    return problems


def compose(
    db,
    source,
    asset,
    asset_parent="",
    price=0,
    max_mint_per_tx=0,
    hard_cap=0,
    premint_quantity=0,
    start_block=0,
    end_block=0,
    soft_cap=0,
    soft_cap_deadline_block=0,
    minted_asset_commission=0.0,
    burn_payment=False,
    lock_description=False,
    lock_quantity=False,
    divisible=True,
    description="",
    no_validate=False,
):
    # validate parameters
    problems = validate(
        db,
        source,
        asset,
        asset_parent,
        price,
        max_mint_per_tx,
        hard_cap,
        premint_quantity,
        start_block,
        end_block,
        soft_cap,
        soft_cap_deadline_block,
        minted_asset_commission,
        burn_payment,
        lock_description,
        lock_quantity,
        divisible,
        description,
    )
    if len(problems) > 0 and not no_validate:
        raise exceptions.ComposeError(problems)

    minted_asset_commission_int = int(minted_asset_commission * 1e8)

    # create message
    data = struct.pack(config.SHORT_TXTYPE_FORMAT, ID)
    # to optimize the data size (avoiding fixed sizes per parameter) we use a simple
    # string of characters separated by `|`.
    # The description is placed last to be able to contain `|`.
    data_content = "|".join(
        [
            str(value)
            for value in [
                asset,
                asset_parent,
                price,
                max_mint_per_tx,
                hard_cap,
                premint_quantity,
                start_block,
                end_block,
                soft_cap,
                soft_cap_deadline_block,
                minted_asset_commission_int,
                int(burn_payment),
                int(lock_description),
                int(lock_quantity),
                int(divisible),
                description,
            ]
        ]
    ).encode("utf-8")
    data += struct.pack(f">{len(data_content)}s", data_content)
    return (source, [], data)


def unpack(message, return_dict=False):
    try:
        data_content = struct.unpack(f">{len(message)}s", message)[0].decode("utf-8").split("|")
        (
            asset,
            asset_parent,
            price,
            max_mint_per_tx,
            hard_cap,
            premint_quantity,
            start_block,
            end_block,
            soft_cap,
            soft_cap_deadline_block,
            minted_asset_commission_int,
            burn_payment,
            lock_description,
            lock_quantity,
            divisible,
        ) = data_content[0:15]
        # The description is placed last to be able to contain `|`.
        description = "|".join(data_content[15:]) if len(data_content) > 15 else ""

        minted_asset_commission = D(minted_asset_commission_int) / D(1e8)

        if return_dict:
            return {
                "asset": asset,
                "asset_parent": asset_parent,
                "price": int(price),
                "max_mint_per_tx": int(max_mint_per_tx),
                "hard_cap": int(hard_cap),
                "premint_quantity": int(premint_quantity),
                "start_block": int(start_block),
                "end_block": int(end_block),
                "soft_cap": int(soft_cap),
                "soft_cap_deadline_block": int(soft_cap_deadline_block),
                "minted_asset_commission": minted_asset_commission,
                "burn_payment": bool(int(burn_payment)),
                "lock_description": bool(int(lock_description)),
                "lock_quantity": bool(int(lock_quantity)),
                "divisible": bool(int(divisible)),
                "description": description,
            }

        return (
            asset,
            asset_parent,
            int(price),
            int(max_mint_per_tx),
            int(hard_cap),
            int(premint_quantity),
            int(start_block),
            int(end_block),
            int(soft_cap),
            int(soft_cap_deadline_block),
            minted_asset_commission,
            bool(int(burn_payment)),
            bool(int(lock_description)),
            bool(int(lock_quantity)),
            bool(int(divisible)),
            description,
        )
    except Exception as e:
        raise exceptions.UnpackError(f"Cannot unpack fair minter message: {e}") from e


def parse(db, tx, message):
    (
        asset,
        asset_parent,
        price,
        max_mint_per_tx,
        hard_cap,
        premint_quantity,
        start_block,
        end_block,
        soft_cap,
        soft_cap_deadline_block,
        minted_asset_commission,
        burn_payment,
        lock_description,
        lock_quantity,
        divisible,
        description,
    ) = unpack(message)

    problems = validate(
        db,
        tx["source"],
        asset,
        asset_parent,
        price,
        max_mint_per_tx,
        hard_cap,
        premint_quantity,
        start_block,
        end_block,
        soft_cap,
        soft_cap_deadline_block,
        minted_asset_commission,
        burn_payment,
        lock_description,
        lock_quantity,
        divisible,
        description,
    )

    # if problems, insert into fairminters table with status invalid and return
    if problems:
        status = "invalid: " + "; ".join(problems)
        bindings = {
            "tx_hash": tx["tx_hash"],
            "tx_index": tx["tx_index"],
            "block_index": tx["block_index"],
            "source": tx["source"],
            "status": status,
        }
        ledger.insert_record(db, "fairminters", bindings, "NEW_FAIRMINTER")
        logger.info(f"Fair minter {tx['tx_hash']} is invalid: {status}")
        return

    # determine status
    status = "pending"
    if start_block == 0 or tx["block_index"] >= start_block:
        status = "open"
    if end_block > 0 and tx["block_index"] > end_block:
        status = "closed"

    # is subasset ?
    asset_longname = ""
    if asset_parent != "":
        asset_longname = f"{asset_parent}.{asset}"

    existing_asset = ledger.get_asset(db, asset_longname if asset_longname != "" else asset)

    fee = 0
    asset_name = asset
    if asset_longname != "":
        # if the asset is a subasset and does not exist we generate a random numeric name
        # subassets are free
        if existing_asset is None:
            asset_name = util.generate_random_asset()
        else:
            asset_name = existing_asset["asset"]
    else:
        # only new named assets have fees
        if existing_asset is None and not asset.startswith("A"):
            fee = 0.5 * config.UNIT

    # we only premint if the faireminter is open and soft cap reached,
    # otherwise we will do it at opening (`start_block`) or when
    # the soft cap is reached
    pre_minted = False
    if status == "open" and premint_quantity > 0 and soft_cap == 0:
        pre_minted = True

    # insert into fairminters table
    bindings = {
        "tx_hash": tx["tx_hash"],
        "tx_index": tx["tx_index"],
        "block_index": tx["block_index"],
        "source": tx["source"],
        "asset": asset_name,
        "asset_parent": asset_parent,
        "asset_longname": asset_longname,
        "description": description,
        "price": price,
        "hard_cap": hard_cap,
        "burn_payment": burn_payment,
        "max_mint_per_tx": max_mint_per_tx,
        "premint_quantity": premint_quantity,
        "start_block": start_block,
        "end_block": end_block,
        "minted_asset_commission_int": int(minted_asset_commission * D(1e8)),
        "soft_cap": soft_cap,
        "soft_cap_deadline_block": soft_cap_deadline_block,
        "lock_description": lock_description,
        "lock_quantity": lock_quantity,
        "divisible": divisible,
        "status": status,
        "pre_minted": pre_minted,
    }
    ledger.insert_record(db, "fairminters", bindings, "NEW_FAIRMINTER")
    logger.info(f"Fair minter opened for {asset_name} by {tx['source']}.")

    if not existing_asset:
        # Add to table of assets if new asset
        asset_id = ledger.generate_asset_id(asset_name, tx["block_index"])
        bindings = {
            "asset_id": str(asset_id),
            "asset_name": asset_name,
            "block_index": tx["block_index"],
            "asset_longname": asset_longname if asset_longname != "" else None,
        }
        ledger.insert_record(db, "assets", bindings, "ASSET_CREATION")

    # insert issuance
    bindings = {
        "tx_index": tx["tx_index"],
        "tx_hash": tx["tx_hash"],
        "block_index": tx["block_index"],
        "asset": asset,
        "quantity": premint_quantity,
        "divisible": divisible,
        "source": tx["source"],
        "issuer": tx["source"],
        "transfer": False,
        "callable": False,
        "call_date": 0,
        "call_price": 0,
        "description": description,
        "fee_paid": fee,
        "locked": False,
        "reset": False,
        "status": "valid",
        "asset_longname": asset_longname,
        "fair_minting": True,
    }
    ledger.insert_record(db, "issuances", bindings, "ASSET_ISSUANCE")

    if pre_minted:
        # issuer is credited with the preminted quantity
        ledger.credit(
            db,
            tx["source"],
            asset_name,
            premint_quantity,
            tx["tx_index"],
            action="premint",
            event=tx["tx_hash"],
        )
    elif premint_quantity > 0:
        # This means that the fair mint is not yet open. In this case we escrow the premint.
        ledger.credit(
            db,
            config.UNSPENDABLE,
            asset_name,
            premint_quantity,
            tx["tx_index"],
            action="escrowed premint",
            event=tx["tx_hash"],
        )

    # debit fees
    if fee > 0:
        ledger.debit(
            db,
            tx["source"],
            config.XCP,
            int(fee),
            tx["tx_index"],
            action="fairminter fee",
            event=tx["tx_hash"],
        )


def unescrow_premint(db, fairminter, destroy=False):
    # unescrow premint quantity...
    ledger.debit(
        db,
        config.UNSPENDABLE,
        fairminter["asset"],
        fairminter["premint_quantity"],
        0,  # tx_index=0 for block actions
        action="unescrowed premint",
        event=fairminter["tx_hash"],
    )
    # ...and send it to the issuer
    if not destroy:
        ledger.credit(
            db,
            fairminter["source"],
            fairminter["asset"],
            fairminter["premint_quantity"],
            0,  # tx_index=0 for block actions
            action="premint",
            event=fairminter["tx_hash"],
        )


# called each block
def open_fairminters(db, block_index):
    # gets the fairminters with a `start_block` equal to `block_index`
    fairminters = ledger.get_fairminters_to_open(db, block_index)
    for fairminter in fairminters:
        assert fairminter["status"] != "open"  # sanity check
        # update status to open
        update_data = {"status": "open"}
        # if there is a premint we must unescrow it and send it to the issuer
        if fairminter["premint_quantity"] > 0 and fairminter["soft_cap"] == 0:
            assert not fairminter["pre_minted"]  # sanity check
            unescrow_premint(db, fairminter)
            update_data["pre_minted"] = True
        # update fairminter
        ledger.update_fairminter(db, fairminter["tx_hash"], update_data)


def close_fairminter(db, fairminter, block_index):
    # update status to closed
    ledger.update_fairminter(db, fairminter["tx_hash"], {"status": "closed"})
    # unlock issuance when fair minter is closed
    last_issuance = ledger.get_asset(db, fairminter["asset"])
    last_issuance["quantity"] = 0
    last_issuance["fair_minting"] = False
    last_issuance["block_index"] = block_index
    last_issuance["msg_index"] += 1  # (tx_index, msg_index) and (tx_hash, msg_index) are unique
    if fairminter["lock_quantity"]:
        last_issuance["locked"] = True
    if fairminter["lock_description"]:
        last_issuance["description_locked"] = True
    del last_issuance["supply"]
    ledger.insert_record(db, "issuances", last_issuance, "ASSET_ISSUANCE")


def close_fairminters(db, block_index):
    fairminters = ledger.get_fairminters_to_close(db, block_index)
    for fairminter in fairminters:
        assert fairminter["status"] != "closed"  # sanity check
        close_fairminter(db, fairminter, block_index)


def check_fairminter_soft_cap(db, fairminter, block_index):
    fairmint_quantity, paid_quantity = ledger.get_fairmint_quantities(db, fairminter["tx_hash"])
    fairminter_supply = fairmint_quantity + fairminter["premint_quantity"]
    fairmints = ledger.get_valid_fairmints(db, fairminter["tx_hash"])

    # we start by unescrow all the assets and payments for this fairminter...
    ledger.debit(
        db,
        config.UNSPENDABLE,
        fairminter["asset"],
        fairminter_supply,
        0,  # tx_index=0 for block actions
        action="unescrowed fairmint",
        event=fairminter["tx_hash"],
    )
    if paid_quantity > 0:
        ledger.debit(
            db,
            config.UNSPENDABLE,
            config.XCP,
            paid_quantity,
            0,  # tx_index=0 for block actions
            action="unescrowed fairmint payment",
            event=fairminter["tx_hash"],
        )
    # ...and then we loop on the fairmints to decide how
    # to distribute the assets and payments
    for fairmint in fairmints:
        # is the fairmint paid ?
        if fairmint["paid_quantity"] > 0:
            # soft cap not reached
            if fairmint_quantity < fairminter["soft_cap"]:
                # reimburse paid quantity to minter
                xcp_destination = fairmint["source"]
                xcp_action = "fairmint refund"
            # soft cap reached but payment is burned
            elif fairminter["burn_payment"]:
                # burn paid quantity
                xcp_destination = None
                xcp_action = "burned fairmint payment"
            # soft cap reached and payment sent to issuer
            else:
                # send funds to issuer
                xcp_destination = fairminter["source"]
                xcp_action = "fairmint payment"
            # credit paid quantity to issuer or minter...
            if xcp_destination:
                ledger.credit(
                    db,
                    xcp_destination,
                    config.XCP,
                    fairmint["paid_quantity"],
                    fairmint["tx_index"],
                    action=xcp_action,
                    event=fairmint["tx_hash"],
                )
            # ...or destroy it
            else:
                bindings = {
                    "tx_index": fairmint["tx_index"],
                    "tx_hash": fairmint["tx_hash"],
                    "block_index": block_index,
                    "source": fairmint["source"],
                    "asset": config.XCP,
                    "quantity": fairmint["paid_quantity"],
                    "tag": xcp_action,
                    "status": "valid",
                }
                ledger.insert_record(db, "destructions", bindings, "ASSET_DESTRUCTION")

        # the soft cap is reached:
        # - the assets are distributed to the miner,
        # - the commissions to the issuer,
        # - the premint is unescrowed
        if fairmint_quantity >= fairminter["soft_cap"]:
            # send assets to minter
            ledger.credit(
                db,
                fairmint["source"],
                fairminter["asset"],
                fairmint["earn_quantity"],
                fairmint["tx_index"],
                action="unescrowed fairmint",
                event=fairmint["tx_hash"],
            )
            # send commission to issuer
            if fairmint["commission"] > 0:
                ledger.credit(
                    db,
                    fairminter["source"],
                    fairminter["asset"],
                    fairmint["commission"],
                    fairmint["tx_index"],
                    action="fairmint commission",
                    event=fairmint["tx_hash"],
                )
    if fairminter["premint_quantity"] > 0:
        ledger.credit(
            db,
            fairminter["source"],
            fairminter["asset"],
            fairminter["premint_quantity"],
            0,  # tx_index=0 for block actions
            action="premint",
            event=fairminter["tx_hash"],
        )
    # the soft cap is not reached, we close the
    # fairminter and destroy all the assets at once
    if fairmint_quantity < fairminter["soft_cap"]:
        close_fairminter(db, fairminter, block_index)
        # destroy assets
        bindings = {
            "tx_index": fairminter["tx_index"],
            "tx_hash": fairminter["tx_hash"],
            "block_index": block_index,
            "source": fairminter["source"],
            "asset": fairminter["asset"],
            "quantity": fairminter_supply,
            "tag": "soft cap not reached",
            "status": "valid",
        }
        ledger.insert_record(db, "destructions", bindings, "ASSET_DESTRUCTION")


def check_soft_cap(db, block_index):
    # get fairminters with `soft_cap_deadline_block` equal to `block_index`
    fairminters = ledger.get_soft_caped_fairminters(db, block_index)

    # we loop on the fairminters to check if the soft cap is reached.
    # If it is reached we transfer the assets to the minters and the payments
    # to the issuer. If not we refund the payments and destroy the assets.
    for fairminter in fairminters:
        check_fairminter_soft_cap(db, fairminter, block_index)


# This function is called on each block BEFORE parsing the transactions
def before_block(db, block_index):
    open_fairminters(db, block_index)


# This function is called on each block AFTER parsing the transactions
def after_block(db, block_index):
    check_soft_cap(db, block_index)
    close_fairminters(db, block_index)
