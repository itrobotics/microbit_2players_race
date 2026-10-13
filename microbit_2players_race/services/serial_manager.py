from dataclasses import dataclass
from queue import Queue
from threading import Event, Lock, Thread

import serial
import serial.tools.list_ports

from config import SERIAL_BAUDRATE, SERIAL_TIMEOUT_SECONDS


@dataclass(frozen=True)
class SerialLine:
    text: str


@dataclass(frozen=True)
class SerialError:
    message: str


class SerialManager:
    """USB serial transport for the computer-connected receiver micro:bit."""

    def __init__(
        self,
        event_queue: Queue,
        port: str | None = None,
        baudrate: int = SERIAL_BAUDRATE,
    ) -> None:
        self.event_queue = event_queue
        self.requested_port = port
        self.baudrate = baudrate
        self.port_name: str | None = None
        self._serial: serial.Serial | None = None
        self._stop_event = Event()
        self._write_lock = Lock()
        self._reader: Thread | None = None

    def open(self) -> str:
        self.port_name = self.requested_port or self._find_microbit_port()
        self._serial = serial.Serial(
            self.port_name,
            self.baudrate,
            timeout=SERIAL_TIMEOUT_SECONDS,
        )
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()
        return self.port_name

    def start(self) -> None:
        if self._serial is None:
            raise RuntimeError("Serial port has not been opened")
        self._stop_event.clear()
        self._reader = Thread(target=self._read_loop, name="microbit-serial", daemon=True)
        self._reader.start()

    def send(self, message: str) -> None:
        if self._serial is None or not self._serial.is_open:
            return
        with self._write_lock:
            self._serial.write(message.encode("ascii"))
            self._serial.flush()

    def close(self) -> None:
        self._stop_event.set()
        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=1)
        if self._serial and self._serial.is_open:
            self._serial.close()

    def _read_loop(self) -> None:
        assert self._serial is not None
        while not self._stop_event.is_set():
            try:
                raw_line = self._serial.readline()
                if not raw_line:
                    continue
                text = raw_line.decode("ascii").strip()
                if text:
                    self.event_queue.put(SerialLine(text))
            except (serial.SerialException, UnicodeDecodeError) as exc:
                self.event_queue.put(SerialError(str(exc)))
                return

    @staticmethod
    def _find_microbit_port() -> str:
        ports = list(serial.tools.list_ports.comports(include_links=False))
        if not ports:
            raise RuntimeError("No serial device was found.")

        markers = ("micro:bit", "microbit", "daplink", "cmsis-dap")
        for port in ports:
            details = " ".join(
                filter(None, (port.description, port.manufacturer, port.product))
            ).lower()
            if any(marker in details for marker in markers):
                return port.device

        if len(ports) == 1:
            return ports[0].device

        devices = ", ".join(port.device for port in ports)
        raise RuntimeError(
            f"Multiple serial devices were found ({devices}). "
            "Start the program with --port COMx."
        )
