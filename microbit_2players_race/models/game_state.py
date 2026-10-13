from enum import Enum, auto


class GameState(Enum):
    WAITING = auto()
    COUNTDOWN = auto()
    RACING = auto()
    FINISHED = auto()
