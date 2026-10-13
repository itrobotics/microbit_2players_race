import random
from collections.abc import Callable

from config import (
    COMPUTER_PLAYER_ID,
    COMPUTER_STEPS_MAX,
    COMPUTER_STEPS_MIN,
    DISTANCE_PER_STEP,
    MAX_PLAYERS,
    MAX_STEPS_PER_MESSAGE,
    RACE_DISTANCE,
)
from models import GameState, Player


class GameController:
    """Owns game rules and data. It has no Tkinter or serial dependency."""

    def __init__(
        self,
        on_change: Callable[[], None] | None = None,
        on_finish: Callable[[Player], None] | None = None,
        race_distance: int = RACE_DISTANCE,
        distance_per_step: int = DISTANCE_PER_STEP,
        max_players: int = MAX_PLAYERS,
    ) -> None:
        self.players: dict[str, Player] = {}
        self.state = GameState.WAITING
        self.winner_id: str | None = None
        self.race_distance = race_distance
        self.distance_per_step = distance_per_step
        self.max_players = max_players
        self._on_change = on_change or (lambda: None)
        self._on_finish = on_finish or (lambda _player: None)

    def add_player(self, device_id: str, *, is_computer: bool = False) -> bool:
        device_id = device_id.strip()
        if not device_id or device_id in self.players:
            return False
        if self.state not in (GameState.WAITING, GameState.FINISHED):
            return False
        if len(self.players) >= self.max_players:
            return False

        self.players[device_id] = Player(
            device_id=device_id,
            display_name=device_id,
            lane=len(self.players),
            is_computer=is_computer,
        )
        self._reassign_lanes()
        self._on_change()
        return True

    def prepare_race(self) -> tuple[bool, str | None]:
        if self.state not in (GameState.WAITING, GameState.FINISHED):
            return False, "The race is already in progress."

        self.players.pop(COMPUTER_PLAYER_ID, None)
        physical_players = [p for p in self.players.values() if not p.is_computer]
        if not physical_players:
            return False, "No player is connected."

        if len(physical_players) == 1:
            self.add_player(COMPUTER_PLAYER_ID, is_computer=True)

        for player in self.players.values():
            player.distance = 0

        self._reassign_lanes()
        self.winner_id = None
        self.state = GameState.COUNTDOWN
        self._on_change()
        return True, None

    def begin_race(self) -> bool:
        if self.state != GameState.COUNTDOWN:
            return False
        self.state = GameState.RACING
        self._on_change()
        return True

    def move_player(self, device_id: str, steps: int) -> bool:
        if self.state != GameState.RACING or device_id not in self.players:
            return False
        if steps < 0 or steps > MAX_STEPS_PER_MESSAGE:
            return False

        player = self.players[device_id]
        player.distance = min(
            self.race_distance,
            player.distance + steps * self.distance_per_step,
        )

        if player.distance >= self.race_distance:
            self.state = GameState.FINISHED
            self.winner_id = player.device_id
            self._on_change()
            self._on_finish(player)
            return True

        self._on_change()
        return True

    def move_computer(self) -> bool:
        if self.state != GameState.RACING or COMPUTER_PLAYER_ID not in self.players:
            return False
        steps = random.randint(COMPUTER_STEPS_MIN, COMPUTER_STEPS_MAX)
        return self.move_player(COMPUTER_PLAYER_ID, steps)

    def reset(self, *, clear_players: bool = True) -> None:
        self.state = GameState.WAITING
        self.winner_id = None
        if clear_players:
            self.players.clear()
        else:
            self.players.pop(COMPUTER_PLAYER_ID, None)
            for player in self.players.values():
                player.distance = 0
            self._reassign_lanes()
        self._on_change()

    def _reassign_lanes(self) -> None:
        for lane, player in enumerate(self.players.values()):
            player.lane = lane
