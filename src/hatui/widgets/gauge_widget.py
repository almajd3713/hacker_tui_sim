from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import coerce_float, trim_text


class GaugeWidget(Widget):
    def __init__(
        self,
        name: str,
        label: str = "",
        value_key: str | None = None,
        min_value: float = 0.0,
        max_value: float = 1.0,
        show_value: bool = True,
        fg_color: str | None = None,
        bg_color: str | None = None,
        fill_color: str | None = None,
        empty_color: str | None = None,
    ):
        super().__init__(name)
        self.label = label
        self.value_key = value_key
        self.min_value = min_value
        self.max_value = max_value
        self.show_value = show_value
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.empty_color = empty_color
        self.state["value"] = min_value

    @property
    def _schema(self):
        return {
            "label": str,
            "value_key": str,
            "min_value": float,
            "max_value": float,
            "show_value": bool,
            "fg_color": str,
            "bg_color": str,
            "fill_color": str,
            "empty_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        value = resolve_path(context.data, self.value_key, self.min_value) if self.value_key else self.min_value
        self.state["value"] = coerce_float(value, self.min_value)
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = min(max(height, 0), 2)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "gauge",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        fill_color = resolve_color_token(
            self.fill_color or context.theme.widget_slot("gauge", "fill_color", context.theme.color("accent")),
            context.theme,
            context.theme.color("accent"),
        )
        empty_color = resolve_color_token(
            self.empty_color or context.theme.widget_slot("gauge", "empty_color", context.theme.color("border")),
            context.theme,
            context.theme.color("border"),
        )

        value = self.state.get("value", self.min_value)
        span = self.max_value - self.min_value
        normalized = 0.0 if span <= 0 else max(0.0, min(1.0, (value - self.min_value) / span))

        if rect.height > 1:
            header = self.label
            if self.show_value:
                header = f"{self.label} {normalized * 100:5.1f}%".strip()
            buffer.write_text(rect.x, rect.y, trim_text(header, rect.width), base_style.fg_color, base_style.bg_color)

        bar_y = rect.y + rect.height - 1
        filled = int(round(normalized * rect.width))
        for index in range(rect.width):
            if index < filled:
                buffer.write(rect.x + index, bar_y, "█", fill_color, base_style.bg_color)
            else:
                buffer.write(rect.x + index, bar_y, "░", empty_color, base_style.bg_color)
