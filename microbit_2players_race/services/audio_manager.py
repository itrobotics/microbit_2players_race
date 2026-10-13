from pathlib import Path


class AudioManager:
    def __init__(self) -> None:
        self._pygame = None
        self._available = True

    def play(self, path: Path) -> None:
        if not self._available:
            return
        try:
            if self._pygame is None:
                import pygame

                self._pygame = pygame
                pygame.mixer.init()
            self._pygame.mixer.music.load(str(path))
            self._pygame.mixer.music.play()
        except Exception as exc:
            self._available = False
            print(f"Audio disabled: {exc}")

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.mixer.quit()
