from __future__ import annotations

from copy import deepcopy
from typing import Any

from hatui.runtime.bindings import set_path


class Router:
    def __init__(
        self,
        routes: list[str] | None = None,
        initial: str | None = None,
        root_path: str = "_router",
    ):
        self.routes = list(routes or [])
        default_route = initial or (self.routes[0] if self.routes else None)
        self.stack: list[str] = [default_route] if default_route else []
        self.root_path = root_path

    @property
    def current(self) -> str | None:
        return self.stack[-1] if self.stack else None

    def sync_to_context(self, context):
        set_path(
            context.data,
            self.root_path,
            {
                "current": self.current,
                "stack": deepcopy(self.stack),
                "routes": list(self.routes),
            },
        )

    def has_route(self, route: str | None) -> bool:
        return bool(route) and route in self.routes

    def set_current(self, route: str) -> bool:
        if not self.has_route(route):
            return False
        if self.stack:
            self.stack[-1] = route
        else:
            self.stack.append(route)
        return True

    def push(self, route: str) -> bool:
        if not self.has_route(route):
            return False
        self.stack.append(route)
        return True

    def pop(self) -> bool:
        if len(self.stack) <= 1:
            return False
        self.stack.pop()
        return True

    def next(self) -> bool:
        if not self.routes:
            return False
        if self.current not in self.routes:
            return self.set_current(self.routes[0])
        index = self.routes.index(self.current)
        return self.set_current(self.routes[(index + 1) % len(self.routes)])

    def previous(self) -> bool:
        if not self.routes:
            return False
        if self.current not in self.routes:
            return self.set_current(self.routes[-1])
        index = self.routes.index(self.current)
        return self.set_current(self.routes[(index - 1) % len(self.routes)])
