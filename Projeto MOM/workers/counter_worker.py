import socket
import uuid

import stomp

from broker.connection import BrokerConnection
from common.config import (
    LINE_QUEUE,
    MESSAGE_LINE,
    MESSAGE_WORKER_ERROR,
    MESSAGE_WORKER_STARTED,
    MESSAGE_WORKER_STOPPED,
    RESULT_TOPIC,
    broker_settings,
)
from common.counter import count_keywords
from common.messages import decode_message, line_result, worker_event


class WorkerListener(stomp.ConnectionListener):
    def __init__(self, worker):
        self.worker = worker

    def on_message(self, frame):
        self.worker.handle_frame(frame)

    def on_error(self, frame):
        self.worker.last_error = frame.body

    def on_disconnected(self):
        self.worker.connected = False


class CounterWorker:
    def __init__(self, host=None, port=None, username=None, password=None, worker_id=None):
        if host is None:
            host, port, username, password = broker_settings()
        self.worker_id = worker_id or "{}-{}".format(socket.gethostname(), uuid.uuid4().hex[:8])
        self.broker = BrokerConnection(
            host, port, username, password,
            client_id="worker-{}".format(self.worker_id),
        )
        self.connected = False
        self.processed = 0
        self.last_error = None

    def start(self):
        self.broker.connect(WorkerListener(self), "worker-listener")
        self.broker.subscribe(
            LINE_QUEUE,
            subscription_id="sub-{}".format(self.worker_id),
            ack="client-individual",
            prefetch=1,
        )
        self.connected = True
        self.broker.send_json(
            RESULT_TOPIC,
            worker_event(MESSAGE_WORKER_STARTED, self.worker_id),
            persistent=False,
        )

    def handle_frame(self, frame):
        try:
            message = decode_message(frame.body)
            if message.get("type") != MESSAGE_LINE:
                self.broker.ack(frame)
                return
            counts = count_keywords(message.get("text", ""), message.get("keywords", []))
            result = line_result(
                message["job_id"],
                message["line_number"],
                counts,
                self.worker_id,
            )
            self.broker.send_json(RESULT_TOPIC, result, persistent=True)
            self.broker.ack(frame)
            self.processed += 1
        except (ValueError, KeyError) as error:
            self.last_error = str(error)
            self.broker.send_json(
                RESULT_TOPIC,
                worker_event(MESSAGE_WORKER_ERROR, self.worker_id, error),
                persistent=False,
            )
            self.broker.ack(frame)
        except Exception as error:
            self.last_error = str(error)
            self.broker.nack(frame)

    def stop(self):
        if self.broker.connected:
            try:
                self.broker.send_json(
                    RESULT_TOPIC,
                    worker_event(MESSAGE_WORKER_STOPPED, self.worker_id),
                    persistent=False,
                )
            finally:
                self.broker.disconnect()
        self.connected = False
