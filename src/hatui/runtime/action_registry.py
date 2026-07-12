from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ActionHandler = Callable[[Any, dict[str, Any], Any], bool]


@dataclass(slots=True)
class ActionRegistry:
    handlers: dict[str, ActionHandler]

    def __init__(self):
        self.handlers = {}

    def register(self, action: str, handler: ActionHandler) -> None:
        self.handlers[action] = handler

    def dispatch(self, action: str, source, payload: dict[str, Any], context) -> bool:
        handler = self.handlers.get(action)
        if handler is None:
            return bool(source.handle_action(action, payload, context))
        return bool(handler(source, payload, context))


def create_default_action_registry() -> ActionRegistry:
    registry = ActionRegistry()
    registry.register("focus_next", _focus_next)
    registry.register("focus_prev", _focus_prev)
    registry.register("focus_first", _focus_first)
    registry.register("focus_last", _focus_last)
    registry.register("focus_widget", _focus_widget)
    registry.register("route_set", _route_set)
    registry.register("route_next", _route_next)
    registry.register("route_prev", _route_prev)
    registry.register("route_push", _route_push)
    registry.register("route_pop", _route_pop)
    registry.register("route_pop_focus_widget", _route_pop_focus_widget)
    registry.register("store_set", _store_set)
    registry.register("store_toggle", _store_toggle)
    return registry


def _interaction(source):
    root = source.root
    interaction = getattr(root, "interaction", None)
    if interaction is None:
        raise RuntimeError("Root widget missing interaction controller")
    return interaction


def _focus_next(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).focus_next(context)


def _focus_prev(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).focus_prev(context)


def _focus_first(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).focus_first(context)


def _focus_last(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).focus_last(context)


def _focus_widget(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).focus_widget(payload.get("target"), context)


def _route_set(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_set(payload.get("route"), context)


def _route_next(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_next(context)


def _route_prev(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_prev(context)


def _route_push(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_push(payload.get("route"), context)


def _route_pop(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_pop(context)


def _route_pop_focus_widget(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).route_pop_focus_widget(payload.get("target"), context)


def _store_set(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).store_set(payload.get("path"), payload.get("value"), context)


def _store_toggle(source, payload: dict[str, Any], context) -> bool:
    return _interaction(source).store_toggle(payload.get("path"), context)
