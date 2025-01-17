import logging

from counterpartycore.lib import config
from counterpartycore.lib.monitors.telemetry.clients.influxdb import TelemetryClientInfluxDB
from counterpartycore.lib.monitors.telemetry.collectors.influxdb import (
    TelemetryCollectorInfluxDB,
)
from counterpartycore.lib.utils.database import LedgerDBConnectionPool
from counterpartycore.lib.utils.helpers import SingletonMeta
from sentry_sdk import capture_exception

logger = logging.getLogger(config.LOGGER_NAME)


class TelemetryOneShot(metaclass=SingletonMeta):
    def __init__(self):
        logger.debug("Initializing TelemetryOneShot")
        self.client = TelemetryClientInfluxDB()

    def submit(self):
        try:
            with LedgerDBConnectionPool().connection() as ledger_db:
                collector = TelemetryCollectorInfluxDB(db=ledger_db)
                data = collector.collect()
                collector.close()
            if data:
                self.client.send(data)
        except Exception as e:
            capture_exception(e)
            logger.warning(f"Error in telemetry one shot: {e}")