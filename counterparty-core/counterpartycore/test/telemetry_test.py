import time
from unittest.mock import MagicMock, patch

from counterpartycore.lib.telemetry.collectors.base import TelemetryCollectorBase
from counterpartycore.lib.telemetry.daemon import TelemetryDaemon


class TestTelemetryDaemon:
    def test_init(self):
        collector = MagicMock()
        client = MagicMock()
        daemon = TelemetryDaemon(collector, client)
        assert daemon.client == client
        assert daemon.collector == collector
        assert daemon.interval == 60

    def test_init_with_custom_interval(self):
        collector = MagicMock()
        client = MagicMock()
        daemon = TelemetryDaemon(collector, client, interval=10)
        assert daemon.client == client
        assert daemon.collector == collector
        assert daemon.interval == 10

    def test_send_at_intervals(self):
        collector = MagicMock()
        client = MagicMock()
        daemon = TelemetryDaemon(collector, client, interval=0.5)
        daemon.start()
        assert daemon.is_running == True  # noqa: E712
        time.sleep(2)
        daemon.stop()
        assert daemon.is_running == False  # noqa: E712
        assert client.send.call_count > 1
        assert collector.collect.call_count > 1


class TestTelemetryCollectorBase:
    @patch("counterpartycore.lib.telemetry.util.config")
    @patch("counterpartycore.lib.telemetry.collectors.base.ledger")
    def test_collect(self, mock_ledger, mock_config):
        mock_db = MagicMock()
        mock_ledger.last_message.return_value = {"block_index": 12345}
        mock_config.__version__ = "1.2.3"
        mock_config.TESTNET3 = False
        mock_config.TESTNET4 = False
        mock_config.FORCE = False

        collector = TelemetryCollectorBase(mock_db)
        time.sleep(0.1)
        data = collector.collect()

        print("\n\n\n", data)

        mock_ledger.last_message.assert_called_with(mock_db)
        mock_db.cursor().execute.assert_called_with(
            "SELECT * FROM blocks where block_index = ?", [12345]
        )

        assert data["version"] == "1.2.3"
        assert data["uptime"] > 0
        assert data["network"] == "MAINNET"
        assert isinstance(data["dockerized"], bool)  # noqa: E712
        assert data["force_enabled"] == False  # noqa: E712

    @patch("counterpartycore.lib.telemetry.collectors.base.ledger")
    @patch("counterpartycore.lib.telemetry.collectors.base.os.path.exists")
    def test_collect_with_docker(self, mock_exists, mock_ledger):
        mock_db = MagicMock()
        mock_exists.return_value = True
        mock_ledger.last_message.return_value = {"block_index": 12345}
        collector = TelemetryCollectorBase(mock_db)
        data = collector.collect()
        assert data["dockerized"] == True  # noqa: E712
