from __future__ import annotations

from copy import deepcopy
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
        path = Path(spec_path).resolve()
        spec = self._load_yaml(path)
        resolved = self._resolve_includes(spec, path.parent, chain=(path,))
        if not isinstance(resolved, dict):
            raise ValueError("Top-level spec must resolve to an object")
        return resolved

    def load_theme(self, spec: dict[str, Any]) -> Theme:
        theme_spec = spec.get("theme", {})
        border_spec = theme_spec.get("border", {})
        text_spec = theme_spec.get("text", {})
        return Theme(
            border=BorderTheme(**border_spec),
            text=TextTheme(**text_spec),
        )

    def load_state(self, spec: dict[str, Any]) -> dict[str, Any]:
        state = spec.get("state", {})
        if not isinstance(state, dict):
            raise ValueError("Top-level 'state' must be an object")
        return state

    def load_router(self, spec: dict[str, Any]) -> dict[str, Any]:
        router = spec.get("router", {})
        if router is None:
            return {}
        if not isinstance(router, dict):
            raise ValueError("Top-level 'router' must be an object")
        return router

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

    def _load_yaml(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _resolve_includes(self, node: Any, base_dir: Path, *, chain: tuple[Path, ...]) -> Any:
        if isinstance(node, list):
            resolved_items = []
            for item in node:
                resolved = self._resolve_includes(item, base_dir, chain=chain)
                if isinstance(resolved, list):
                    resolved_items.extend(resolved)
                else:
                    resolved_items.append(resolved)
            return resolved_items

        if not isinstance(node, dict):
            return node

        include_path = node.get("include")
        if include_path is not None:
            include_file = (base_dir / include_path).resolve()
            if include_file in chain:
                joined = " -> ".join(str(path) for path in (*chain, include_file))
                raise ValueError(f"Circular include detected: {joined}")

            included = self._load_yaml(include_file)
            included = self._resolve_includes(
                included,
                include_file.parent,
                chain=(*chain, include_file),
            )

            overrides = {key: value for key, value in node.items() if key != "include"}
            if not overrides:
                return deepcopy(included)
            if not isinstance(included, dict):
                raise ValueError(f"Include overrides require an object include: {include_file}")

            merged = deepcopy(included)
            for key, value in overrides.items():
                merged[key] = self._resolve_includes(value, base_dir, chain=chain)
            return merged

        return {
            key: self._resolve_includes(value, base_dir, chain=chain)
            for key, value in node.items()
        }
