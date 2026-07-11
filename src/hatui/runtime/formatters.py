from typing import Any, Callable


def _format_percent(value: Any, precision: int = 0) -> str:
    return f"{float(value) * 100:.{precision}f}%"


def _format_fixed(value: Any, precision: int = 2) -> str:
    return f"{float(value):.{precision}f}"


def _format_upper(value: Any) -> str:
    return str(value).upper()


def _format_lower(value: Any) -> str:
    return str(value).lower()


def _format_join(value: Any, separator: str = ", ") -> str:
    if not isinstance(value, list):
        return str(value)
    return separator.join(str(item) for item in value)


def _format_bytes(value: Any) -> str:
    size = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]
    unit = units[0]
    for unit in units:
        if abs(size) < 1024 or unit == units[-1]:
            break
        size /= 1024
    return f"{size:.1f} {unit}"


FORMATTERS: dict[str, Callable[..., str]] = {
    "str": lambda value, **_: str(value),
    "upper": lambda value, **_: _format_upper(value),
    "lower": lambda value, **_: _format_lower(value),
    "percent": lambda value, precision=0, **_: _format_percent(value, precision=precision),
    "fixed": lambda value, precision=2, **_: _format_fixed(value, precision=precision),
    "join": lambda value, separator=", ", **_: _format_join(value, separator=separator),
    "bytes": lambda value, **_: _format_bytes(value),
}


def apply_formatter(value: Any, spec: str | dict | None = None) -> Any:
    if spec is None:
        return value
    if isinstance(spec, str):
        formatter = FORMATTERS.get(spec)
        return formatter(value) if formatter else value

    formatter = FORMATTERS.get(spec.get("name", ""))
    if formatter is None:
        return value
    kwargs = {key: item for key, item in spec.items() if key != "name"}
    return formatter(value, **kwargs)


def apply_template(value: Any, template: str | None = None) -> Any:
    if template is None:
        return value
    return template.format(value=value)
