import argparse
import signal
import threading

from workers.counter_worker import CounterWorker


def parse_args():
    parser = argparse.ArgumentParser(description="Worker contador do Projeto MOM")
    parser.add_argument("--id", dest="worker_id")
    return parser.parse_args()


def main():
    args = parse_args()
    worker = CounterWorker(worker_id=args.worker_id)
    stopped = threading.Event()

    def stop(_signal=None, _frame=None):
        stopped.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    worker.start()
    print("Worker {} conectado. Pressione Ctrl+C para encerrar.".format(worker.worker_id))
    try:
        stopped.wait()
    finally:
        worker.stop()


if __name__ == "__main__":
    main()
