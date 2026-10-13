import argparse
import tkinter as tk
from queue import Empty, Queue

from config import (
    AUDIO_DIR,
    COMPUTER_TICK_MS,
    COUNTDOWN_SECONDS,
    SERIAL_POLL_INTERVAL_MS,
)
from controllers import GameController
from services import (
    JoinEvent,
    MoveEvent,
    ProtocolError,
    SerialError,
    SerialLine,
    SerialManager,
    parse_message,
)
from services.audio_manager import AudioManager
from services.protocol import encode_finish, encode_join_ack, encode_reset
from views import GameView


class GameApplication:
    """Coordinates serial data from the receiver micro:bit with game/UI events."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        port: str | None = None,
        fullscreen: bool = True,
        demo: bool = False,
    ) -> None:
        self.root = root
        self.demo = demo
        self.event_queue: Queue = Queue()
        self.audio = AudioManager()
        self.serial = None if demo else SerialManager(self.event_queue, port=port)
        self.controller = GameController(
            on_change=self._render,
            on_finish=self._handle_finish,
        )
        self.view = GameView(
            root,
            on_start=self.start_race,
            on_reset=self.reset,
            on_exit=self.close,
            fullscreen=fullscreen,
        )

    def run(self) -> None:
        if self.demo:
            self.controller.add_player("Demo player")
            self.view.set_connection_message("Demo mode")
        else:
            assert self.serial is not None
            try:
                port_name = self.serial.open()
                self.serial.start()
                self.view.set_connection_message(f"Connected: {port_name}")
            except Exception as exc:
                self.view.show_error(str(exc))
                self.close()
                return

        self.root.after(SERIAL_POLL_INTERVAL_MS, self._process_serial_events)
        self.root.after(COMPUTER_TICK_MS, self._computer_tick)
        self.root.mainloop()

    def start_race(self) -> None:
        started, error = self.controller.prepare_race()
        if not started:
            self.view.show_error(error or "The race cannot start.")
            return
        self.view.start_countdown(
            COUNTDOWN_SECONDS,
            on_complete=self.controller.begin_race,
            on_tick=lambda: self.audio.play(AUDIO_DIR / "counter.mp3"),
        )

    def reset(self) -> None:
        self.view.cancel_countdown()
        self.controller.reset(clear_players=True)
        if self.serial:
            self.serial.send(encode_reset())

    def close(self) -> None:
        self.view.cancel_countdown()
        if self.serial:
            self.serial.close()
        self.audio.close()
        if self.root.winfo_exists():
            self.root.destroy()

    def _render(self) -> None:
        if not hasattr(self, "view"):
            return
        self.view.render(
            self.controller.players.values(),
            self.controller.state,
            self.controller.winner_id,
        )

    def _handle_finish(self, player) -> None:
        self.audio.play(AUDIO_DIR / "win.mp3")
        if self.serial:
            self.serial.send(encode_finish(player.device_id))

    def _process_serial_events(self) -> None:
        try:
            while True:
                event = self.event_queue.get_nowait()
                if isinstance(event, SerialError):
                    self.view.show_error(f"Serial connection lost: {event.message}")
                    continue
                if isinstance(event, SerialLine):
                    self._handle_serial_line(event.text)
        except Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(SERIAL_POLL_INTERVAL_MS, self._process_serial_events)

    def _handle_serial_line(self, line: str) -> None:
        try:
            event = parse_message(line)
        except ProtocolError as exc:
            print(f"Ignored serial message {line!r}: {exc}")
            return

        if isinstance(event, JoinEvent):
            self.controller.add_player(event.device_id)
            if self.serial and event.device_id in self.controller.players:
                self.serial.send(encode_join_ack(event.device_id))
        elif isinstance(event, MoveEvent):
            self.controller.move_player(event.device_id, event.steps)

    def _computer_tick(self) -> None:
        self.controller.move_computer()
        if self.root.winfo_exists():
            self.root.after(COMPUTER_TICK_MS, self._computer_tick)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="micro:bit racing game")
    parser.add_argument("--port", help="Serial port, for example COM4")
    parser.add_argument("--windowed", action="store_true", help="Disable fullscreen mode")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Start without a micro:bit serial connection",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = tk.Tk()
    app = GameApplication(
        root,
        port=args.port,
        fullscreen=not args.windowed,
        demo=args.demo,
    )
    app.run()


if __name__ == "__main__":
    main()
