import os
import tempfile
import threading
import unittest

from client.readers import ReaderCoordinator


class ReaderTests(unittest.TestCase):
    def test_two_readers_publish_each_line_once(self):
        handle, path = tempfile.mkstemp(text=True)
        os.close(handle)
        try:
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("um\ndois\ntres\nquatro\ncinco\n")
            published = []
            lock = threading.Lock()
            done = threading.Event()

            def publish(message):
                with lock:
                    published.append(message)

            coordinator = ReaderCoordinator(
                path, "job", ["um"], publish,
                finished=lambda _readers: done.set(),
            )
            coordinator.start()
            self.assertTrue(done.wait(3))
            self.assertEqual(sorted(message["line_number"] for message in published), [1, 2, 3, 4, 5])
            self.assertEqual(len(published), 5)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
