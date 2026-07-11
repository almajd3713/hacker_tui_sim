from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class SparklineWidget(Widget):
    """Single-line sparkline chart from a numeric series."""

    GLYPHS = "▁▂▃▄▅▆▇█"

    def __init__(
        self,
        name: str,
        values_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.values_key = values_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["values"] = []

    @property
    def _schema(self):
        return {
            "values_key": str,
            "fg_color": str,
            "bg_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        values = resolve_path(context.data, self.values_key, []) if self.values_key is not None else []
        self.state["values"] = list(values)
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = 1 if height > 0 else 0
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def _sparkline(self, width: int) -> str:
        values = self.state.get("values", [])[-width:]
        if width <= 0:
            return ""
        if not values:
            return " " * width

        minimum = min(values)
        maximum = max(values)
        if minimum == maximum:
            return self.GLYPHS[0] * len(values)

        chars = []
        for value in values:
            normalized = (value - minimum) / (maximum - minimum)
            index = min(int(normalized * (len(self.GLYPHS) - 1)), len(self.GLYPHS) - 1)
            chars.append(self.GLYPHS[index])
        return "".join(chars).rjust(width)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        buffer.write_text(rect.x, rect.y, self._sparkline(rect.width), style.fg_color, style.bg_color)
