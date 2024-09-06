#! /usr/bin/python3

"""
Allow simultaneous lock and transfer.
"""

import decimal
import logging
import struct

from counterpartycore.lib import config, database, exceptions, ledger, message_type, util

logger = logging.getLogger(config.LOGGER_NAME)
D = decimal.Decimal

FORMAT_1 = ">QQ?"
LENGTH_1 = 8 + 8 + 1
FORMAT_2 = ">QQ??If"
LENGTH_2 = 8 + 8 + 1 + 1 + 4 + 4
SUBASSET_FORMAT = ">QQ?B"
SUBASSET_FORMAT_LENGTH = 8 + 8 + 1 + 1
ID = 20
SUBASSET_ID = 21
# NOTE: Pascal strings are used for storing descriptions for backwards‐compatibility.

# Lock Reset issuances. Default composed message
LR_ISSUANCE_ID = 22
LR_SUBASSET_ID = 23

DESCRIPTION_MARK_BYTE = b"\xc0"
DESCRIPTION_NULL_ACTION = "NULL"


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "valid_asset_idx",
            "status_idx",
            "source_idx",
            "asset_longname_idx",
            "status_asset_txindex_idx",
        ],
    )

    cursor.execute("""CREATE TABLE IF NOT EXISTS issuances(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      asset TEXT,
                      quantity INTEGER,
                      divisible BOOL,
                      source TEXT,
                      issuer TEXT,
                      transfer BOOL,
                      callable BOOL,
                      call_date INTEGER,
                      call_price REAL,
                      description TEXT,
                      fee_paid INTEGER,
                      locked BOOL,
                      status TEXT,
                      asset_longname TEXT,
                      reset BOOL,
                      description_locked BOOL,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)

    # Add asset_longname for sub-assets
    #   SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS`.
    columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(issuances)""")]
    if "asset_longname" not in columns:
        cursor.execute("""ALTER TABLE issuances ADD COLUMN asset_longname TEXT""")
    if "reset" not in columns:
        cursor.execute("""ALTER TABLE issuances ADD COLUMN reset BOOL""")
    if "description_locked" not in columns:
        cursor.execute("""ALTER TABLE issuances ADD COLUMN description_locked BOOL""")

    # If sweep_hotfix activated, Create issuances copy, copy old data, drop old table, rename new table, recreate indexes
    #   SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS` nor can drop UNIQUE constraints
    if "msg_index" not in columns:
        cursor.execute("""CREATE TABLE IF NOT EXISTS new_issuances(
                              tx_index INTEGER,
                              tx_hash TEXT,
                              msg_index INTEGER DEFAULT 0,
                              block_index INTEGER,
                              asset TEXT,
                              quantity INTEGER,
                              divisible BOOL,
                              source TEXT,
                              issuer TEXT,
                              transfer BOOL,
                              callable BOOL,
                              call_date INTEGER,
                              call_price REAL,
                              description TEXT,
                              fee_paid INTEGER,
                              locked BOOL,
                              status TEXT,
                              asset_longname TEXT,
                              reset BOOL,
                              description_locked BOOL,
                              PRIMARY KEY (tx_index, msg_index),
                              FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                              UNIQUE (tx_hash, msg_index))
                           """)
        cursor.execute(
            """INSERT INTO new_issuances(tx_index, tx_hash, msg_index,
                block_index, asset, quantity, divisible, source, issuer, transfer, callable,
                call_date, call_price, description, fee_paid, locked, status, asset_longname, reset, description_locked)
                SELECT tx_index, tx_hash, 0, block_index, asset, quantity, divisible, source,
                issuer, transfer, callable, call_date, call_price, description, fee_paid,
                locked, status, asset_longname, reset, description_locked FROM issuances""",
            {},
        )
        cursor.execute("DROP TABLE issuances")
        cursor.execute("ALTER TABLE new_issuances RENAME TO issuances")

    if "fair_minting" not in columns:
        cursor.execute("""ALTER TABLE issuances ADD COLUMN fair_minting BOOL DEFAULT 0""")

    # remove FOREIGN KEY with transactions
    if database.has_fk_on(cursor, "issuances", "transactions.tx_index"):
        create_issuances_query = """
            CREATE TABLE IF NOT EXISTS issuances(
                tx_index INTEGER,
                tx_hash TEXT,
                msg_index INTEGER DEFAULT 0,
                block_index INTEGER,
                asset TEXT,
                quantity INTEGER,
                divisible BOOL,
                source TEXT,
                issuer TEXT,
                transfer BOOL,
                callable BOOL,
                call_date INTEGER,
                call_price REAL,
                description TEXT,
                fee_paid INTEGER,
                locked BOOL,
                status TEXT,
                asset_longname TEXT,
                reset BOOL,
                description_locked BOOL,
                fair_minting BOOL DEFAULT 0,
                PRIMARY KEY (tx_index, msg_index),
                UNIQUE (tx_hash, msg_index)
            )
        """
        database.copy_old_table(cursor, "issuances", create_issuances_query)

    database.create_indexes(
        cursor,
        "issuances",
        [
            ["block_index"],
            ["asset", "status"],
            ["status"],
            ["source"],
            ["asset_longname"],
            ["status", "asset", "tx_index DESC"],
            ["issuer"],
        ],
    )


def validate(
    db,
    source,
    destination,
    asset,
    quantity,
    divisible,
    lock,
    reset,
    callable_,
    call_date,
    call_price,
    description,
    subasset_parent,
    subasset_longname,
    block_index,
):
    problems = []
    fee = 0

    if asset in (config.BTC, config.XCP):
        problems.append(f"cannot issue {config.BTC} or {config.XCP}")

    if call_date is None:
        call_date = 0
    if call_price is None:
        call_price = 0.0
    if description is None:
        description = ""
    if divisible is None:
        divisible = True
    if lock is None:
        lock = False
    if reset is None:
        reset = False

    if isinstance(call_price, int):
        call_price = float(call_price)
    # ^ helps especially with calls from JS‐based clients, where parseFloat(15) returns 15 (not 15.0), which json takes as an int

    if not isinstance(quantity, int):
        problems.append("quantity must be in satoshis")
        return call_date, call_price, problems, fee, description, divisible, None, None
    if call_date and not isinstance(call_date, int):
        problems.append("call_date must be epoch integer")
        return call_date, call_price, problems, fee, description, divisible, None, None
    if call_price and not isinstance(call_price, float):
        problems.append("call_price must be a float")
        return call_date, call_price, problems, fee, description, divisible, None, None

    if quantity < 0:
        problems.append("negative quantity")
    if call_price < 0:
        problems.append("negative call price")
    if call_date < 0:
        problems.append("negative call date")

    # Callable, or not.
    if not callable_:
        if block_index >= 312500 or config.TESTNET or config.REGTEST:  # Protocol change.
            call_date = 0
            call_price = 0.0
        elif block_index >= 310000:  # Protocol change.
            if call_date:
                problems.append("call date for non‐callable asset")
            if call_price:
                problems.append("call price for non‐callable asset")

    # Valid re-issuance?
    issuances = ledger.get_issuances(db, asset=asset, status="valid", first=True)
    reissued_asset_longname = None
    if issuances:
        reissuance = True
        last_issuance = issuances[-1]
        reissued_asset_longname = last_issuance["asset_longname"]
        issuance_locked = False
        if util.enabled("issuance_lock_fix"):
            for issuance in issuances:
                if issuance["locked"]:
                    issuance_locked = True
                    break
        elif last_issuance["locked"]:
            # before the issuance_lock_fix, only the last issuance was checked
            issuance_locked = True

        if last_issuance["fair_minting"]:
            problems.append("cannot issue during fair minting")

        if last_issuance["issuer"] != source:
            problems.append("issued by another address")
        if (bool(last_issuance["divisible"]) != bool(divisible)) and (
            (not util.enabled("cip03", block_index)) or (not reset)
        ):
            problems.append("cannot change divisibility")
        if (not util.enabled("issuance_callability_parameters_removal", block_index)) and bool(
            last_issuance["callable"]
        ) != bool(callable_):
            problems.append("cannot change callability")
        if last_issuance["call_date"] > call_date and (
            call_date != 0 or (block_index < 312500 and (not config.TESTNET or not config.REGTEST))
        ):
            problems.append("cannot advance call date")
        if last_issuance["call_price"] > call_price:
            problems.append("cannot reduce call price")
        if issuance_locked and quantity:
            problems.append("locked asset and non‐zero quantity")
        if issuance_locked and reset:
            problems.append("cannot reset a locked asset")
        if (
            util.enabled("lockable_issuance_descriptions", block_index)
            and last_issuance["description_locked"]
        ):
            if description is not None:
                problems.append("Cannot update a locked description")
            if reset:
                problems.append("Cannot reset issuance with locked description")
    else:
        reissuance = False
        if description.lower() == "lock":
            problems.append("cannot lock a non‐existent asset")
        # if destination:
        #    problems.append('cannot transfer a non‐existent asset')
        if reset:
            problems.append("cannot reset a non existent asset")

    # validate parent ownership for subasset
    if subasset_longname is not None and not reissuance:
        parent_issuances = ledger.get_issuances(
            db, asset=subasset_parent, status="valid", first=True
        )
        if parent_issuances:
            last_parent_issuance = parent_issuances[-1]
            if last_parent_issuance["issuer"] != source:
                problems.append("parent asset owned by another address")
        else:
            problems.append("parent asset not found")

    # validate subasset issuance is not a duplicate
    if subasset_longname is not None and not reissuance:
        assets = ledger.get_assets_by_longname(db, subasset_longname)
        if len(assets) > 0:
            problems.append("subasset already exists")

        # validate that the actual asset is numeric
        if asset[0] != "A":
            problems.append("a subasset must be a numeric asset")

    # Check for existence of fee funds.
    if quantity or (block_index >= 315000 or config.TESTNET or config.REGTEST):  # Protocol change.
        if not reissuance or (
            block_index < 310000 and not config.TESTNET and not config.REGTEST
        ):  # Pay fee only upon first issuance. (Protocol change.)
            cursor = db.cursor()
            balance = ledger.get_balance(db, source, config.XCP)
            cursor.close()
            if util.enabled("numeric_asset_names"):  # Protocol change.
                if subasset_longname is not None and util.enabled("subassets"):  # Protocol change.
                    if util.enabled("free_subassets", block_index):
                        fee = 0
                    else:
                        # subasset issuance is 0.25
                        fee = int(0.25 * config.UNIT)
                elif len(asset) >= 13:
                    fee = 0
                else:
                    fee = int(0.5 * config.UNIT)
            elif block_index >= 291700 or config.TESTNET or config.REGTEST:  # Protocol change.
                fee = int(0.5 * config.UNIT)
            elif block_index >= 286000 or config.TESTNET or config.REGTEST:  # Protocol change.
                fee = 5 * config.UNIT
            elif block_index > 281236 or config.TESTNET or config.REGTEST:  # Protocol change.
                fee = 5
            if fee and (balance < fee):
                problems.append("insufficient funds")

    if not (block_index >= 317500 or config.TESTNET or config.REGTEST):  # Protocol change.
        if len(description) > 42:
            problems.append("description too long")

    # For SQLite3
    call_date = min(call_date, config.MAX_INT)
    assert isinstance(quantity, int)
    if reset and util.enabled("cip03", block_index):  # reset will overwrite the quantity
        if quantity > config.MAX_INT:
            problems.append("total quantity overflow")
    else:
        total = sum([issuance["quantity"] for issuance in issuances])
        if total + quantity > config.MAX_INT:
            problems.append("total quantity overflow")

    if util.enabled("cip03", block_index) and reset and issuances:
        # Checking that all supply are held by the owner of the asset
        balances = ledger.get_asset_balances(db, asset)

        if len(balances) == 0:
            if ledger.asset_supply(db, asset) > 0:
                problems.append("Cannot reset an asset with no holder")
        elif len(balances) > 1:
            problems.append("Cannot reset an asset with many holders")
        elif len(balances) == 1:
            if balances[0]["address"] != last_issuance["issuer"]:
                problems.append("Cannot reset an asset held by a different address than the owner")

    # if destination and quantity:
    #    problems.append('cannot issue and transfer simultaneously')

    # For SQLite3
    if util.enabled("integer_overflow_fix", block_index=block_index) and (
        fee > config.MAX_INT or quantity > config.MAX_INT
    ):
        problems.append("integer overflow")

    return (
        call_date,
        call_price,
        problems,
        fee,
        description,
        divisible,
        lock,
        reset,
        reissuance,
        reissued_asset_longname,
    )


def compose(
    db,
    source: str,
    asset: str,
    quantity: int,
    transfer_destination: str = None,
    divisible: bool = None,
    lock: bool = None,
    reset: bool = None,
    description: str = None,
    no_validate=False,
):
    # Callability is deprecated, so for re‐issuances set relevant parameters
    # to old values; for first issuances, make uncallable.
    issuances = ledger.get_issuances(db, asset=asset, status="valid", first=True)
    if issuances:
        last_issuance = issuances[-1]
        callable_ = last_issuance["callable"]
        call_date = last_issuance["call_date"]
        call_price = last_issuance["call_price"]
    else:
        callable_ = False
        call_date = 0
        call_price = 0.0

    # check subasset
    subasset_parent = None
    subasset_longname = None
    if util.enabled("subassets"):  # Protocol change.
        subasset_parent, subasset_longname = util.parse_subasset_from_asset_name(
            asset, util.enabled("allow_subassets_on_numerics")
        )
        if subasset_longname is not None:
            # try to find an existing subasset
            assets = ledger.get_assets_by_longname(db, subasset_longname)
            if len(assets) > 0:
                # this is a reissuance
                asset = assets[0]["asset_name"]
            else:
                # this is a new issuance
                #   generate a random numeric asset id which will map to this subasset
                asset = util.generate_random_asset()

    asset_id = ledger.generate_asset_id(asset, util.CURRENT_BLOCK_INDEX)
    asset_name = ledger.generate_asset_name(
        asset_id, util.CURRENT_BLOCK_INDEX
    )  # This will remove leading zeros in the numeric assets

    (
        call_date,
        call_price,
        problems,
        fee,
        validated_description,
        divisible,
        lock,
        reset,
        reissuance,
        reissued_asset_longname,
    ) = validate(
        db,
        source,
        transfer_destination,
        asset_name,
        quantity,
        divisible,
        lock,
        reset,
        callable_,
        call_date,
        call_price,
        description,
        subasset_parent,
        subasset_longname,
        util.CURRENT_BLOCK_INDEX,
    )
    if problems and not no_validate:
        raise exceptions.ComposeError(problems)

    if subasset_longname is None or reissuance:
        asset_format = util.get_value_by_block_index("issuance_asset_serialization_format")
        asset_format_length = util.get_value_by_block_index("issuance_asset_serialization_length")

        # Type 20 standard issuance FORMAT_2 >QQ??If
        #   used for standard issuances and all reissuances
        if util.enabled("issuance_backwards_compatibility"):
            data = message_type.pack(LR_ISSUANCE_ID)
        else:
            data = message_type.pack(ID)

        if description == None and util.enabled("issuance_description_special_null"):  # noqa: E711
            # a special message is created to be catched by the parse function
            curr_format = (
                asset_format + f"{len(DESCRIPTION_MARK_BYTE) + len(DESCRIPTION_NULL_ACTION)}s"
            )
            encoded_description = DESCRIPTION_MARK_BYTE + DESCRIPTION_NULL_ACTION.encode("utf-8")
        else:
            if (len(validated_description) <= 42) and not util.enabled("pascal_string_removed"):
                curr_format = FORMAT_2 + f"{len(validated_description) + 1}p"
            else:
                curr_format = asset_format + f"{len(validated_description)}s"

            encoded_description = validated_description.encode("utf-8")

        if asset_format_length <= 19:  # callbacks parameters were removed
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if lock else 0,
                1 if reset else 0,
                encoded_description,
            )
        elif asset_format_length <= 26:
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if callable_ else 0,
                call_date or 0,
                call_price or 0.0,
                encoded_description,
            )
        elif asset_format_length <= 27:  # param reset was inserted
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if reset else 0,
                1 if callable_ else 0,
                call_date or 0,
                call_price or 0.0,
                encoded_description,
            )
        elif asset_format_length <= 28:  # param lock was inserted
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if lock else 0,
                1 if reset else 0,
                1 if callable_ else 0,
                call_date or 0,
                call_price or 0.0,
                encoded_description,
            )
    else:
        subasset_format = util.get_value_by_block_index(
            "issuance_subasset_serialization_format", util.CURRENT_BLOCK_INDEX
        )
        subasset_format_length = util.get_value_by_block_index(
            "issuance_subasset_serialization_length", util.CURRENT_BLOCK_INDEX
        )

        # Type 21 subasset issuance SUBASSET_FORMAT >QQ?B
        #   Used only for initial subasset issuance
        # compacts a subasset name to save space
        compacted_subasset_longname = util.compact_subasset_longname(subasset_longname)
        compacted_subasset_length = len(compacted_subasset_longname)
        if util.enabled("issuance_backwards_compatibility"):
            data = message_type.pack(LR_SUBASSET_ID)
        else:
            data = message_type.pack(SUBASSET_ID)

        if description == None and util.enabled("issuance_description_special_null"):  # noqa: E711
            # a special message is created to be catched by the parse function
            curr_format = (
                subasset_format
                + f"{compacted_subasset_length}s"
                + f"{len(DESCRIPTION_MARK_BYTE) + len(DESCRIPTION_NULL_ACTION)}s"
            )
            encoded_description = DESCRIPTION_MARK_BYTE + DESCRIPTION_NULL_ACTION.encode("utf-8")
        else:
            curr_format = (
                subasset_format + f"{compacted_subasset_length}s" + f"{len(validated_description)}s"
            )
            encoded_description = validated_description.encode("utf-8")

        if subasset_format_length <= 18:
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                compacted_subasset_length,
                compacted_subasset_longname,
                encoded_description,
            )
        elif subasset_format_length <= 19:  # param reset was inserted
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if reset else 0,
                compacted_subasset_length,
                compacted_subasset_longname,
                encoded_description,
            )
        elif subasset_format_length <= 20:  # param lock was inserted
            data += struct.pack(
                curr_format,
                asset_id,
                quantity,
                1 if divisible else 0,
                1 if lock else 0,
                1 if reset else 0,
                compacted_subasset_length,
                compacted_subasset_longname,
                encoded_description,
            )

    if transfer_destination:
        destination_outputs = [(transfer_destination, None)]
    else:
        destination_outputs = []
    return (source, destination_outputs, data)


def unpack(db, message, message_type_id, block_index, return_dict=False):
    asset_format = util.get_value_by_block_index("issuance_asset_serialization_format", block_index)
    asset_format_length = util.get_value_by_block_index(
        "issuance_asset_serialization_length", block_index
    )
    subasset_format = util.get_value_by_block_index(
        "issuance_subasset_serialization_format", block_index
    )
    subasset_format_length = util.get_value_by_block_index(
        "issuance_subasset_serialization_length", block_index
    )

    # Unpack message.
    try:
        subasset_longname = None
        if message_type_id == LR_SUBASSET_ID or message_type_id == SUBASSET_ID:
            if not util.enabled("subassets", block_index=block_index):
                logger.warning(f"subassets are not enabled at block {block_index}")
                raise exceptions.UnpackError

            # parse a subasset original issuance message
            lock = None
            reset = None

            if subasset_format_length <= 18:
                asset_id, quantity, divisible, compacted_subasset_length = struct.unpack(
                    subasset_format, message[0:subasset_format_length]
                )
            elif subasset_format_length <= 19:  # param reset was inserted
                asset_id, quantity, divisible, reset, compacted_subasset_length = struct.unpack(
                    subasset_format, message[0:subasset_format_length]
                )
            elif subasset_format_length <= 20:  # param lock was inserted
                asset_id, quantity, divisible, lock, reset, compacted_subasset_length = (
                    struct.unpack(subasset_format, message[0:subasset_format_length])
                )

            description_length = len(message) - subasset_format_length - compacted_subasset_length
            if description_length < 0:
                logger.warning(f"invalid subasset length: {compacted_subasset_length}")
                raise exceptions.UnpackError
            messages_format = f">{compacted_subasset_length}s{description_length}s"
            compacted_subasset_longname, description = struct.unpack(
                messages_format, message[subasset_format_length:]
            )
            subasset_longname = util.expand_subasset_longname(compacted_subasset_longname)
            callable_, call_date, call_price = False, 0, 0.0
            try:
                description = description.decode("utf-8")
            except UnicodeDecodeError:
                description_data = description
                description = ""
                if description_data[0:1] == DESCRIPTION_MARK_BYTE:
                    try:
                        if description_data[1:].decode("utf-8") == DESCRIPTION_NULL_ACTION:
                            description = None
                    except UnicodeDecodeError:
                        description = ""
        elif (block_index > 283271 or config.TESTNET or config.REGTEST) and len(
            message
        ) >= asset_format_length:  # Protocol change.
            if (len(message) - asset_format_length <= 42) and not util.enabled(
                "pascal_string_removed"
            ):
                curr_format = asset_format + f"{len(message) - asset_format_length}p"
            else:
                curr_format = asset_format + f"{len(message) - asset_format_length}s"

            lock = None
            reset = None
            if asset_format_length <= 19:  # callbacks parameters were removed
                asset_id, quantity, divisible, lock, reset, description = struct.unpack(
                    curr_format, message
                )
                callable_, call_date, call_price = False, 0, 0.0
            elif asset_format_length <= 26:  # the reset param didn't even exist
                asset_id, quantity, divisible, callable_, call_date, call_price, description = (
                    struct.unpack(curr_format, message)
                )
            elif asset_format_length <= 27:  # param reset was inserted
                (
                    asset_id,
                    quantity,
                    divisible,
                    reset,
                    callable_,
                    call_date,
                    call_price,
                    description,
                ) = struct.unpack(curr_format, message)
            elif asset_format_length <= 28:  # param lock was inserted
                (
                    asset_id,
                    quantity,
                    divisible,
                    lock,
                    reset,
                    callable_,
                    call_date,
                    call_price,
                    description,
                ) = struct.unpack(curr_format, message)

            call_price = round(call_price, 6)  # TODO: arbitrary
            try:
                description = description.decode("utf-8")
            except UnicodeDecodeError:
                description_data = description
                description = ""
                if description_data[0:1] == DESCRIPTION_MARK_BYTE:
                    try:
                        if description_data[1:].decode("utf-8") == DESCRIPTION_NULL_ACTION:
                            description = None
                    except UnicodeDecodeError:
                        description = ""
        else:
            if len(message) != LENGTH_1:
                raise exceptions.UnpackError
            asset_id, quantity, divisible = struct.unpack(FORMAT_1, message)
            lock, reset, callable_, call_date, call_price, description = (
                False,
                False,
                False,
                0,
                0.0,
                "",
            )
        try:
            asset = ledger.generate_asset_name(asset_id, block_index)

            ##This is for backwards compatibility with assets names longer than 12 characters
            if asset.startswith("A"):
                named_asset = ledger.get_asset_name(db, asset_id, block_index)

                if named_asset != 0:
                    asset = named_asset

            if description == None:  # noqa: E711
                try:
                    description = ledger.get_asset_description(db, asset)
                except exceptions.AssetError:
                    description = ""

            status = "valid"
        except exceptions.AssetIDError:
            asset = None
            status = "invalid: bad asset name"
    except exceptions.UnpackError as e:  # noqa: F841
        (
            asset_id,
            asset,
            subasset_longname,
            quantity,
            divisible,
            lock,
            reset,
            callable_,
            call_date,
            call_price,
            description,
        ) = (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        status = "invalid: could not unpack"

    if return_dict:
        return {
            "asset_id": asset_id,
            "asset": asset,
            "subasset_longname": subasset_longname,
            "quantity": quantity,
            "divisible": divisible,
            "lock": lock,
            "reset": reset,
            "callable": callable_,
            "call_date": call_date,
            "call_price": call_price,
            "description": description,
            "status": status,
        }
    return (
        asset_id,
        asset,
        subasset_longname,
        quantity,
        divisible,
        lock,
        reset,
        callable_,
        call_date,
        call_price,
        description,
        status,
    )


def _get_last_description(db, asset, default):
    issuances = ledger.get_issuances(db, asset=asset, status="valid", first=True)
    if len(issuances) > 0:
        return issuances[-1]["description"]  # Use last description

    return default


def parse(db, tx, message, message_type_id):
    (
        asset_id,
        asset,
        subasset_longname,
        quantity,
        divisible,
        lock,
        reset,
        callable_,
        call_date,
        call_price,
        description,
        status,
    ) = unpack(db, message, message_type_id, tx["block_index"])
    # parse and validate the subasset from the message
    subasset_parent = None
    if status == "valid" and subasset_longname is not None:  # Protocol change.
        try:
            # ensure the subasset_longname is valid
            util.validate_subasset_longname(subasset_longname)
            subasset_parent, subasset_longname = util.parse_subasset_from_asset_name(
                subasset_longname, util.enabled("allow_subassets_on_numerics")
            )
        except exceptions.AssetNameError as e:  # noqa: F841
            asset = None
            status = "invalid: bad subasset name"

    reissuance = None
    fee = 0
    if status == "valid":
        (
            call_date,
            call_price,
            problems,
            fee,
            description,
            divisible,
            lock,
            reset,
            reissuance,
            reissued_asset_longname,
        ) = validate(
            db,
            tx["source"],
            tx["destination"],
            asset,
            quantity,
            divisible,
            lock,
            reset,
            callable_,
            call_date,
            call_price,
            description,
            subasset_parent,
            subasset_longname,
            block_index=tx["block_index"],
        )

        if problems:
            status = "invalid: " + "; ".join(problems)
        if (
            not util.enabled("integer_overflow_fix", block_index=tx["block_index"])
            and "total quantity overflow" in problems
        ):
            quantity = 0

    # Reset?
    if (status == "valid") and reset and util.enabled("cip03", tx["block_index"]):
        balances_result = ledger.get_asset_balances(db, asset)

        if len(balances_result) <= 1:
            if len(balances_result) == 0:
                issuances_result = ledger.get_issuances(db, asset=asset, last=True)

                owner_balance = 0
                owner_address = issuances_result[0]["issuer"]
            else:
                owner_balance = balances_result[0]["quantity"]
                owner_address = balances_result[0]["address"]

            if owner_address == tx["source"]:
                if owner_balance > 0:
                    ledger.debit(
                        db,
                        tx["source"],
                        asset,
                        owner_balance,
                        tx["tx_index"],
                        "reset destroy",
                        tx["tx_hash"],
                    )

                    bindings = {
                        "tx_index": tx["tx_index"],
                        "tx_hash": tx["tx_hash"],
                        "block_index": tx["block_index"],
                        "source": tx["source"],
                        "asset": asset,
                        "quantity": owner_balance,
                        "tag": "reset",
                        "status": "valid",
                    }
                    ledger.insert_record(db, "destructions", bindings, "ASSET_DESTRUCTION")

                bindings = {
                    "tx_index": tx["tx_index"],
                    "tx_hash": tx["tx_hash"],
                    "block_index": tx["block_index"],
                    "asset": asset,
                    "quantity": quantity,
                    "divisible": divisible,
                    "source": tx["source"],
                    "issuer": tx["source"],
                    "transfer": False,
                    "callable": callable_,
                    "call_date": call_date,
                    "call_price": call_price,
                    "description": description,
                    "fee_paid": 0,
                    "locked": lock,
                    "status": status,
                    "reset": True,
                    "asset_longname": reissued_asset_longname,
                }

                ledger.insert_record(db, "issuances", bindings, "RESET_ISSUANCE")

                logger.info("Reset issuance of %(asset)s [%(tx_hash)s] (%(status)s)", bindings)

                # Credit.
                if quantity:
                    ledger.credit(
                        db,
                        tx["source"],
                        asset,
                        quantity,
                        tx["tx_index"],
                        action="reset issuance",
                        event=tx["tx_hash"],
                    )

    else:
        if tx["destination"]:
            issuer = tx["destination"]
            transfer = True
            # quantity = 0
        else:
            issuer = tx["source"]
            transfer = False

        # Debit fee.
        if status == "valid":
            ledger.debit(
                db,
                tx["source"],
                config.XCP,
                fee,
                tx["tx_index"],
                action="issuance fee",
                event=tx["tx_hash"],
            )

        # Lock?
        if not isinstance(lock, bool):
            lock = False

        description_locked = False
        if status == "valid" and description:
            if description.lower() == "lock":
                lock = True
                description = _get_last_description(db, asset, description)
            elif description.lower() == "lock_description" and util.enabled(
                "lockable_issuance_descriptions", tx["block_index"]
            ):
                description_locked = True
                description = _get_last_description(db, asset, description)

        if status == "valid" and not reissuance:
            # Add to table of assets.
            bindings = {
                "asset_id": str(asset_id),
                "asset_name": str(asset),
                "block_index": tx["block_index"],
                "asset_longname": subasset_longname,
            }
            ledger.insert_record(db, "assets", bindings, "ASSET_CREATION")

        if status == "valid" and reissuance:
            # when reissuing, add the asset_longname to the issuances table for API lookups
            asset_longname = reissued_asset_longname
        else:
            asset_longname = subasset_longname

        # Add parsed transaction to message-type–specific table.
        bindings = {
            "tx_index": tx["tx_index"],
            "tx_hash": tx["tx_hash"],
            "block_index": tx["block_index"],
            "asset": asset,
            "quantity": quantity,
            "divisible": divisible,
            "source": tx["source"],
            "issuer": issuer,
            "transfer": transfer,
            "callable": callable_,
            "call_date": call_date,
            "call_price": call_price,
            "description": description,
            "fee_paid": fee,
            "locked": lock,
            "description_locked": description_locked,
            "reset": reset,
            "status": status,
            "asset_longname": asset_longname,
        }
        # ensure last issuance is locked when fair minting is active
        if "cannot issue during fair minting" in status:
            bindings["fair_minting"] = True
        if "integer overflow" not in status:
            ledger.insert_record(db, "issuances", bindings, "ASSET_ISSUANCE")

        logger.info(
            "Issuance of %(quantity)s %(asset)s by %(source)s [%(tx_hash)s] (%(status)s)", bindings
        )

        # Credit.
        if status == "valid" and quantity:
            ledger.credit(
                db,
                tx["source"],
                asset,
                quantity,
                tx["tx_index"],
                action="issuance",
                event=tx["tx_hash"],
            )
