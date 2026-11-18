import queue
import uuid

import stomp

from broker.connection import BrokerConnection
from common.config import RESULT_TOPIC, broker_settings
from common.messages import decode_message


class DashboardListener(stomp.ConnectionListener):
    def __init__(self, events):
        self.events = events

    def on_message(self, frame):
        try:
            self.events.put(("message", decode_message(frame.body)))
        except Exception as error:
            self.events.put(("error", str(error)))

    def on_error(self, frame):
        self.events.put(("error", frame.body))

    def on_disconnected(self):
        self.events.put(("disconnected", "Conexao encerrada"))


class DashboardSubscriber:
    def __init__(self, host=None, port=None, username=None, password=None):
        if host is None:
            host, port, username, password = broker_settings()
        self.events = queue.Queue()
        self.subscription_id = "dashboard-{}".format(uuid.uuid4().hex[:8])
        self.broker = BrokerConnection(
            host, port, username, password,
            client_id=self.subscription_id,
        )

    def connect(self):
        self.broker.connect(DashboardListener(self.events), "dashboard-listener")
        self.broker.subscribe(
            RESULT_TOPIC,
            subscription_id=self.subscription_id,
            ack="auto",
        )

    def disconnect(self):
        self.broker.disconnect()
