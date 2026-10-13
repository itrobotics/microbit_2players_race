import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import messagebox

from PIL import Image, ImageTk

from config import IMAGE_DIR, MAX_PLAYERS, RACE_DISTANCE, SPRITE_PATHS
from models import GameState, Player


class GameView:
    def __init__(
        self,
        root: tk.Tk,
        on_start: Callable[[], None],
        on_reset: Callable[[], None],
        on_exit: Callable[[], None],
        *,
        fullscreen: bool = True,
    ) -> None:
        self.root = root
        self.root.title("micro:bit racing game")
        self.root.attributes("-fullscreen", fullscreen)
        self.root.protocol("WM_DELETE_WINDOW", on_exit)
        self.root.bind("<Escape>", lambda _event: on_exit())
        self.root.bind("<F11>", self._toggle_fullscreen)

        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.root.update()

        self.width = max(self.canvas.winfo_width(), 800)
        self.height = max(self.canvas.winfo_height(), 600)
        self.start_x = int(self.width * 0.05)
        self.finish_x = int(self.width * 0.85)
        self.start_y = int(self.height * 0.57)
        self.lane_gap = int(self.height * 0.08)
        self.player_width = int(self.width * 0.04)
        self.player_height = int(self.width * 0.05)

        self._countdown_after_id: str | None = None
        self._icons: dict[str, int] = {}
        self._sprite_images: dict[str, ImageTk.PhotoImage] = {}
        self._last_players: list[Player] = []

        self._build_track()
        self._build_controls(on_start, on_reset, on_exit)
        self.render([], GameState.WAITING, None)

    def _build_track(self) -> None:
        track_height = int(self.height * 0.4)
        image = Image.open(IMAGE_DIR / "race_track.jpg")
        image = image.resize((self.width, track_height), Image.Resampling.LANCZOS)
        self._track_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(
            self.width // 2,
            int(self.height * 0.7),
            image=self._track_image,
        )

    def _build_controls(self, on_start, on_reset, on_exit) -> None:
        self.players_frame = tk.Frame(self.root, bg="#FA8072", bd=2)
        self.players_frame.place(
            relx=0.01, rely=0.02, relwidth=0.25, relheight=0.28, anchor="nw"
        )
        for column, text in enumerate(("Name", "Image", "Status")):
            tk.Label(self.players_frame, text=text).grid(
                column=column, row=0, sticky="nsew", padx=1, pady=1
            )

        self.name_labels: list[tk.Label] = []
        self.sprite_vars: list[tk.StringVar] = []
        self.sprite_menus: list[tk.OptionMenu] = []
        self.status_labels: list[tk.Label] = []
        choices = tuple(SPRITE_PATHS)

        for lane in range(MAX_PLAYERS):
            name_label = tk.Label(self.players_frame, anchor="w")
            sprite_var = tk.StringVar(value=choices[lane % len(choices)])
            sprite_menu = tk.OptionMenu(self.players_frame, sprite_var, *choices)
            status_label = tk.Label(self.players_frame, bg="green")
            sprite_var.trace_add("write", lambda *_args: self._refresh_sprites())
            self.name_labels.append(name_label)
            self.sprite_vars.append(sprite_var)
            self.sprite_menus.append(sprite_menu)
            self.status_labels.append(status_label)

        button_frame = tk.Frame(self.root, bg="green", bd=2)
        button_frame.place(
            relx=0.5, rely=0.1, relwidth=0.3, relheight=0.1, anchor="n"
        )
        tk.Button(
            button_frame,
            text="Start Race",
            font="Helvetica 25 bold",
            bg="blue",
            fg="white",
            command=on_start,
        ).place(relwidth=1, relheight=1)

        upper_frame = tk.Frame(self.root, bg="black", bd=5)
        upper_frame.place(
            relx=0.5, rely=0.25, relwidth=0.65, relheight=0.2, anchor="n"
        )
        self.message_label = tk.Label(upper_frame, font="Helvetica 40 bold italic")
        self.message_label.place(relwidth=1, relheight=1)

        actions = tk.Frame(self.root, bg="white", bd=5)
        actions.place(
            relx=0.5, rely=0.9, relwidth=0.22, relheight=0.1, anchor="n"
        )
        tk.Button(actions, text="Reset", bg="red", fg="white", command=on_reset).place(
            relwidth=0.45, relheight=1
        )
        tk.Button(actions, text="Exit", bg="black", fg="white", command=on_exit).place(
            relx=0.55, relwidth=0.45, relheight=1
        )

    def render(
        self,
        players: Iterable[Player],
        state: GameState,
        winner_id: str | None,
    ) -> None:
        player_list = list(players)
        self._last_players = player_list
        active_ids = {player.device_id for player in player_list}

        for device_id in list(self._icons):
            if device_id not in active_ids:
                self.canvas.delete(self._icons.pop(device_id))
                self._sprite_images.pop(device_id, None)

        for lane in range(MAX_PLAYERS):
            widgets = (
                self.name_labels[lane],
                self.sprite_menus[lane],
                self.status_labels[lane],
            )
            if lane >= len(player_list):
                for widget in widgets:
                    widget.grid_remove()
                continue

            player = player_list[lane]
            self.name_labels[lane].configure(text=player.display_name)
            self.status_labels[lane].configure(bg="green" if player.connected else "red")
            for column, widget in enumerate(widgets):
                widget.grid(row=lane + 1, column=column, sticky="nsew", padx=1, pady=1)

            if player.device_id not in self._icons:
                self._icons[player.device_id] = self.canvas.create_image(
                    self.start_x,
                    self.start_y + self.lane_gap * lane,
                    tags=("players",),
                )
            progress = min(player.distance / RACE_DISTANCE, 1)
            x = self.start_x + progress * (self.finish_x - self.start_x)
            self.canvas.coords(
                self._icons[player.device_id],
                x,
                self.start_y + self.lane_gap * lane,
            )

        self._refresh_sprites()

        if state == GameState.WAITING:
            self.message_label.configure(text=f"{len(player_list)} players")
        elif state == GameState.COUNTDOWN:
            self.message_label.configure(text="Get ready")
        elif state == GameState.RACING:
            status = "   ".join(
                f"{player.display_name}: {player.distance}" for player in player_list
            )
            self.message_label.configure(text=status)
        elif state == GameState.FINISHED and winner_id:
            winner = next(p for p in player_list if p.device_id == winner_id)
            self.message_label.configure(text=f"{winner.display_name} wins!")

    def _refresh_sprites(self) -> None:
        for player in self._last_players:
            path = SPRITE_PATHS[self.sprite_vars[player.lane].get()]
            image = Image.open(path).resize(
                (self.player_width, self.player_height), Image.Resampling.LANCZOS
            )
            photo = ImageTk.PhotoImage(image)
            self._sprite_images[player.device_id] = photo
            self.canvas.itemconfigure(self._icons[player.device_id], image=photo)

    def start_countdown(
        self,
        count: int,
        on_complete: Callable[[], None],
        on_tick: Callable[[], None],
    ) -> None:
        self.cancel_countdown()

        def tick(value: int) -> None:
            self._countdown_after_id = None
            if value > 0:
                self.message_label.configure(text=str(value))
                on_tick()
                self._countdown_after_id = self.root.after(900, tick, value - 1)
            else:
                self.message_label.configure(text="GO!")
                on_complete()

        tick(count)

    def cancel_countdown(self) -> None:
        if self._countdown_after_id is not None:
            self.root.after_cancel(self._countdown_after_id)
            self._countdown_after_id = None

    def show_error(self, message: str) -> None:
        messagebox.showerror("Error", message)

    def set_connection_message(self, message: str) -> None:
        self.message_label.configure(text=message)

    def _toggle_fullscreen(self, _event=None) -> None:
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
