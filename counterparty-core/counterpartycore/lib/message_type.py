import logging
import struct
from io import BytesIO

from counterpartycore.lib import config, util

logger = logging.getLogger(config.LOGGER_NAME)


def pack(message_type_id, block_index=None):
    # pack message ID into 1 byte if not zero
    if (
        util.enabled("short_tx_type_id", block_index)
        and message_type_id > 0
        and message_type_id < 256
    ):
        return struct.pack(config.SHORT_TXTYPE_FORMAT, message_type_id)

    # pack into 4 bytes
    return struct.pack(config.TXTYPE_FORMAT, message_type_id)


# retuns both the message type id and the remainder of the message data
def unpack(packed_data, block_index=None):
    message_datas = []

    if util.enabled("new_tx_format"):
        byte_stream = BytesIO(packed_data)
        message_length = util.read_varint(byte_stream)
        while message_length:
            new_data = byte_stream.read(message_length)
            message_datas.append(new_data)
            message_length = util.read_varint(byte_stream)
    else:
        message_datas = [packed_data]

    messages = []

    for message_data in message_datas:
        message_type_id = None
        message_remainder = None

        if len(message_data) > 1:
            # try to read 1 byte first
            if util.enabled("short_tx_type_id", block_index):
                message_type_id = struct.unpack(config.SHORT_TXTYPE_FORMAT, message_data[:1])[0]
                if message_type_id > 0:
                    message_remainder = message_data[1:]
                    messages.append((message_type_id, message_remainder))
                    continue

        # First message byte was 0.  We will read 4 bytes
        if len(message_data) > 4:
            message_type_id = struct.unpack(config.TXTYPE_FORMAT, message_data[:4])[0]
            message_remainder = message_data[4:]

        messages.append((message_type_id, message_remainder))

    return messages
