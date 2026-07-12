from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext


class DividerWidget(Widget):
    """Simple horizontal or vertical separator."""

    def __init__(
        self,
        name: str,
        orientation: str = "horizontal",
        char: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.orientation = orientation
        self.char = char
        self.fg_color = fg_color
        self.bg_color = bg_color

    @property
    def _schema(self):
        return {
            "orientation": str,
            "char": str,
            "fg_color": str,
            "bg_color": str,
        }

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0) if self.orientation == "horizontal" else min(max(width, 0), 1)
        rect.height = min(max(height, 0), 1) if self.orientation == "horizontal" else max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        style = themed_style(
            context.theme,
            "divider",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.border.fg_color,
                bg_color=context.theme.border.bg_color,
            ),
        )
        char = self.char or ("─" if self.orientation == "horizontal" else "│")

        if self.orientation == "horizontal":
            buffer.write_text(rect.x, rect.y, char * rect.width, style.fg_color, style.bg_color)
            return

        for y in range(rect.height):
            buffer.write(rect.x, rect.y + y, char, style.fg_color, style.bg_color)
