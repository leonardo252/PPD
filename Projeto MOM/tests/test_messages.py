import unittest

from common.messages import decode_message, encode_message, line_message


class MessageTests(unittest.TestCase):
    def test_round_trip_preserves_accents(self):
        message = line_message("job-1", 7, "computacao distribuida", ["computacao"])
        self.assertEqual(decode_message(encode_message(message)), message)

    def test_rejects_message_without_type(self):
        with self.assertRaises(ValueError):
            decode_message('{"job_id":"x"}')


if __name__ == "__main__":
    unittest.main()
