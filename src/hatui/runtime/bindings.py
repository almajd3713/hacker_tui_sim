from collections.abc import Mapping
from typing import Any


def resolve_path(data: Any, path: str | None, default: Any = None) -> Any:
    if path is None or path == "":
        return default

    current = data
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return default
            current = current[part]
            continue

        if isinstance(current, list):
            try:
                index = int(part)
            except ValueError:
                return default
            if index < 0 or index >= len(current):
                return default
            current = current[index]
            continue

        return default
    return current


def set_path(data: dict[str, Any], path: str, value: Any):
    parts = path.split(".")
    current: dict[str, Any] = data
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value
