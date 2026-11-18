LINE_QUEUE = "/queue/mom.keyword.lines"
RESULT_TOPIC = "/topic/mom.keyword.results"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_STOMP_PORT = 61613
DEFAULT_USERNAME = "guest"
DEFAULT_PASSWORD = "guest"
DEFAULT_VHOST = "/"
DEFAULT_LOCAL_WORKERS = 4
MAX_LOCAL_WORKERS = 32

MESSAGE_LINE = "line"
MESSAGE_JOB_STARTED = "job_started"
MESSAGE_JOB_MANIFEST = "job_manifest"
MESSAGE_LINE_RESULT = "line_result"
MESSAGE_WORKER_STARTED = "worker_started"
MESSAGE_WORKER_STOPPED = "worker_stopped"
MESSAGE_WORKER_ERROR = "worker_error"


def broker_settings():
    """Retorna a configuracao unica do RabbitMQ usada por toda a aplicacao."""
    return DEFAULT_HOST, DEFAULT_STOMP_PORT, DEFAULT_USERNAME, DEFAULT_PASSWORD
