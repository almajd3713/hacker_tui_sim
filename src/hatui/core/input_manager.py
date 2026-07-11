
from dataclasses import dataclass
from typing import Callable, List


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

    def poll_input(self, timeout: float = 0.05) -> None:
        """
        Polls stdin for a single character without blocking indefinitely.
        Returns the character if available, or None if the timeout is reached.
        """
        import sys
        import select

        fd = sys.stdin.fileno()
        ready, _, _ = select.select([fd], [], [], timeout)
        
        if ready:
            char = sys.stdin.read(1)
            # If you are using setraw and want to handle Ctrl+C manually:
            if char == '\x03':
                raise KeyboardInterrupt("Ctrl+C pressed")
            # Modifiers
            modifiers = []
            if char.isupper():
                modifiers.append('shift')
            if char in ['\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D']:
                modifiers.append('arrow')
            if char in ['\x1b', '\x1b[', '\x1b[1;5A', '\x1b[1;5B', '\x1b[1;5C', '\x1b[1;5D']:
                modifiers.append('ctrl')
            # Emit the event for the character read
            self.emit_event('keypress', char.lower(), modifiers)