from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WidgetRegistration:
    widget_type: str
    factory: Callable[[dict[str, Any], Any], Any]
    widget_cls: type | None = None
    allowed_keys: set[str] = field(default_factory=set)
    required_keys: set[str] = field(default_factory=set)


class WidgetRegistry:
    def __init__(self):
        self._registrations: dict[str, WidgetRegistration] = {}

    def register(
        self,
        widget_type: str,
        factory: Callable[[dict[str, Any], Any], Any],
        *,
        widget_cls: type | None = None,
        allowed_keys: set[str] | None = None,
        required_keys: set[str] | None = None,
    ):
        self._registrations[widget_type] = WidgetRegistration(
            widget_type=widget_type,
            factory=factory,
            widget_cls=widget_cls,
            allowed_keys=set(allowed_keys or set()),
            required_keys=set(required_keys or set()),
        )

    def create(self, widget_type: str, spec: dict[str, Any], loader):
        registration = self.get(widget_type)
        if registration is None:
            raise ValueError(f"Unknown widget type: {widget_type}")
        return registration.factory(spec, loader)

    def get(self, widget_type: str) -> WidgetRegistration | None:
        return self._registrations.get(widget_type)

    def registered_types(self) -> list[str]:
        return sorted(self._registrations)


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, type] = {}

    def register(self, provider_type: str, provider_cls: type):
        self._providers[provider_type] = provider_cls

    def create(self, provider_type: str, spec: dict[str, Any]):
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        return self._providers[provider_type](spec)

    def get(self, provider_type: str) -> type | None:
        return self._providers.get(provider_type)

    def registered_types(self) -> list[str]:
        return sorted(self._providers)
