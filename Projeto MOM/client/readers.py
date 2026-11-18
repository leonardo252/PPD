import os
import threading

from common.messages import line_message


class ParityReader(threading.Thread):
    """Uma execucao independente para linhas pares ou impares."""

    def __init__(
        self,
        file_path,
        parity,
        job_id,
        keywords,
        publish,
        progress=None,
        finished=None,
        encoding="utf-8",
    ):
        label = "pares" if parity == 0 else "impares"
        super().__init__(name="leitor-{}".format(label), daemon=True)
        self.file_path = file_path
        self.parity = parity
        self.job_id = job_id
        self.keywords = list(keywords)
        self.publish = publish
        self.progress = progress
        self.finished = finished
        self.encoding = encoding
        self.published = 0
        self.error = None

    def run(self):
        try:
            with open(self.file_path, "r", encoding=self.encoding, errors="replace") as stream:
                for line_number, text in enumerate(stream, start=1):
                    if line_number % 2 != self.parity:
                        continue
                    self.publish(
                        line_message(
                            self.job_id,
                            line_number,
                            text.rstrip("\r\n"),
                            self.keywords,
                        )
                    )
                    self.published += 1
                    if self.progress and self.published % 100 == 0:
                        self.progress(self, self.published)
        except Exception as error:
            self.error = error
        finally:
            if self.finished:
                self.finished(self)


class ReaderCoordinator:
    def __init__(self, file_path, job_id, keywords, publish, progress=None, finished=None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        self.lock = threading.Lock()
        self.finished_callback = finished
        self.finished_readers = []
        self.readers = [
            ParityReader(
                file_path, parity, job_id, keywords, publish,
                progress=progress, finished=self._reader_finished,
            )
            for parity in (0, 1)
        ]

    def start(self):
        for reader in self.readers:
            reader.start()

    def _reader_finished(self, reader):
        with self.lock:
            self.finished_readers.append(reader)
            if len(self.finished_readers) == len(self.readers) and self.finished_callback:
                self.finished_callback(list(self.readers))
