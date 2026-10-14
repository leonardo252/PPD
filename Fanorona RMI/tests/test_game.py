import unittest

from game.board import BLACK, EMPTY, WHITE, Board
from game.game import FanoronaGame, InvalidMove


class GameTests(unittest.TestCase):
    def test_initial_moves_are_captures(self):
        game = FanoronaGame()
        moves = game.legal_moves()
        self.assertTrue(moves)
        self.assertTrue(all(move[2] for move in moves))

    def test_approach_capture(self):
        game = FanoronaGame()
        cells = [[EMPTY] * 9 for _ in range(5)]
        cells[2][2] = WHITE
        cells[2][4] = BLACK
        cells[2][5] = BLACK
        game.board = Board(cells)
        captured = game.move((2, 2), (2, 3), "approach")
        self.assertEqual(captured, [(2, 4), (2, 5)])
        self.assertEqual(game.board.count(BLACK), 0)
        self.assertEqual(game.winner, WHITE)

    def test_invalid_non_capture_when_capture_exists(self):
        game = FanoronaGame()
        with self.assertRaises(InvalidMove):
            game.move((4, 0), (3, 1))

    def test_state_round_trip_preserves_sequence(self):
        source = FanoronaGame()
        source.chain_position = (2, 4)
        source.visited = {(2, 3), (2, 4)}
        target = FanoronaGame()
        target.load_state(source.state())
        self.assertEqual(target.chain_position, (2, 4))
        self.assertEqual(target.visited, {(2, 3), (2, 4)})


if __name__ == "__main__":
    unittest.main()
