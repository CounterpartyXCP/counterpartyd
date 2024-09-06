#! /usr/bin/python3

from counterpartycore.lib import config, database, exceptions, util
from counterpartycore.lib.messages.versions import enhanced_send, mpma, send1

ID = send1.ID


def initialise(db):
    cursor = db.cursor()

    # remove misnamed indexes
    database.drop_indexes(
        cursor,
        [
            "block_index_idx",
            "source_idx",
            "destination_idx",
            "asset_idx",
            "memo_idx",
        ],
    )

    cursor.execute("""CREATE TABLE IF NOT EXISTS sends(
                      tx_index INTEGER PRIMARY KEY,
                      tx_hash TEXT UNIQUE,
                      block_index INTEGER,
                      source TEXT,
                      destination TEXT,
                      asset TEXT,
                      quantity INTEGER,
                      status TEXT,
                      FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index))
                   """)
    columns = [column["name"] for column in cursor.execute("""PRAGMA table_info(sends)""")]

    # If CIP10 activated, Create Sends copy, copy old data, drop old table, rename new table, recreate indexes
    #   SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS` nor can drop UNIQUE constraints
    if "msg_index" not in columns:
        if "memo" not in columns:
            cursor.execute("""CREATE TABLE IF NOT EXISTS new_sends(
                              tx_index INTEGER,
                              tx_hash TEXT,
                              block_index INTEGER,
                              source TEXT,
                              destination TEXT,
                              asset TEXT,
                              quantity INTEGER,
                              status TEXT,
                              msg_index INTEGER DEFAULT 0,
                              PRIMARY KEY (tx_index, msg_index),
                              FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                              UNIQUE (tx_hash, msg_index) ON CONFLICT FAIL)
                           """)
            cursor.execute(
                """INSERT INTO new_sends(tx_index, tx_hash, block_index, source, destination, asset, quantity, status)
                SELECT tx_index, tx_hash, block_index, source, destination, asset, quantity, status
                FROM sends""",
                {},
            )
        else:
            cursor.execute("""CREATE TABLE IF NOT EXISTS new_sends(
                  tx_index INTEGER,
                  tx_hash TEXT,
                  block_index INTEGER,
                  source TEXT,
                  destination TEXT,
                  asset TEXT,
                  quantity INTEGER,
                  status TEXT,
                  memo BLOB,
                  msg_index INTEGER DEFAULT 0,
                  PRIMARY KEY (tx_index, msg_index),
                  FOREIGN KEY (tx_index, tx_hash, block_index) REFERENCES transactions(tx_index, tx_hash, block_index),
                  UNIQUE (tx_hash, msg_index) ON CONFLICT FAIL)
               """)
            cursor.execute(
                """INSERT INTO new_sends (tx_index, tx_hash, block_index, source, destination, asset, quantity, status, memo)
                SELECT tx_index, tx_hash, block_index, source, destination, asset, quantity, status, memo
                FROM sends""",
                {},
            )

        cursor.execute("DROP TABLE sends")
        cursor.execute("ALTER TABLE new_sends RENAME TO sends")

    # Adds a memo to sends
    #   SQLite can’t do `ALTER TABLE IF COLUMN NOT EXISTS`.

    if "memo" not in columns:
        cursor.execute("""ALTER TABLE sends ADD COLUMN memo BLOB""")

    if "fee_paid" not in columns:
        cursor.execute("""ALTER TABLE sends ADD COLUMN fee_paid INTEGER DEFAULT 0""")

    database.create_indexes(
        cursor,
        "sends",
        [
            ["block_index"],
            ["source"],
            ["destination"],
            ["asset"],
            ["memo"],
        ],
    )


def unpack(db, message, block_index):
    return send1.unpack(db, message, block_index)


def validate(db, source, destination, asset, quantity, block_index):
    return send1.validate(db, source, destination, asset, quantity, block_index)


def compose(
    db,
    source: str,
    destination: str,
    asset: str,
    quantity: int,
    memo: str = None,
    memo_is_hex: bool = False,
    use_enhanced_send: bool = None,
    no_validate: bool = False,
):
    # special case - enhanced_send replaces send by default when it is enabled
    #   but it can be explicitly disabled with an API parameter
    if util.enabled("enhanced_sends"):
        # Another special case, if destination, asset and quantity are arrays, it's an MPMA send
        if isinstance(destination, list) and isinstance(asset, list) and isinstance(quantity, list):
            if util.enabled("mpma_sends"):
                if len(destination) == len(asset) and len(asset) == len(quantity):
                    # Sending memos in a MPMA message can be done by several approaches:
                    # 1. Send a list of memos, there must be one for each send and they correspond to the sends by index
                    #   - In this case memo_is_hex should be a list with the same cardinality
                    # 2. Send a dict with the message specific memos and the message wide memo (same for the hex specifier):
                    #   - Each dict should have 2 members:
                    #     + list: same as case (1). An array that specifies the memo for each send
                    #     + msg_wide: the memo for the whole message. This memo will be used for sends that don't have a memo specified. Same as in (3)
                    # 3. Send one memo (either bytes or string) and True/False in memo_is_hex. This will be interpreted as a message wide memo.
                    if len(destination) > config.MPMA_LIMIT:
                        raise exceptions.ComposeError(
                            "mpma sends have a maximum of " + str(config.MPMA_LIMIT) + " sends"
                        )

                    if isinstance(memo, list) and isinstance(memo_is_hex, list):
                        # (1) implemented here
                        if len(memo) != len(memo_is_hex):
                            raise exceptions.ComposeError(
                                "memo and memo_is_hex lists should have the same length"
                            )
                        elif len(memo) != len(destination):
                            raise exceptions.ComposeError(
                                "memo/memo_is_hex lists should have the same length as sends"
                            )

                        return mpma.compose(
                            db,
                            source,
                            util.flat(zip(asset, destination, quantity, memo, memo_is_hex)),
                            None,
                            None,
                            no_validate,
                        )
                    elif isinstance(memo, dict) and isinstance(memo_is_hex, dict):
                        # (2) implemented here
                        if not (
                            "list" in memo
                            and "list" in memo_is_hex
                            and "msg_wide" in memo
                            and "msg_wide" in memo_is_hex
                        ):
                            raise exceptions.ComposeError(
                                'when specifying memo/memo_is_hex as a dict, they must contain keys "list" and "msg_wide"'
                            )
                        elif len(memo["list"]) != len(memo_is_hex["list"]):
                            raise exceptions.ComposeError(
                                "length of memo.list and memo_is_hex.list must be equal"
                            )
                        elif len(memo["list"]) != len(destination):
                            raise exceptions.ComposeError(
                                "length of memo.list/memo_is_hex.list must be equal to the amount of sends"
                            )

                        return mpma.compose(
                            db,
                            source,
                            util.flat(
                                zip(asset, destination, quantity, memo["list"], memo_is_hex["list"])
                            ),
                            memo["msg_wide"],
                            memo_is_hex["msg_wide"],
                            no_validate,
                        )
                    else:
                        # (3) the default case
                        return mpma.compose(
                            db,
                            source,
                            util.flat(zip(asset, destination, quantity)),
                            memo,
                            memo_is_hex,
                            no_validate,
                        )
                else:
                    raise exceptions.ComposeError(
                        "destination, asset and quantity arrays must have the same amount of elements"
                    )
            else:
                raise exceptions.ComposeError("mpma sends are not enabled")
        elif use_enhanced_send is None or use_enhanced_send == True:  # noqa: E712
            return enhanced_send.compose(
                db, source, destination, asset, quantity, memo, memo_is_hex, no_validate
            )
    elif memo is not None or use_enhanced_send == True:  # noqa: E712
        raise exceptions.ComposeError("enhanced sends are not enabled")

    return send1.compose(db, source, destination, asset, quantity, no_validate)


def parse(db, tx, message):  # TODO: *args
    return send1.parse(db, tx, message)
