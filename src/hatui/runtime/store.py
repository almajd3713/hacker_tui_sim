from __future__ import annotations

from copy import deepcopy
from typing import Any

from hatui.runtime.bindings import resolve_path, set_path


class Store:
    def __init__(self, initial_state: dict[str, Any] | None = None, root_path: str = "state"):
        self.root_path = root_path
        self.state = deepcopy(initial_state or {})

    def sync_to_context(self, context):
        set_path(context.data, self.root_path, deepcopy(self.state))

    def get(self, path: str | None = None, default: Any = None) -> Any:
        if not path:
            return self.state
        return resolve_path(self.state, path, default)

    def set(self, path: str, value: Any):
        set_path(self.state, path, value)
        return value

    def toggle(self, path: str, default: bool = False) -> bool:
        next_value = not bool(self.get(path, default))
        self.set(path, next_value)
        return next_value
