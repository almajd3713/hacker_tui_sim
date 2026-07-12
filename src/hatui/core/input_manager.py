from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import os
import select
import sys


@dataclass
class InputEvent:
    event_type: str
    key: str
    modifiers: list[str]
    callback: Callable


class InputManager:
    def __init__(self):
        self.events: list[InputEvent] = []
        self.is_windows = os.name == "nt"

    def on(self, event_type: str, key: str, modifiers: list[str], callback: Callable):
        self.events.append(InputEvent(event_type, key, modifiers, callback))

    def emit_event(self, event_type: str, key: str, modifiers: list[str]):
        for event in self.events:
            if event.event_type == event_type and event.key == key and event.modifiers == modifiers:
                event.callback()

    def poll_input(self, timeout: float = 0.05) -> tuple[str, list[str]] | None:
        raw = self._read_input(timeout)
        if raw is None:
            return None
        key, modifiers = self._parse_key(raw)
        self.emit_event("keypress", key, modifiers)
        return key, modifiers

    def _read_input(self, timeout: float) -> str | None:
        if self.is_windows:
            return self._read_input_windows(timeout)
        return self._read_input_posix(timeout)

    def _read_input_posix(self, timeout: float) -> str | None:
        fd = sys.stdin.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            return None

        first = os.read(fd, 1).decode(errors="ignore")
        if first != "\x1b":
            return first
        return first + self._read_ready_chars(fd, 0.02, settle_timeout=0.005)

    def _read_ready_chars(self, fd: int, timeout: float, settle_timeout: float = 0.01) -> str:
        chars: list[str] = []
        ready, _, _ = select.select([fd], [], [], timeout)
        while ready:
            chars.append(os.read(fd, 32).decode(errors="ignore"))
            ready, _, _ = select.select([fd], [], [], settle_timeout)
        return "".join(chars)

    def _read_input_windows(self, timeout: float) -> str | None:
        import time
        import msvcrt

        deadline = time.monotonic() + max(timeout, 0.0)
        while time.monotonic() < deadline:
            if not msvcrt.kbhit():
                time.sleep(min(0.005, timeout))
                continue
            first = msvcrt.getwch()
            if first in ("\x00", "\xe0"):
                second = msvcrt.getwch()
                return self._windows_extended_key(first + second)
            return first
        return None

    def _windows_extended_key(self, raw: str) -> str:
        extended = {
            "\xe0H": "\x1b[A",
            "\xe0P": "\x1b[B",
            "\xe0M": "\x1b[C",
            "\xe0K": "\x1b[D",
            "\x00H": "\x1b[A",
            "\x00P": "\x1b[B",
            "\x00M": "\x1b[C",
            "\x00K": "\x1b[D",
            "\x00\x0f": "\x1b[Z",
        }
        return extended.get(raw, raw)

    def _parse_key(self, raw: str) -> tuple[str, list[str]]:
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
            return arrow_map[raw], []

        if raw == "\x1b[Z":
            return "tab", ["shift"]

        if raw == "\t":
            return "tab", []

        if raw in ("\r", "\n"):
            return "enter", []

        if raw in ("\x7f", "\b", "\x08"):
            return "backspace", []

        if raw == " ":
            return "space", []

        if len(raw) == 2 and raw.startswith("\x1b") and raw[1].isprintable():
            key = raw[1].lower()
            modifiers = ["alt"]
            if raw[1].isalpha() and raw[1].isupper():
                modifiers.append("shift")
            return key, modifiers

        if len(raw) == 1 and 0 < ord(raw) < 27:
            return chr(ord(raw) + 96), ["ctrl"]

        if raw == "\x1b":
            return "escape", []

        if raw.startswith("\x1b[1;") and raw.endswith(("A", "B", "C", "D")):
            return self._parse_csi_arrow(raw)

        if raw.startswith("\x1b"):
            return "escape", []

        modifiers: list[str] = []
        if raw.isalpha() and raw.isupper():
            modifiers.append("shift")
        return raw.lower(), modifiers

    def _parse_csi_arrow(self, raw: str) -> tuple[str, list[str]]:
        modifier_map = {
            "2": ["shift"],
            "3": ["alt"],
            "4": ["shift", "alt"],
            "5": ["ctrl"],
            "6": ["shift", "ctrl"],
            "7": ["alt", "ctrl"],
            "8": ["shift", "alt", "ctrl"],
        }
        suffix = raw[-1]
        key = {
            "A": "up",
            "B": "down",
            "C": "right",
            "D": "left",
        }[suffix]
        code = raw[4:-1]
        return key, modifier_map.get(code, [])
