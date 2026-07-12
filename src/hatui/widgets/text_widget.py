from hatui.core.widget import Widget, WidgetContext
from hatui.core.style import Style, themed_style


class TextWidget(Widget):
    """
    A simple text widget that displays a string of text.
    """
    def __init__(
        self,
        name: str,
        text: str,
        fg_color: str | None = None,
        bg_color: str | None = None,
        font_name: str | None = None,
    ):
        super().__init__(name)
        self.text = text
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.font_name = font_name

    @property
    def _schema(self):
        return {
            "text": str,
            "fg_color": str,
            "bg_color": str,
            "font_name": str,
        }

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = min(max(width, 0), len(self.text))
        rect.height = 1 if height > 0 else 0

        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        # Render the text to the buffer at the specified position
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        clipped_text = self.text[:rect.width]
        style = themed_style(
            context.theme,
            "text",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            font_name=self.font_name,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
                font_name=context.theme.text.font_name,
            ),
        )
        buffer.write_text(rect.x, rect.y, clipped_text, style.fg_color, style.bg_color)
