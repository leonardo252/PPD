import unittest

from game.board import BLACK, WHITE
from game.game import FanoronaGame


class GameTests(unittest.TestCase):
    def test_initial_piece_count(self):
        game = FanoronaGame()
        self.assertEqual(game.board.count(WHITE), 22)
        self.assertEqual(game.board.count(BLACK), 22)

    def test_initial_turn_has_mandatory_captures(self):
        game = FanoronaGame()
        moves = game.legal_moves()
        self.assertTrue(moves)
        self.assertTrue(all(move[2] for move in moves))


if __name__ == "__main__":
    unittest.main()
