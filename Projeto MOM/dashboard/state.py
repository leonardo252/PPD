import time

from common.config import (
    MESSAGE_JOB_MANIFEST,
    MESSAGE_JOB_STARTED,
    MESSAGE_LINE_RESULT,
    MESSAGE_WORKER_ERROR,
    MESSAGE_WORKER_STARTED,
    MESSAGE_WORKER_STOPPED,
)


class JobState:
    def __init__(self, job_id):
        self.job_id = job_id
        self.file_name = ""
        self.keywords = []
        self.totals = {}
        self.processed_lines = set()
        self.total_lines = None
        self.even_lines = 0
        self.odd_lines = 0
        self.workers_seen = set()
        self.started_at = time.time()
        self.last_update = self.started_at

    @property
    def processed_count(self):
        return len(self.processed_lines)

    @property
    def complete(self):
        return self.total_lines is not None and self.processed_count >= self.total_lines

    @property
    def progress(self):
        if not self.total_lines:
            return 0.0
        return min(100.0, self.processed_count * 100.0 / self.total_lines)

    @property
    def elapsed(self):
        return max(0.0, self.last_update - self.started_at)


class DashboardState:
    """Agregador idempotente dos eventos recebidos pelo topico."""

    def __init__(self):
        self.jobs = {}
        self.active_job_id = None
        self.active_workers = set()
        self.worker_errors = []

    @property
    def active_job(self):
        return self.jobs.get(self.active_job_id)

    def apply(self, message):
        message_type = message.get("type")
        if message_type == MESSAGE_WORKER_STARTED:
            self.active_workers.add(message["worker_id"])
            return True
        if message_type == MESSAGE_WORKER_STOPPED:
            self.active_workers.discard(message["worker_id"])
            return True
        if message_type == MESSAGE_WORKER_ERROR:
            self.worker_errors.append(message)
            return True

        job_id = message.get("job_id")
        if not job_id:
            return False
        state = self.jobs.setdefault(job_id, JobState(job_id))

        if message_type == MESSAGE_JOB_STARTED:
            state.file_name = message.get("file_name", "")
            announced = list(message.get("keywords", []))
            state.keywords = list(dict.fromkeys(announced + state.keywords))
            for keyword in state.keywords:
                state.totals.setdefault(keyword, 0)
            state.started_at = float(message.get("started_at", time.time()))
            state.last_update = time.time()
            self.active_job_id = job_id
            return True

        if message_type == MESSAGE_JOB_MANIFEST:
            state.total_lines = int(message.get("total_lines", 0))
            state.even_lines = int(message.get("even_lines", 0))
            state.odd_lines = int(message.get("odd_lines", 0))
            state.last_update = time.time()
            self.active_job_id = job_id
            return True

        if message_type == MESSAGE_LINE_RESULT:
            line_number = int(message["line_number"])
            if line_number in state.processed_lines:
                return False
            state.processed_lines.add(line_number)
            for keyword, value in message.get("counts", {}).items():
                if keyword not in state.keywords:
                    state.keywords.append(keyword)
                state.totals[keyword] = state.totals.get(keyword, 0) + int(value)
            worker_id = message.get("worker_id")
            if worker_id:
                state.workers_seen.add(worker_id)
            state.last_update = time.time()
            self.active_job_id = job_id
            return True

        return False
