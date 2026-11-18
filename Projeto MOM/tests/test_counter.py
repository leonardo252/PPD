import unittest

from common.counter import count_keywords, normalize_keywords


class CounterTests(unittest.TestCase):
    def test_normalize_removes_empty_and_duplicates(self):
        self.assertEqual(
            normalize_keywords("Python, activemq; PYTHON, worker, "),
            ["Python", "activemq", "worker"],
        )

    def test_count_is_case_insensitive_and_uses_word_boundaries(self):
        counts = count_keywords(
            "Python python pythonista ActiveMQ. Um worker e outro worker.",
            ["python", "ActiveMQ", "worker"],
        )
        self.assertEqual(counts, {"python": 2, "ActiveMQ": 1, "worker": 2})

    def test_keyword_can_be_a_phrase(self):
        self.assertEqual(count_keywords("message broker e message broker", ["message broker"]), {"message broker": 2})


if __name__ == "__main__":
    unittest.main()
