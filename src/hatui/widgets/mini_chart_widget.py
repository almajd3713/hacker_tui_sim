from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class MiniChartWidget(Widget):
    """Compact vertical bar chart."""

    def __init__(
        self,
        name: str,
        values_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        fill_char: str = "█",
    ):
        super().__init__(name)
        self.values_key = values_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.fill_char = fill_char
        self.state["values"] = []

    @property
    def _schema(self):
        return {
            "values_key": str,
            "fg_color": str,
            "bg_color": str,
            "fill_char": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["values"] = list(context.data.get(self.values_key, [])) if self.values_key is not None else []
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
        values = self.state.get("values", [])[-rect.width :]
        if rect.width <= 0 or rect.height <= 0 or not values:
            return

        style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        minimum = min(values)
        maximum = max(values)
        span = maximum - minimum
        if span <= 0:
            normalized_values = [1.0 for _ in values]
        else:
            normalized_values = [(value - minimum) / span for value in values]

        for index, normalized in enumerate(normalized_values):
            column_height = max(1, int(round(normalized * rect.height)))
            for y in range(rect.height):
                char = self.fill_char if rect.height - y <= column_height else " "
                buffer.write(rect.x + index, rect.y + y, char, style.fg_color, style.bg_color)
