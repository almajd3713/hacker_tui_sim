from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hatui.core.style import BorderTheme, TextTheme, Theme
from hatui.runtime.registries import ProviderRegistry, WidgetRegistry


class ScreenSpecLoader:
    def __init__(self, widget_registry: WidgetRegistry, provider_registry: ProviderRegistry):
        self.widget_registry = widget_registry
        self.provider_registry = provider_registry

    def load_spec(self, spec_path: str | Path) -> dict[str, Any]:
        with Path(spec_path).open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def load_theme(self, spec: dict[str, Any]) -> Theme:
        theme_spec = spec.get("theme", {})
        border_spec = theme_spec.get("border", {})
        text_spec = theme_spec.get("text", {})
        return Theme(
            border=BorderTheme(**border_spec),
            text=TextTheme(**text_spec),
        )

    def load_providers(self, spec: dict[str, Any]) -> list[Any]:
        providers = []
        for provider_spec in spec.get("providers", []):
            provider_type = provider_spec.get("type")
            if not provider_type:
                raise ValueError("Provider spec missing 'type'")
            providers.append(self.provider_registry.create(provider_type, provider_spec))
        return providers

    def load_screen(self, spec: dict[str, Any]):
        screen_spec = spec.get("screen")
        if not isinstance(screen_spec, dict):
            raise ValueError("Spec missing top-level 'screen' object")
        return self.build_widget(screen_spec)

    def build_widget(self, spec: dict[str, Any]):
        widget_type = spec.get("type")
        if not widget_type:
            raise ValueError("Widget spec missing 'type'")
        widget = self.widget_registry.create(widget_type, spec, self)
        widget.configure_interaction(spec)
        weight = spec.get("weight")
        if weight is not None:
            widget.set_layout_weight(weight)
        return widget
