import json
import time
import uuid

from common.config import (
    MESSAGE_JOB_MANIFEST,
    MESSAGE_JOB_STARTED,
    MESSAGE_LINE,
    MESSAGE_LINE_RESULT,
    MESSAGE_WORKER_ERROR,
    MESSAGE_WORKER_STARTED,
    MESSAGE_WORKER_STOPPED,
)


def new_job_id():
    return uuid.uuid4().hex


def encode_message(message):
    return json.dumps(message, ensure_ascii=False, separators=(",", ":"))


def decode_message(body):
    message = json.loads(body)
    if not isinstance(message, dict) or "type" not in message:
        raise ValueError("Mensagem MOM sem campo type.")
    return message


def job_started(job_id, file_name, keywords):
    return {
        "type": MESSAGE_JOB_STARTED,
        "job_id": job_id,
        "file_name": file_name,
        "keywords": list(keywords),
        "started_at": time.time(),
    }


def line_message(job_id, line_number, text, keywords):
    return {
        "type": MESSAGE_LINE,
        "job_id": job_id,
        "line_number": int(line_number),
        "text": text,
        "keywords": list(keywords),
    }


def job_manifest(job_id, total_lines, even_lines, odd_lines):
    return {
        "type": MESSAGE_JOB_MANIFEST,
        "job_id": job_id,
        "total_lines": int(total_lines),
        "even_lines": int(even_lines),
        "odd_lines": int(odd_lines),
        "published_at": time.time(),
    }


def line_result(job_id, line_number, counts, worker_id):
    return {
        "type": MESSAGE_LINE_RESULT,
        "job_id": job_id,
        "line_number": int(line_number),
        "counts": dict(counts),
        "worker_id": worker_id,
        "processed_at": time.time(),
    }


def worker_event(event_type, worker_id, detail=None):
    if event_type not in (MESSAGE_WORKER_STARTED, MESSAGE_WORKER_STOPPED, MESSAGE_WORKER_ERROR):
        raise ValueError("Tipo de evento de worker invalido.")
    message = {
        "type": event_type,
        "worker_id": worker_id,
        "timestamp": time.time(),
    }
    if detail:
        message["detail"] = str(detail)
    return message
