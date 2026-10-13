from dataclasses import dataclass


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class JoinEvent:
    device_id: str


@dataclass(frozen=True)
class MoveEvent:
    device_id: str
    steps: int


def parse_message(message: str) -> JoinEvent | MoveEvent:
    """Parse both the original underscore protocol and the newer pipe format."""
    message = message.strip()
    if not message:
        raise ProtocolError("Empty message")

    if "|" in message:
        fields = message.split("|")
        command = fields[0].upper()
        if command == "JOIN" and len(fields) == 2 and fields[1]:
            return JoinEvent(fields[1])
        if command == "MOVE" and len(fields) == 3 and fields[1]:
            return MoveEvent(fields[1], _parse_steps(fields[2]))
        raise ProtocolError(f"Invalid protocol message: {message!r}")

    if "_" not in message:
        return JoinEvent(message)

    device_id, raw_steps = message.rsplit("_", maxsplit=1)
    if not device_id:
        raise ProtocolError("Missing device ID")
    return MoveEvent(device_id, _parse_steps(raw_steps))


def _parse_steps(raw_steps: str) -> int:
    if raw_steps == "":
        return 0
    try:
        steps = int(raw_steps)
    except ValueError as exc:
        raise ProtocolError(f"Invalid step count: {raw_steps!r}") from exc
    if steps < 0:
        raise ProtocolError("Step count cannot be negative")
    return steps


def encode_join_ack(device_id: str) -> str:
    return f"{device_id}_connect ok\n"


def encode_finish(device_id: str) -> str:
    return f"{device_id}_finish\n"


def encode_reset() -> str:
    return "reset\n"
