import unittest

from game.board import BLACK, WHITE
from remote.service import FanoronaService


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = FanoronaService()
        self.white = self.service.join_game("Ana")
        self.black = self.service.join_game("Bruno")

    def test_assigns_colors_and_starts_with_two_players(self):
        self.assertEqual(self.white["color"], WHITE)
        self.assertEqual(self.black["color"], BLACK)
        self.assertTrue(self.black["snapshot"]["started"])

    def test_rejects_third_player(self):
        response = self.service.join_game("Carlos")
        self.assertFalse(response["success"])

    def test_rejects_move_out_of_turn(self):
        response = self.service.make_move(
            self.black["token"], [1, 0], [2, 0], "approach"
        )
        self.assertFalse(response["success"])
        self.assertIn("turno", response["error"])

    def test_chat_returns_only_user_messages(self):
        token = self.white["token"]
        sent = self.service.send_chat(token, "Boa partida!")
        received = self.service.get_messages(self.black["token"], 0)
        self.assertTrue(sent["success"])
        self.assertEqual(len(received["messages"]), 1)
        self.assertEqual(received["messages"][0]["text"], "Boa partida!")

    def test_snapshot_version_avoids_retransmission(self):
        token = self.white["token"]
        version = self.service.get_snapshot(token)["snapshot"]["version"]
        response = self.service.get_snapshot(token, version)
        self.assertFalse(response["changed"])

    def test_surrender_sets_winner(self):
        response = self.service.surrender(self.black["token"])
        self.assertEqual(response["snapshot"]["game"]["winner"], WHITE)


if __name__ == "__main__":
    unittest.main()
