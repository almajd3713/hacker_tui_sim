from __future__ import annotations

from collections.abc import Mapping

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import SHADE_LEVELS, coerce_float, coerce_float_list, glyph_levels, value_bounds


class HeatmapWidget(Widget):
    def __init__(
        self,
        name: str,
        matrix_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        levels: str = SHADE_LEVELS,
        color_ramp: list[str] | None = None,
        bg_ramp: list[str] | None = None,
        cell_char: str | None = None,
    ):
        super().__init__(name)
        self.matrix_key = matrix_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.levels = levels
        self.color_ramp = color_ramp
        self.bg_ramp = bg_ramp
        self.cell_char = cell_char
        self.state["matrix"] = []

    @property
    def _schema(self):
        return {
            "matrix_key": str,
            "fg_color": str,
            "bg_color": str,
            "levels": str,
            "color_ramp": list,
            "bg_ramp": list,
            "cell_char": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        payload = resolve_path(context.data, self.matrix_key, []) if self.matrix_key else []
        rows = []
        if isinstance(payload, list):
            for row in payload:
                rows.append(self._coerce_row(row))
        self.state["matrix"] = rows
        super().update(delta_time, context)

    def _coerce_row(self, row) -> list[float]:
        if isinstance(row, list):
            values: list[float] = []
            for item in row:
                if isinstance(item, Mapping):
                    if "value" in item:
                        values.append(coerce_float(item.get("value")))
                    elif "source" in item:
                        values.append(coerce_float(item.get("source")))
                    elif len(item) == 1:
                        values.append(coerce_float(next(iter(item.values()))))
                    else:
                        values.append(0.0)
                else:
                    values.append(coerce_float(item))
            return values
        if isinstance(row, Mapping):
            return coerce_float_list(list(row.values()))
        return [coerce_float(row)]

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def _resolve_ramp(self, values, context: WidgetContext, default: list[str]) -> list[str]:
        if not isinstance(values, list) or not values:
            return default
        if not default:
            return [resolve_color_token(value, context.theme, context.theme.text.bg_color) for value in values]
        return [resolve_color_token(value, context.theme, default[index % len(default)]) for index, value in enumerate(values)]

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        matrix = self.state.get("matrix", [])
        if rect.width <= 0 or rect.height <= 0 or not matrix:
            return

        style = themed_style(
            context.theme,
            "heatmap",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.color("accent"), context.theme.text.bg_color),
        )
        fg_ramp = self._resolve_ramp(
            self.color_ramp if self.color_ramp is not None else context.theme.widget_slot("heatmap", "color_ramp", None),
            context,
            [
                context.theme.color("text_muted"),
                context.theme.color("accent"),
                context.theme.color("success"),
                context.theme.color("warn"),
                context.theme.color("error"),
            ],
        )
        bg_ramp = self._resolve_ramp(
            self.bg_ramp if self.bg_ramp is not None else context.theme.widget_slot("heatmap", "bg_ramp", None),
            context,
            [],
        )
        cell_char = self.cell_char
        if cell_char is None:
            cell_char = context.theme.widget_slot("heatmap", "cell_char", None)
        cell_char = " " if cell_char is None else str(cell_char)[:1]
        levels = glyph_levels(context, "shade", self.levels or SHADE_LEVELS)
        visible_rows = matrix[-rect.height :]
        normalized_rows = []
        for row in visible_rows:
            if len(row) >= rect.width:
                normalized_rows.append(row[: rect.width])
            elif row:
                scale = max(len(row) / rect.width, 1)
                normalized_rows.append([row[min(int(index * scale), len(row) - 1)] for index in range(rect.width)])
            else:
                normalized_rows.append([0.0] * rect.width)
        minimum, maximum = value_bounds(normalized_rows)
        for row_index, row in enumerate(normalized_rows):
            for column_index, value in enumerate(row[: rect.width]):
                if maximum <= minimum:
                    ratio = 1.0
                else:
                    ratio = (value - minimum) / (maximum - minimum)
                    ratio = max(0.0, min(1.0, ratio))
                level_index = min(len(self.levels) - 1, int(round(ratio * (len(self.levels) - 1))))
                ramp_index = min(len(fg_ramp) - 1, int(round(ratio * (len(fg_ramp) - 1))))
                char = cell_char if bg_ramp else (cell_char if cell_char.strip() else levels[level_index])
                fg_color = fg_ramp[ramp_index] if fg_ramp else style.fg_color
                bg_color = style.bg_color
                if bg_ramp:
                    bg_index = min(len(bg_ramp) - 1, int(round(ratio * (len(bg_ramp) - 1))))
                    bg_color = bg_ramp[bg_index]
                buffer.write(rect.x + column_index, rect.y + row_index, char, fg_color, bg_color)
