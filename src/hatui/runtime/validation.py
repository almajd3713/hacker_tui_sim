from __future__ import annotations

import inspect
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, get_args, get_origin

from hatui.runtime.registries import ProviderRegistry, WidgetRegistration, WidgetRegistry

TOP_LEVEL_KEYS = {"theme", "state", "router", "providers", "screen"}
GENERIC_WIDGET_KEYS = {"type", "name", "weight", "focusable", "selectable", "focus_fg_color", "focus_bg_color", "keybindings", "include"}
BASE_PROVIDER_KEYS = {
    "type",
    "name",
    "target",
    "metadata_target",
    "interval",
    "group",
    "depends_on",
    "enabled",
    "include",
}


@dataclass(frozen=True)
class ValidationMessage:
    path: str
    message: str
    level: str = "error"

    def format(self) -> str:
        return f"{self.level.upper()} {self.path}: {self.message}"


class SpecValidationError(ValueError):
    def __init__(self, spec_path: str | Path, messages: list[ValidationMessage]):
        self.spec_path = str(spec_path)
        self.messages = list(messages)
        formatted = "\n".join(message.format() for message in self.messages)
        super().__init__(f"Invalid Hatui spec: {self.spec_path}\n{formatted}")


class SpecValidator:
    def __init__(self, widget_registry: WidgetRegistry, provider_registry: ProviderRegistry):
        self.widget_registry = widget_registry
        self.provider_registry = provider_registry

    def validate(self, spec: dict[str, Any], *, spec_path: str | Path = "<memory>") -> list[ValidationMessage]:
        messages: list[ValidationMessage] = []
        if not isinstance(spec, dict):
            return [ValidationMessage("$", "top-level spec must resolve to an object")]

        self._validate_top_level(spec, messages)
        self._validate_theme(spec.get("theme"), "theme", messages)
        self._validate_state(spec.get("state"), "state", messages)
        self._validate_router(spec.get("router"), "router", messages)
        self._validate_providers(spec.get("providers"), "providers", messages)
        self._validate_screen(spec.get("screen"), "screen", messages)
        return messages

    def raise_for_errors(self, spec: dict[str, Any], *, spec_path: str | Path = "<memory>") -> None:
        messages = self.validate(spec, spec_path=spec_path)
        errors = [message for message in messages if message.level == "error"]
        if errors:
            raise SpecValidationError(spec_path, errors)

    def _validate_top_level(self, spec: dict[str, Any], messages: list[ValidationMessage]) -> None:
        for key in spec:
            if key not in TOP_LEVEL_KEYS:
                messages.append(ValidationMessage("$", f"unknown top-level key '{key}'"))
        if "screen" not in spec:
            messages.append(ValidationMessage("$", "missing required top-level 'screen' object"))

    def _validate_theme(self, theme: Any, path: str, messages: list[ValidationMessage]) -> None:
        if theme is None:
            return
        if not isinstance(theme, dict):
            messages.append(ValidationMessage(path, "expected an object"))
            return
        for key in ("preset",):
            if key in theme and not isinstance(theme[key], str):
                messages.append(ValidationMessage(f"{path}.{key}", "expected a string"))
        for key in ("colors", "fonts", "spacing", "widgets", "border", "text"):
            if key in theme and not isinstance(theme[key], dict):
                messages.append(ValidationMessage(f"{path}.{key}", "expected an object"))

    def _validate_state(self, state: Any, path: str, messages: list[ValidationMessage]) -> None:
        if state is None:
            return
        if not isinstance(state, dict):
            messages.append(ValidationMessage(path, "expected an object"))

    def _validate_router(self, router: Any, path: str, messages: list[ValidationMessage]) -> None:
        if router is None:
            return
        if not isinstance(router, dict):
            messages.append(ValidationMessage(path, "expected an object"))
            return
        routes = router.get("routes")
        if routes is not None and not isinstance(routes, list):
            messages.append(ValidationMessage(f"{path}.routes", "expected a list"))
        if "initial" in router and not isinstance(router["initial"], str):
            messages.append(ValidationMessage(f"{path}.initial", "expected a string"))

    def _validate_providers(self, providers: Any, path: str, messages: list[ValidationMessage]) -> None:
        if providers is None:
            return
        if not isinstance(providers, list):
            messages.append(ValidationMessage(path, "expected a list"))
            return
        for index, provider in enumerate(providers):
            item_path = f"{path}[{index}]"
            if not isinstance(provider, dict):
                messages.append(ValidationMessage(item_path, "expected an object"))
                continue
            provider_type = provider.get("type")
            if not provider_type:
                messages.append(ValidationMessage(item_path, "missing required key 'type'"))
                continue
            if not isinstance(provider_type, str):
                messages.append(ValidationMessage(f"{item_path}.type", "expected a string"))
                continue
            provider_cls = self.provider_registry.get(provider_type)
            if provider_cls is None:
                known = ", ".join(self.provider_registry.registered_types())
                messages.append(ValidationMessage(f"{item_path}.type", f"unknown provider type '{provider_type}'. Known types: {known}"))
                continue

            allowed_keys = set(BASE_PROVIDER_KEYS)
            allowed_keys.update(getattr(provider_cls, "spec_schema", {}).keys())
            required_keys = set(getattr(provider_cls, "required_spec_keys", set()))

            self._validate_mapping_keys(provider, allowed_keys, item_path, messages, ignored={"include"})
            self._validate_required_keys(provider, required_keys, item_path, messages)
            self._validate_typed_mapping(provider, getattr(provider_cls, "spec_schema", {}), item_path, messages)

    def _validate_screen(self, screen: Any, path: str, messages: list[ValidationMessage]) -> None:
        self._validate_widget_spec(screen, path, messages)

    def _validate_widget_spec(self, spec: Any, path: str, messages: list[ValidationMessage]) -> None:
        if not isinstance(spec, dict):
            messages.append(ValidationMessage(path, "expected an object"))
            return
        widget_type = spec.get("type")
        if not widget_type:
            messages.append(ValidationMessage(path, "missing required key 'type'"))
            return
        if not isinstance(widget_type, str):
            messages.append(ValidationMessage(f"{path}.type", "expected a string"))
            return

        registration = self.widget_registry.get(widget_type)
        if registration is None:
            known = ", ".join(self.widget_registry.registered_types())
            messages.append(ValidationMessage(f"{path}.type", f"unknown widget type '{widget_type}'. Known types: {known}"))
            return

        allowed_keys = set(GENERIC_WIDGET_KEYS)
        allowed_keys.update(registration.allowed_keys)
        required_keys = set(registration.required_keys)

        signature_schema, signature_required = self._signature_schema(registration)
        allowed_keys.update(signature_schema.keys())
        required_keys.update(signature_required)

        self._validate_mapping_keys(spec, allowed_keys, path, messages, ignored={"include"})
        self._validate_required_keys(spec, required_keys, path, messages)
        self._validate_typed_mapping(spec, signature_schema, path, messages)

        self._validate_nested_widgets(registration, spec, path, messages)

    def _validate_nested_widgets(
        self,
        registration: WidgetRegistration,
        spec: dict[str, Any],
        path: str,
        messages: list[ValidationMessage],
    ) -> None:
        widget_type = registration.widget_type
        if widget_type in {"box", "border", "scroll", "center", "modal"} and "child" in spec:
            self._validate_widget_spec(spec["child"], f"{path}.child", messages)
        if widget_type in {"row", "column"}:
            children = spec.get("children", [])
            if not isinstance(children, list):
                messages.append(ValidationMessage(f"{path}.children", "expected a list"))
            else:
                for index, child in enumerate(children):
                    self._validate_widget_spec(child, f"{path}.children[{index}]", messages)
        if widget_type == "tabs":
            tabs = spec.get("tabs", [])
            if not isinstance(tabs, list):
                messages.append(ValidationMessage(f"{path}.tabs", "expected a list"))
            else:
                for index, tab in enumerate(tabs):
                    tab_path = f"{path}.tabs[{index}]"
                    if not isinstance(tab, dict):
                        messages.append(ValidationMessage(tab_path, "expected an object"))
                        continue
                    if not isinstance(tab.get("title"), str):
                        messages.append(ValidationMessage(f"{tab_path}.title", "expected a string"))
                    child = tab.get("child") or tab.get("screen")
                    if child is None:
                        messages.append(ValidationMessage(tab_path, "requires 'child' or 'screen'"))
                    else:
                        child_key = "child" if "child" in tab else "screen"
                        self._validate_widget_spec(child, f"{tab_path}.{child_key}", messages)
        if widget_type == "modal_host":
            child = spec.get("child") or spec.get("screen")
            if child is None:
                messages.append(ValidationMessage(path, "requires 'child' or 'screen'"))
            else:
                child_key = "child" if "child" in spec else "screen"
                self._validate_widget_spec(child, f"{path}.{child_key}", messages)
            modals = spec.get("modals", [])
            if not isinstance(modals, list):
                messages.append(ValidationMessage(f"{path}.modals", "expected a list"))
            else:
                for index, modal in enumerate(modals):
                    modal_path = f"{path}.modals[{index}]"
                    if not isinstance(modal, dict):
                        messages.append(ValidationMessage(modal_path, "expected an object"))
                        continue
                    if not isinstance(modal.get("route"), str):
                        messages.append(ValidationMessage(f"{modal_path}.route", "expected a string"))
                    child = modal.get("child") or modal.get("screen") or modal.get("modal")
                    if child is None:
                        messages.append(ValidationMessage(modal_path, "requires 'child', 'screen', or 'modal'"))
                    else:
                        child_key = "child" if "child" in modal else "screen" if "screen" in modal else "modal"
                        self._validate_widget_spec(child, f"{modal_path}.{child_key}", messages)

    def _signature_schema(self, registration: WidgetRegistration) -> tuple[dict[str, Any], set[str]]:
        widget_cls = registration.widget_cls
        if widget_cls is None:
            return {}, set()
        schema: dict[str, Any] = {}
        required: set[str] = set()
        signature = inspect.signature(widget_cls.__init__)
        for name, parameter in signature.parameters.items():
            if name in {"self", "children"}:
                continue
            if parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
                continue
            if name == "name":
                required.add("name")
                schema["name"] = str
                continue
            if parameter.annotation is not inspect._empty:
                schema[name] = parameter.annotation
            if parameter.default is inspect._empty:
                required.add(name)
        return schema, required

    def _validate_mapping_keys(
        self,
        mapping: dict[str, Any],
        allowed_keys: set[str],
        path: str,
        messages: list[ValidationMessage],
        *,
        ignored: set[str] | None = None,
    ) -> None:
        ignored = ignored or set()
        for key in mapping:
            normalized_key = self._normalize_mapping_key(key)
            if normalized_key in ignored:
                continue
            if normalized_key not in allowed_keys:
                messages.append(ValidationMessage(path, f"unknown field '{key}'"))

    def _validate_required_keys(
        self,
        mapping: dict[str, Any],
        required_keys: set[str],
        path: str,
        messages: list[ValidationMessage],
    ) -> None:
        for key in sorted(required_keys):
            if key not in {self._normalize_mapping_key(item) for item in mapping}:
                messages.append(ValidationMessage(path, f"missing required field '{key}'"))

    def _validate_typed_mapping(
        self,
        mapping: dict[str, Any],
        schema: dict[str, Any],
        path: str,
        messages: list[ValidationMessage],
    ) -> None:
        for key, expected in schema.items():
            if key not in mapping:
                continue
            value = mapping[key]
            if value is None:
                continue
            if key in {"child", "screen", "modal"} and isinstance(value, dict):
                continue
            if not self._matches_type(value, expected):
                messages.append(
                    ValidationMessage(
                        f"{path}.{key}",
                        f"expected {self._type_label(expected)}, got {type(value).__name__}",
                    )
                )

    def _normalize_mapping_key(self, key: Any) -> Any:
        if key is True:
            return "true"
        if key is False:
            return "false"
        return key

    def _matches_type(self, value: Any, expected: Any) -> bool:
        origin = get_origin(expected)
        if expected is Any:
            return True
        if origin is None:
            if expected is float:
                return isinstance(value, (int, float)) and not isinstance(value, bool)
            if expected is int:
                return isinstance(value, int) and not isinstance(value, bool)
            if expected is bool:
                return isinstance(value, bool)
            if expected in {str, list, dict}:
                return isinstance(value, expected)
            if isinstance(expected, type):
                return isinstance(value, expected)
            return True
        if origin in {list, set, tuple}:
            return isinstance(value, origin)
        if origin is dict:
            return isinstance(value, dict)
        if origin in {types.UnionType, getattr(types, "UnionType", types.UnionType)} or str(origin).endswith("Union"):
            args = [arg for arg in get_args(expected) if arg is not type(None)]
            return any(self._matches_type(value, arg) for arg in args)
        return True

    def _type_label(self, expected: Any) -> str:
        origin = get_origin(expected)
        if origin is None:
            return getattr(expected, "__name__", str(expected))
        args = ", ".join(self._type_label(arg) for arg in get_args(expected))
        return f"{origin.__name__}[{args}]"
