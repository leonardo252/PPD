import threading

import stomp

from common.config import DEFAULT_VHOST
from common.messages import encode_message


class BrokerConnection:
    def __init__(self, host, port, username, password, client_id=None):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.client_id = client_id
        self.connection = stomp.Connection12(
            [(host, int(port))],
            heartbeats=(10000, 10000),
            keepalive=True,
            vhost=DEFAULT_VHOST,
        )
        self.send_lock = threading.Lock()

    @property
    def connected(self):
        return self.connection.is_connected()

    def connect(self, listener=None, listener_name="application"):
        if listener is not None:
            self.connection.set_listener(listener_name, listener)
        headers = {}
        if self.client_id:
            headers["client-id"] = self.client_id
        self.connection.connect(
            login=self.username,
            passcode=self.password,
            wait=True,
            headers=headers,
        )

    def send_json(self, destination, message, persistent=True):
        headers = {
            "content-type": "application/json;charset=utf-8",
            "persistent": "true" if persistent else "false",
        }
        with self.send_lock:
            self.connection.send(
                destination=destination,
                body=encode_message(message),
                headers=headers,
            )

    def subscribe(self, destination, subscription_id, ack="auto", prefetch=None):
        headers = {}
        if prefetch is not None:
            headers["prefetch-count"] = str(prefetch)
        self.connection.subscribe(
            destination=destination,
            id=subscription_id,
            ack=ack,
            headers=headers,
        )

    def ack(self, frame):
        message_id = frame.headers.get("ack") or frame.headers.get("message-id")
        self.connection.ack(id=message_id)

    def nack(self, frame):
        message_id = frame.headers.get("ack") or frame.headers.get("message-id")
        self.connection.nack(id=message_id)

    def disconnect(self):
        if self.connected:
            self.connection.disconnect()
