from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from hatui.runtime.bindings import resolve_path


@dataclass(frozen=True)
class StoreSelectionBinding:
    path: str
    value_factory: Callable[[], Any]


def read_selected_index(context, key_path: str | None, fallback: int) -> int:
    if key_path is None:
        return fallback
    value = resolve_path(context.data, key_path, fallback)
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return fallback


def clamp_selected_index(index: int, items: list[Any]) -> int:
    if not items:
        return 0
    return max(0, min(int(index), len(items) - 1))


def move_selected_index(index: int, delta: int, items: list[Any]) -> int:
    if not items:
        return 0
    return clamp_selected_index(index + delta, items)


def sync_selection(
    widget,
    context,
    items: list[Any],
    selected_index: int,
    *,
    index_key: str | None = None,
    bindings: list[StoreSelectionBinding] | None = None,
) -> int:
    clamped = clamp_selected_index(selected_index, items)
    if index_key is not None:
        widget.root.perform_action("store_set", {"path": index_key, "value": clamped}, context)
    if items:
        for binding in bindings or []:
            widget.root.perform_action("store_set", {"path": binding.path, "value": binding.value_factory()}, context)
    return clamped
