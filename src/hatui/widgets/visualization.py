from __future__ import annotations

from math import floor
from typing import Any


BLOCK_LEVELS = " ▁▂▃▄▅▆▇█"
SHADE_LEVELS = " ░▒▓█"


def coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def coerce_float_list(values: Any) -> list[float]:
    if not isinstance(values, list):
        return []
    return [coerce_float(value) for value in values]


def fit_values(values: list[float], width: int) -> list[float]:
    if width <= 0 or not values:
        return []
    if len(values) == width:
        return list(values)
    if len(values) == 1:
        return [values[0] for _ in range(width)]

    result: list[float] = []
    last_index = len(values) - 1
    for index in range(width):
        position = 0.0 if width == 1 else index * last_index / (width - 1)
        left = floor(position)
        right = min(left + 1, last_index)
        fraction = position - left
        result.append(values[left] + (values[right] - values[left]) * fraction)
    return result


def value_bounds(series: list[list[float]], minimum: float | None = None, maximum: float | None = None) -> tuple[float, float]:
    flattened = [value for values in series for value in values]
    if not flattened:
        low = 0.0 if minimum is None else minimum
        high = 1.0 if maximum is None else maximum
        return low, high if high > low else low + 1.0

    low = min(flattened) if minimum is None else minimum
    high = max(flattened) if maximum is None else maximum
    if high <= low:
        high = low + 1.0
    return low, high


def value_to_row(value: float, minimum: float, maximum: float, height: int) -> int:
    if height <= 1:
        return 0
    span = maximum - minimum
    if span <= 0:
        return height - 1
    normalized = (value - minimum) / span
    normalized = max(0.0, min(1.0, normalized))
    return max(0, min(height - 1, height - 1 - int(round(normalized * (height - 1)))))


def quantize(value: float, minimum: float, maximum: float, levels: str) -> str:
    if not levels:
        return " "
    if maximum <= minimum:
        return levels[-1]
    normalized = (value - minimum) / (maximum - minimum)
    normalized = max(0.0, min(1.0, normalized))
    index = min(len(levels) - 1, int(round(normalized * (len(levels) - 1))))
    return levels[index]


def trim_text(text: Any, width: int) -> str:
    return str(text)[: max(width, 0)]


def flatten_object(value: Any, *, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_object(item, prefix=path))
        return rows
    if isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            rows.extend(flatten_object(item, prefix=path))
        return rows
    rows.append((prefix or "value", str(value)))
    return rows
