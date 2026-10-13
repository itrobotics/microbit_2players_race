from dataclasses import dataclass


@dataclass
class Player:
    device_id: str
    display_name: str
    lane: int
    distance: int = 0
    connected: bool = True
    is_computer: bool = False
