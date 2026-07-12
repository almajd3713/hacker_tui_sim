from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import coerce_float, trim_text


class HistogramWidget(Widget):
    """Horizontal histogram for bucketed distributions."""

    def __init__(
        self,
        name: str,
        buckets_key: str | None = None,
        label_width: int = 10,
        show_value: bool = True,
        fg_color: str | None = None,
        bg_color: str | None = None,
        fill_color: str | None = None,
    ):
        super().__init__(name)
        self.buckets_key = buckets_key
        self.label_width = max(int(label_width), 0)
        self.show_value = show_value
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.state["buckets"] = []

    @property
    def _schema(self):
        return {
            "buckets_key": str,
            "label_width": int,
            "show_value": bool,
            "fg_color": str,
            "bg_color": str,
            "fill_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["buckets"] = list(resolve_path(context.data, self.buckets_key, [])) if self.buckets_key is not None else []
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

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        buckets = self.state.get("buckets", [])
        if rect.width <= 0 or rect.height <= 0 or not buckets:
            return
        base_style = themed_style(
            context.theme,
            "histogram",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        fill_color = resolve_color_token(
            self.fill_color or context.theme.widget_slot("histogram", "fill_color", context.theme.color("accent")),
            context.theme,
            context.theme.color("accent"),
        )
        max_value = max(coerce_float(bucket.get("value", bucket.get("count", 0.0))) for bucket in buckets if isinstance(bucket, dict))
        max_value = max(max_value, 1.0)
        label_width = min(self.label_width, max(rect.width - 1, 0))
        for row_index, bucket in enumerate(buckets[: rect.height]):
            if not isinstance(bucket, dict):
                bucket = {"label": str(bucket), "value": 0}
            value = coerce_float(bucket.get("value", bucket.get("count", 0.0)))
            label = trim_text(bucket.get("label", ""), label_width).ljust(label_width)
            y = rect.y + row_index
            buffer.write_text(rect.x, y, label, base_style.fg_color, base_style.bg_color)
            available = max(rect.width - label_width - 1, 0)
            fill_width = int(round((value / max_value) * available)) if available > 0 else 0
            color = resolve_color_token(bucket.get("fg_color"), context.theme, fill_color)
            for index in range(available):
                char = "█" if index < fill_width else " "
                buffer.write(rect.x + label_width + 1 + index, y, char, color if char == "█" else base_style.fg_color, base_style.bg_color)
            if self.show_value and available > 0:
                value_text = trim_text(bucket.get("display", bucket.get("count", value)), available)
                start = rect.x + label_width + 1 + max(available - len(value_text), 0)
                buffer.write_text(start, y, value_text, base_style.fg_color, base_style.bg_color)

