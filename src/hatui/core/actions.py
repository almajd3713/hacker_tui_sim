from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KeyBinding:
    key: str
    modifiers: tuple[str, ...] = ()
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def chord(self) -> str:
        if not self.modifiers:
            return self.key
        return "+".join([*self.modifiers, self.key])


def normalize_chord(key: str, modifiers: list[str] | tuple[str, ...] | None = None) -> str:
    parts = [
        part.strip().lower()
        for part in (modifiers or [])
        if part and part.strip().lower() != "arrow"
    ]
    key_name = key.strip().lower()
    if key_name:
        parts.append(key_name)
    return "+".join(parts)


def parse_keybinding(spec: str | dict[str, Any]) -> KeyBinding:
    if isinstance(spec, str):
        return KeyBinding(key=spec.strip().lower())

    chord = str(spec.get("key", "")).strip().lower()
    if not chord:
        raise ValueError("Keybinding spec missing 'key'")

    parts = [part for part in chord.split("+") if part]
    key = parts[-1]
    modifiers = tuple(parts[:-1])
    action = str(spec.get("action", "")).strip()
    payload = dict(spec.get("payload", {}) or {})
    return KeyBinding(key=key, modifiers=modifiers, action=action, payload=payload)
