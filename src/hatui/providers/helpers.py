from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hatui.runtime.bindings import resolve_path
from hatui.runtime.formatters import apply_formatter, apply_template

_MISSING = object()

def resolve_value_spec(
    spec: Any,
    data: dict[str, Any],
    *,
    current: Any = None,
    default: Any = None,
    string_mode: str = "path",
) -> Any:
    if isinstance(spec, Mapping):
        value = _resolve_mapping_value(
            spec,
            data,
            current=current,
            default=default,
            string_mode=string_mode,
        )
        operations = spec.get("operations", [])
        if operations:
            value = apply_operations(value, operations, data)
        return value

    if isinstance(spec, str):
        resolved = resolve_path(data, spec, _MISSING)
        if resolved is not _MISSING:
            return resolved
        if string_mode == "literal_fallback":
            return spec
        if string_mode == "literal":
            return spec
        return default

    if spec is None:
        return default

    return spec


def resolve_mapping(
    mapping: Mapping[str, Any],
    data: dict[str, Any],
    *,
    current: Any = None,
    string_mode: str = "path",
) -> dict[str, Any]:
    return {
        key: resolve_value_spec(source, data, current=current, string_mode=string_mode)
        for key, source in mapping.items()
    }


def resolve_items(
    items: list[Any],
    data: dict[str, Any],
    *,
    current: Any = None,
    string_mode: str = "literal_fallback",
) -> list[Any]:
    resolved: list[Any] = []
    for item in items:
        if isinstance(item, Mapping):
            resolved.append(resolve_mapping(item, data, current=current, string_mode=string_mode))
        else:
            resolved.append(resolve_value_spec(item, data, current=current, string_mode=string_mode))
    return resolved


def render_template(template: str, mapping: Mapping[str, Any], data: dict[str, Any], *, current: Any = None) -> str:
    values = resolve_mapping(mapping, data, current=current, string_mode="path")
    return template.format(**values)


def apply_operations(value: Any, operations: list[Any], data: dict[str, Any]) -> Any:
    current = value
    for operation in operations:
        if not isinstance(operation, Mapping):
            continue
        name = operation.get("name")
        if name == "path":
            current = resolve_path(current, operation.get("path"), operation.get("default"))
        elif name == "default":
            if current is None:
                current = operation.get("value")
        elif name == "formatter":
            formatter = operation.get("formatter")
            if formatter is None:
                formatter = {key: item for key, item in operation.items() if key != "name"}
            current = apply_formatter(current, formatter)
        elif name == "template":
            current = apply_template(current, operation.get("template"))
        elif name == "sort":
            current = _sort_values(current, operation)
        elif name == "reverse":
            if isinstance(current, list):
                current = list(reversed(current))
        elif name == "slice":
            if isinstance(current, (list, str)):
                start = operation.get("start")
                end = operation.get("end")
                current = current[slice(start, end)]
        elif name == "take":
            if isinstance(current, list):
                current = current[: int(operation.get("count", 0))]
        elif name == "join":
            separator = operation.get("separator", ", ")
            if isinstance(current, list):
                current = separator.join(str(item) for item in current)
        elif name == "mapping":
            current = resolve_mapping(operation.get("mapping", {}), data, current=current, string_mode="path")
        elif name == "template_map":
            current = render_template(
                operation.get("template", ""),
                operation.get("mapping", {}),
                data,
                current=current,
            )
        elif name == "items":
            current = resolve_items(operation.get("items", []), data, current=current, string_mode="literal_fallback")
    return current


def _resolve_mapping_value(
    spec: Mapping[str, Any],
    data: dict[str, Any],
    *,
    current: Any,
    default: Any,
    string_mode: str,
) -> Any:
    if "value" in spec:
        value = spec.get("value")
    elif spec.get("current") is True:
        value = current
    elif "path" in spec or "source" in spec:
        value = resolve_path(data, spec.get("path") or spec.get("source"), spec.get("default", default))
    elif "mapping" in spec and "template" in spec:
        value = render_template(spec.get("template", ""), spec.get("mapping", {}), data, current=current)
    elif "mapping" in spec:
        value = resolve_mapping(spec.get("mapping", {}), data, current=current, string_mode=string_mode)
    elif "items" in spec:
        value = resolve_items(spec.get("items", []), data, current=current, string_mode="literal_fallback")
    else:
        value = default

    if "formatter" in spec:
        value = apply_formatter(value, spec.get("formatter"))
    if "template" in spec and "mapping" not in spec:
        value = apply_template(value, spec.get("template"))
    return value


def _sort_values(value: Any, operation: Mapping[str, Any]) -> Any:
    if not isinstance(value, list):
        return value

    reverse = bool(operation.get("reverse", False))
    key_path = operation.get("path")
    if key_path:
        return sorted(value, key=lambda item: resolve_path(item, key_path), reverse=reverse)
    return sorted(value, reverse=reverse)
