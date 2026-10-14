import threading

import Pyro5.api
import Pyro5.errors


OBJECT_ID = "fanorona.game"


class LocalGateway:
    """Usa o mesmo contrato remoto para a interface que hospeda a partida."""

    def __init__(self, service):
        self.service = service

    def call(self, method, *args):
        return getattr(self.service, method)(*args)

    def close(self):
        pass


class PyroGateway:
    """Proxy Pyro protegido e transferido para a thread de cada chamada."""

    def __init__(self, host, port):
        uri = "PYRO:{}@{}:{}".format(OBJECT_ID, host, int(port))
        self.proxy = Pyro5.api.Proxy(uri)
        self.lock = threading.Lock()
        with self.lock:
            self.proxy._pyroBind()
            self.proxy.ping()

    def call(self, method, *args):
        with self.lock:
            # O Tkinter cria workers curtos para nao travar a interface. Pyro5
            # associa o Proxy a thread que o usou por ultimo; portanto, alem
            # de serializar as chamadas, e preciso transferir sua propriedade.
            self.proxy._pyroClaimOwnership()
            return getattr(self.proxy, method)(*args)

    def close(self):
        with self.lock:
            self.proxy._pyroClaimOwnership()
            self.proxy._pyroRelease()
