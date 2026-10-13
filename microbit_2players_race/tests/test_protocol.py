import unittest

from services.protocol import JoinEvent, MoveEvent, ProtocolError, parse_message


class ProtocolTests(unittest.TestCase):
    def test_parses_legacy_join(self):
        self.assertEqual(parse_message("player1"), JoinEvent("player1"))

    def test_parses_legacy_move(self):
        self.assertEqual(parse_message("player_one_3"), MoveEvent("player_one", 3))

    def test_parses_pipe_protocol(self):
        self.assertEqual(parse_message("MOVE|player1|4"), MoveEvent("player1", 4))

    def test_rejects_negative_steps(self):
        with self.assertRaises(ProtocolError):
            parse_message("player1_-1")


if __name__ == "__main__":
    unittest.main()
