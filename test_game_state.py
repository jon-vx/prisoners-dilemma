import unittest
from contextlib import redirect_stdout
from io import StringIO

from game_state import Game
from player import Unconditional_Coopearator, Unconditional_Defector


class GameLifecycleTests(unittest.TestCase):
    def make_game(self, rounds):
        return Game(
            Unconditional_Coopearator(rounds),
            Unconditional_Defector(rounds),
            rounds,
        )

    def play_silently(self, game):
        with redirect_stdout(StringIO()):
            return game.play_round()

    def test_round_count_must_be_positive(self):
        with self.assertRaises(ValueError):
            Game(Unconditional_Coopearator(1), Unconditional_Defector(1), 0)
        with self.assertRaises(ValueError):
            Game(Unconditional_Coopearator(1), Unconditional_Defector(1), -1)

    def test_round_count_must_be_an_integer(self):
        with self.assertRaises(TypeError):
            Game(Unconditional_Coopearator(1), Unconditional_Defector(1), 1.5)
        with self.assertRaises(TypeError):
            Game(Unconditional_Coopearator(1), Unconditional_Defector(1), True)

    def test_one_round_game_finishes_after_first_round(self):
        game = self.make_game(1)

        self.assertTrue(self.play_silently(game))
        self.assertTrue(game.game_over)
        self.assertEqual(game.current_round, 2)
        self.assertEqual(game.return_player_scores(), (10, 0))

    def test_playing_after_completion_is_safe_and_does_not_mutate_state(self):
        game = self.make_game(2)
        self.assertFalse(self.play_silently(game))
        self.assertTrue(self.play_silently(game))
        state = (
            game.current_round,
            game.return_player_scores(),
            game.p1_scores.copy(),
            game.p2_scores.copy(),
        )

        self.assertTrue(self.play_silently(game))
        self.assertEqual(game.current_round, state[0])
        self.assertEqual(game.return_player_scores(), state[1])
        self.assertTrue((game.p1_scores == state[2]).all())
        self.assertTrue((game.p2_scores == state[3]).all())


if __name__ == "__main__":
    unittest.main()
