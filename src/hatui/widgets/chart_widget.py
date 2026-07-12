from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import coerce_float, coerce_float_list, fit_values, glyph, trim_text, value_bounds, value_to_row


class ChartWidget(Widget):
    def __init__(
        self,
        name: str,
        mode: str = "line",
        values_key: str | None = None,
        series_key: str | None = None,
        bars_key: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        show_scale: bool = False,
        show_labels: bool = False,
        fg_color: str | None = None,
        bg_color: str | None = None,
        axis_color: str | None = None,
        fill_color: str | None = None,
    ):
        super().__init__(name)
        self.mode = mode
        self.values_key = values_key
        self.series_key = series_key
        self.bars_key = bars_key
        self.min_value = min_value
        self.max_value = max_value
        self.show_scale = show_scale
        self.show_labels = show_labels
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.axis_color = axis_color
        self.fill_color = fill_color
        self.state["series"] = []
        self.state["bars"] = []

    @property
    def _schema(self):
        return {
            "mode": str,
            "values_key": str,
            "series_key": str,
            "bars_key": str,
            "min_value": float,
            "max_value": float,
            "show_scale": bool,
            "show_labels": bool,
            "fg_color": str,
            "bg_color": str,
            "axis_color": str,
            "fill_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["series"] = self._resolve_series(context)
        self.state["bars"] = self._resolve_bars(context)
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def _resolve_series(self, context: WidgetContext) -> list[dict]:
        payload = resolve_path(context.data, self.series_key, []) if self.series_key else None
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            series = []
            for item in payload:
                values = coerce_float_list(item.get("values", []))
                if values:
                    series.append(
                        {
                            "values": values,
                            "fg_color": item.get("fg_color"),
                            "fill_color": item.get("fill_color"),
                            "label": item.get("label", ""),
                        }
                    )
            if series:
                return series

        values = resolve_path(context.data, self.values_key, []) if self.values_key else []
        numeric = coerce_float_list(values)
        if numeric:
            return [{"values": numeric, "fg_color": self.fg_color, "fill_color": self.fill_color, "label": ""}]
        return []

    def _resolve_bars(self, context: WidgetContext) -> list[dict]:
        payload = resolve_path(context.data, self.bars_key, []) if self.bars_key else []
        if isinstance(payload, list):
            bars = []
            for item in payload:
                if isinstance(item, dict):
                    bars.append(
                        {
                            "label": item.get("label", ""),
                            "value": coerce_float(item.get("value")),
                            "fg_color": item.get("fg_color"),
                        }
                    )
                else:
                    bars.append({"label": "", "value": coerce_float(item), "fg_color": None})
            return bars
        return []

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "chart",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        axis_color = resolve_color_token(
            self.axis_color or context.theme.widget_slot("chart", "axis_color", context.theme.color("border")),
            context.theme,
            context.theme.color("border"),
        )
        fill_color = resolve_color_token(
            self.fill_color or context.theme.widget_slot("chart", "fill_color", base_style.fg_color),
            context.theme,
            base_style.fg_color,
        )

        if self.mode == "bar":
            self._paint_bars(buffer, rect, base_style, axis_color, context)
            return
        self._paint_series(buffer, rect, base_style, axis_color, fill_color, context)

    def _paint_series(self, buffer, rect, base_style: Style, axis_color: str, fill_color: str, context: WidgetContext):
        series = self.state.get("series", [])
        if not series:
            return

        footer_rows = 1 if self.show_scale and rect.height > 1 else 0
        chart_height = max(rect.height - footer_rows, 1)
        fitted = [fit_values(item["values"], rect.width) for item in series]
        minimum, maximum = value_bounds(fitted, self.min_value, self.max_value)

        baseline_row = rect.y + chart_height - 1
        horizontal_char = glyph(context, "horizontal", "-")
        fill_char = glyph(context, "fill", "#")
        point_char = glyph(context, "point", "*")
        diag_down = glyph(context, "diag_down", "\\")
        diag_up = glyph(context, "diag_up", "/")
        for x in range(rect.width):
            buffer.write(rect.x + x, baseline_row, horizontal_char, axis_color, base_style.bg_color)

        for series_index, values in enumerate(fitted):
            config = series[series_index]
            color = resolve_color_token(config.get("fg_color"), context.theme, base_style.fg_color)
            series_fill = resolve_color_token(config.get("fill_color"), context.theme, fill_color)
            previous_row = None
            for index, value in enumerate(values):
                row = rect.y + value_to_row(value, minimum, maximum, chart_height)
                x = rect.x + index
                if self.mode == "area":
                    for fill_y in range(row, rect.y + chart_height):
                        buffer.write(x, fill_y, fill_char, series_fill, base_style.bg_color)
                else:
                    buffer.write(x, row, point_char, color, base_style.bg_color)

                if previous_row is not None and self.mode == "line":
                    step = 1 if row > previous_row else -1
                    if row == previous_row:
                        buffer.write(x - 1, row, horizontal_char, color, base_style.bg_color)
                    else:
                        for y in range(previous_row, row + step, step):
                            char = diag_down if row > previous_row else diag_up
                            buffer.write(x - 1, y, char, color, base_style.bg_color)
                previous_row = row

        if footer_rows:
            scale = f"{minimum:.2f}..{maximum:.2f}"
            buffer.write_text(rect.x, rect.y + rect.height - 1, trim_text(scale, rect.width), axis_color, base_style.bg_color)

    def _paint_bars(self, buffer, rect, base_style: Style, axis_color: str, context: WidgetContext):
        bars = self.state.get("bars", [])
        if not bars:
            return
        footer_rows = 1 if self.show_labels and rect.height > 2 else 0
        chart_height = max(rect.height - footer_rows, 1)
        maximum = self.max_value if self.max_value is not None else max((item["value"] for item in bars), default=1.0)
        maximum = maximum if maximum > 0 else 1.0
        slot_width = max(rect.width // max(len(bars), 1), 1)
        fill_char = glyph(context, "fill", "#")

        for index, bar in enumerate(bars[: rect.width]):
            x = rect.x + index * slot_width
            width = max(min(slot_width - 1, rect.width - index * slot_width), 1)
            height = int(round((bar["value"] / maximum) * chart_height))
            color = resolve_color_token(bar.get("fg_color"), context.theme, base_style.fg_color)
            for column in range(width):
                for offset in range(chart_height):
                    y = rect.y + chart_height - 1 - offset
                    active = offset < height
                    char = fill_char if active else " "
                    buffer.write(x + column, y, char, color if active else axis_color, base_style.bg_color)
            if footer_rows and x < rect.x + rect.width:
                buffer.write_text(
                    x,
                    rect.y + rect.height - 1,
                    trim_text(bar.get("label", ""), width),
                    axis_color,
                    base_style.bg_color,
                )
