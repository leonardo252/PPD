import unittest
import threading

try:
    import Pyro5.api
except ImportError:
    Pyro5 = None

from remote.client import PyroGateway
from remote.server import PyroServer
from remote.service import FanoronaService


@unittest.skipIf(Pyro5 is None, "Pyro5 nao instalado")
class PyroIntegrationTests(unittest.TestCase):
    def test_remote_join_chat_and_snapshot(self):
        server = PyroServer(FanoronaService(), "127.0.0.1", 0)
        server.start()
        gateway = PyroGateway("127.0.0.1", server.port)
        try:
            joined = gateway.call("join_game", "Cliente remoto")
            self.assertTrue(joined["success"])
            sent = gateway.call("send_chat", joined["token"], "Ola via Pyro")
            self.assertTrue(sent["success"])
            messages = gateway.call("get_messages", joined["token"], 0)
            self.assertEqual(messages["messages"][0]["text"], "Ola via Pyro")
        finally:
            gateway.close()
            server.close()

    def test_proxy_can_be_used_by_successive_worker_threads(self):
        server = PyroServer(FanoronaService(), "127.0.0.1", 0)
        server.start()
        gateway = PyroGateway("127.0.0.1", server.port)
        errors = []
        results = []

        def run(method, *args):
            try:
                results.append(gateway.call(method, *args))
            except Exception as error:
                errors.append(error)

        try:
            first = threading.Thread(target=run, args=("join_game", "Cliente"))
            first.start()
            first.join()
            self.assertFalse(errors)
            token = results[0]["token"]

            second = threading.Thread(target=run, args=("get_snapshot", token, -1))
            second.start()
            second.join()
            self.assertFalse(errors)
            self.assertTrue(results[1]["success"])
        finally:
            gateway.close()
            server.close()


if __name__ == "__main__":
    unittest.main()
