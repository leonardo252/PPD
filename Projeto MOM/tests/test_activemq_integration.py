import os
import queue
import time
import unittest

from broker.connection import BrokerConnection
from common.config import DEFAULT_PASSWORD, DEFAULT_USERNAME
from dashboard.subscriber import DashboardListener


@unittest.skipUnless(os.environ.get("RUN_RABBITMQ_TESTS") == "1", "Requer RabbitMQ local com STOMP")
class RabbitMQIntegrationTests(unittest.TestCase):
    def test_topic_round_trip(self):
        events = queue.Queue()
        subscriber = BrokerConnection("127.0.0.1", 61613, DEFAULT_USERNAME, DEFAULT_PASSWORD)
        producer = BrokerConnection("127.0.0.1", 61613, DEFAULT_USERNAME, DEFAULT_PASSWORD)
        try:
            subscriber.connect(DashboardListener(events), "test-listener")
            subscriber.subscribe("/topic/mom.test", "test-sub")
            producer.connect()
            producer.send_json("/topic/mom.test", {"type": "test", "value": 42}, persistent=False)
            event_type, message = events.get(timeout=5)
            self.assertEqual(event_type, "message")
            self.assertEqual(message["value"], 42)
        finally:
            producer.disconnect()
            subscriber.disconnect()


if __name__ == "__main__":
    unittest.main()
