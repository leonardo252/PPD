import unittest

from game.board import BLACK, EMPTY, WHITE, Board


class BoardTests(unittest.TestCase):
    def test_initial_position(self):
        board = Board()
        self.assertEqual(board.count(WHITE), 22)
        self.assertEqual(board.count(BLACK), 22)
        self.assertEqual(board.count(EMPTY), 1)

    def test_diagonals_only_exist_on_strong_points(self):
        board = Board()
        self.assertTrue(board.connected((2, 4), (1, 3)))
        self.assertFalse(board.connected((2, 3), (1, 2)))


if __name__ == "__main__":
    unittest.main()
