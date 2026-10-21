import sys


class ProgressIndicator:
    """Display lightweight progress without interfering with normal output."""

    _FRAMES = ("|", "/", "-", "\\")

    def __init__(self, label: str, total: int):
        self.label = label
        self.total = total
        self.current = 0
        self._frame = 0
        self._interactive = sys.stdout.isatty()

    def update(self, detail: str = ""):
        self.current += 1
        progress = f"{self.current}/{self.total}" if self.total else str(self.current)
        message = f"{self.label} [{progress}]"
        if detail:
            message += f" {detail}"

        if self._interactive:
            frame = self._FRAMES[self._frame % len(self._FRAMES)]
            self._frame += 1
            print(f"\r{frame} {message}", end="", flush=True)
        else:
            print(message, flush=True)

    def finish(self):
        if self._interactive:
            print("\r" + " " * 100 + "\r", end="", flush=True)
