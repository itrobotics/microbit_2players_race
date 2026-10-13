# micro:bit 2-player racing game

Two players carry micro:bits and move to advance their runners on the computer
screen. The computer does not handle micro:bit radio itself. A receiver/bridge
micro:bit listens for the wireless messages and forwards the received data to
the Python program through its USB serial port.

```text
Player micro:bits -> micro:bit radio -> Receiver micro:bit -> USB serial -> Python game
```

## Requirements

- Python 3.10 or newer
- Three micro:bits for a two-player physical race: two players and one receiver
- The receiver (`moderator.hex`) and player firmware in `microbit_programs/`

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the game:

```powershell
python microbit_1v1_race.py
```

If several serial devices are attached, select the moderator explicitly:

```powershell
python microbit_1v1_race.py --port COM4
```

For a windowed UI without hardware:

```powershell
python microbit_1v1_race.py --demo --windowed
```

Run the automated tests:

```powershell
python -m unittest discover -s tests -v
```

## Architecture

- `models/`: player data and game states
- `controllers/`: race rules and winner detection
- `services/`: serial communication, protocol parsing, and audio
- `views/`: Tkinter user interface
- `main.py`: application wiring and event-loop coordination

The serial reader runs in a background thread and sends messages through a
thread-safe queue. All Tkinter updates remain on the main UI thread.

Radio reception and radio addressing remain entirely inside the micro:bit
firmware. The computer program only reads and writes serial messages.

The original underscore messages are still supported:

```text
player1
player1_3
```

The parser also accepts a more explicit pipe format for future firmware:

```text
JOIN|player1
MOVE|player1|3
```
