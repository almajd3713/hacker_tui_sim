from collections.abc import Callable
from typing import Any


class WidgetRegistry:
    def __init__(self):
        self._factories: dict[str, Callable[[dict[str, Any], Any], Any]] = {}

    def register(self, widget_type: str, factory: Callable[[dict[str, Any], Any], Any]):
        self._factories[widget_type] = factory

    def create(self, widget_type: str, spec: dict[str, Any], loader):
        if widget_type not in self._factories:
            raise ValueError(f"Unknown widget type: {widget_type}")
        return self._factories[widget_type](spec, loader)


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, type] = {}

    def register(self, provider_type: str, provider_cls: type):
        self._providers[provider_type] = provider_cls

    def create(self, provider_type: str, spec: dict[str, Any]):
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        return self._providers[provider_type](spec)
