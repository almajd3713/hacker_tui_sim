from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class MetricGridWidget(Widget):
    """Compact multi-column label/value grid."""

    def __init__(
        self,
        name: str,
        metrics_key: str | None = None,
        columns: int = 2,
        gap: int = 2,
        fg_color: str | None = None,
        bg_color: str | None = None,
        accent_color: str | None = None,
    ):
        super().__init__(name)
        self.metrics_key = metrics_key
        self.columns = max(columns, 1)
        self.gap = max(gap, 0)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.state["metrics"] = []

    @property
    def _schema(self):
        return {
            "metrics_key": str,
            "columns": int,
            "gap": int,
            "fg_color": str,
            "bg_color": str,
            "accent_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        metrics = resolve_path(context.data, self.metrics_key, []) if self.metrics_key is not None else []
        self.state["metrics"] = list(metrics)
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
        metrics = self.state.get("metrics", [])
        if rect.width <= 0 or rect.height <= 0 or not metrics:
            return

        base_style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        accent_style = resolve_style(
            fg_color=self.accent_color or base_style.fg_color,
            bg_color=base_style.bg_color,
            fallback=base_style,
        )

        total_gap = self.gap * (self.columns - 1)
        cell_width = max((rect.width - total_gap) // self.columns, 1)

        for index, metric in enumerate(metrics[: rect.height * self.columns]):
            row = index // self.columns
            col = index % self.columns
            if row >= rect.height:
                break

            x = rect.x + col * (cell_width + self.gap)
            label = str(metric.get("label", ""))
            value = str(metric.get("value", ""))
            combined = f"{label}: "
            available = max(cell_width - len(combined), 0)

            buffer.write_text(x, rect.y + row, combined[:cell_width], base_style.fg_color, base_style.bg_color)
            if available > 0:
                buffer.write_text(
                    x + min(len(combined), cell_width),
                    rect.y + row,
                    value[:available],
                    accent_style.fg_color,
                    accent_style.bg_color,
                )
