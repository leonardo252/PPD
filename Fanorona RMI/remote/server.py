import threading

import Pyro5.api

from remote.client import OBJECT_ID


class PyroServer:
    def __init__(self, service, host, port):
        self.service = service
        self.daemon = Pyro5.api.Daemon(host=host, port=int(port))
        self.port = int(self.daemon.locationStr.rsplit(":", 1)[1])
        self.uri = self.daemon.register(service, objectId=OBJECT_ID)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(
            target=self.daemon.requestLoop,
            name="fanorona-pyro-server",
            daemon=True,
        )
        self.thread.start()
        return str(self.uri)

    def close(self):
        self.daemon.shutdown()
        self.daemon.close()
