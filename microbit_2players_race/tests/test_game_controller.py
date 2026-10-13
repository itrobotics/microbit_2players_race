import unittest

from controllers import GameController
from models import GameState


class GameControllerTests(unittest.TestCase):
    def test_duplicate_player_is_not_added(self):
        controller = GameController()
        self.assertTrue(controller.add_player("p1"))
        self.assertFalse(controller.add_player("p1"))
        self.assertEqual(len(controller.players), 1)

    def test_single_player_gets_computer_opponent(self):
        controller = GameController()
        controller.add_player("p1")
        started, _ = controller.prepare_race()
        self.assertTrue(started)
        self.assertIn("Computer", controller.players)
        self.assertEqual(controller.state, GameState.COUNTDOWN)

    def test_steps_during_countdown_are_ignored(self):
        controller = GameController()
        controller.add_player("p1")
        controller.prepare_race()
        self.assertFalse(controller.move_player("p1", 5))
        self.assertEqual(controller.players["p1"].distance, 0)

    def test_first_player_to_distance_wins_once(self):
        winners = []
        controller = GameController(
            on_finish=lambda player: winners.append(player.device_id),
            race_distance=100,
            distance_per_step=10,
        )
        controller.add_player("p1")
        controller.add_player("p2")
        controller.prepare_race()
        controller.begin_race()
        controller.move_player("p1", 10)
        controller.move_player("p2", 10)

        self.assertEqual(controller.state, GameState.FINISHED)
        self.assertEqual(controller.winner_id, "p1")
        self.assertEqual(winners, ["p1"])


if __name__ == "__main__":
    unittest.main()
