from dataclasses import dataclass
from typing import Callable, List
import os
import select
import sys


@dataclass
class InputEvent:
    event_type: str
    key: str
    modifiers: list
    callback: Callable

class InputManager:
    def __init__(self):
        self.events: List[InputEvent] = []
    
    def on(self, event_type: str, key: str, modifiers: list, callback: Callable):
        event = InputEvent(event_type, key, modifiers, callback)
        self.events.append(event)

    def emit_event(self, event_type: str, key: str, modifiers: list):
        for event in self.events:
            if event.event_type == event_type and event.key == key and event.modifiers == modifiers:
                event.callback()

    def _read_ready_chars(self, fd: int, timeout: float, settle_timeout: float = 0.01) -> str:
        chars = []
        ready, _, _ = select.select([fd], [], [], timeout)
        while ready:
            chars.append(os.read(fd, 32).decode(errors="ignore"))
            ready, _, _ = select.select([fd], [], [], settle_timeout)
        return "".join(chars)

    def _parse_key(self, raw: str) -> tuple[str, list]:
        if raw == "\x03":
            raise KeyboardInterrupt("Ctrl+C pressed")

        arrow_map = {
            "\x1b[A": "up",
            "\x1b[B": "down",
            "\x1b[C": "right",
            "\x1b[D": "left",
            "\x1bOA": "up",
            "\x1bOB": "down",
            "\x1bOC": "right",
            "\x1bOD": "left",
        }
        if raw in arrow_map:
            return arrow_map[raw], ["arrow"]

        if raw == "\x1b[Z":
            return "tab", ["shift"]

        if raw == "\t":
            return "tab", []

        if raw in ("\r", "\n"):
            return "enter", []

        if raw in ("\x7f", "\b"):
            return "backspace", []

        if len(raw) == 1 and 0 < ord(raw) < 27:
            return chr(ord(raw) + 96), ["ctrl"]

        if raw == " ":
            return "space", []

        if raw.startswith("\x1b"):
            return "escape", []

        modifiers = []
        if raw.isalpha() and raw.isupper():
            modifiers.append("shift")
        return raw.lower(), modifiers

    def poll_input(self, timeout: float = 0.05) -> tuple[str, list] | None:
        """
        Polls stdin for a single character without blocking indefinitely.
        Returns the character if available, or None if the timeout is reached.
        """
        fd = sys.stdin.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None

        first = os.read(fd, 1).decode(errors="ignore")
        raw = first
        if first == "\x1b":
            raw += self._read_ready_chars(fd, 0.02, settle_timeout=0.005)
        key, modifiers = self._parse_key(raw)
        self.emit_event("keypress", key, modifiers)
        return key, modifiers
