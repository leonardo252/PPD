import os

from broker.connection import BrokerConnection
from client.readers import ReaderCoordinator
from common.config import LINE_QUEUE, RESULT_TOPIC, broker_settings
from common.messages import job_manifest, job_started, new_job_id
from workers.counter_worker import CounterWorker


class ClientController:
    def __init__(self, host=None, port=None, username=None, password=None):
        if host is None:
            host, port, username, password = broker_settings()
        self.broker = BrokerConnection(host, port, username, password, client_id="mom-client")
        self.workers = []
        self.coordinator = None
        self.current_job_id = None
        self.on_progress = None
        self.on_finished = None

    def connect(self):
        self.broker.connect()

    def start_local_workers(self, count):
        for index in range(int(count)):
            worker = CounterWorker(
                self.broker.host,
                self.broker.port,
                self.broker.username,
                self.broker.password,
                worker_id="local-worker-{}".format(index + 1),
            )
            worker.start()
            self.workers.append(worker)

    def start_job(self, file_path, keywords):
        if self.coordinator is not None:
            raise RuntimeError("Ja existe uma leitura em andamento.")
        job_id = new_job_id()
        self.current_job_id = job_id
        self.broker.send_json(
            RESULT_TOPIC,
            job_started(job_id, os.path.basename(file_path), keywords),
            persistent=False,
        )
        self.coordinator = ReaderCoordinator(
            file_path=file_path,
            job_id=job_id,
            keywords=keywords,
            publish=lambda message: self.broker.send_json(LINE_QUEUE, message, persistent=True),
            progress=self._progress,
            finished=self._finished,
        )
        self.coordinator.start()
        return job_id

    def _progress(self, reader, count):
        if self.on_progress:
            self.on_progress(reader.name, count)

    def _finished(self, readers):
        errors = [reader.error for reader in readers if reader.error]
        even = next(reader.published for reader in readers if reader.parity == 0)
        odd = next(reader.published for reader in readers if reader.parity == 1)
        if not errors:
            self.broker.send_json(
                RESULT_TOPIC,
                job_manifest(self.current_job_id, even + odd, even, odd),
                persistent=False,
            )
        self.coordinator = None
        if self.on_finished:
            self.on_finished(even, odd, errors)

    def close(self):
        for worker in self.workers:
            worker.stop()
        self.workers.clear()
        self.broker.disconnect()
