from hatui.core.widget import Widget, WidgetContext
from hatui.core.style import BorderTheme


class BorderWidget(Widget):
    """Draw a border around a single child with configurable inner padding."""

    BORDER_STYLES = {
        "ascii": {
            "top_left": "+",
            "top_right": "+",
            "bottom_left": "+",
            "bottom_right": "+",
            "horizontal": "-",
            "vertical": "|",
        },
        "sharp": {
            "top_left": "┌",
            "top_right": "┐",
            "bottom_left": "└",
            "bottom_right": "┘",
            "horizontal": "─",
            "vertical": "│",
        },
        "rounded": {
            "top_left": "╭",
            "top_right": "╮",
            "bottom_left": "╰",
            "bottom_right": "╯",
            "horizontal": "─",
            "vertical": "│",
        },
    }

    def __init__(
        self,
        name: str,
        child: Widget | None = None,
        padding: int = 0,
        style: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        font_name: str | None = None,
    ):
        children = [child] if child is not None else []
        super().__init__(name, children)
        self.padding = max(padding, 0)
        self.style = style
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.font_name = font_name

    @property
    def _schema(self):
        return {
            "padding": int,
            "style": str,
            "fg_color": str,
            "bg_color": str,
            "font_name": str,
        }

    def _resolved_theme(self, context: WidgetContext) -> BorderTheme:
        fallback = context.theme.border
        style = self.style if self.style in self.BORDER_STYLES else fallback.style
        return BorderTheme(
            style=style,
            fg_color=fallback.fg_color if self.fg_color is None else self.fg_color,
            bg_color=fallback.bg_color if self.bg_color is None else self.bg_color,
            font_name=fallback.font_name if self.font_name is None else self.font_name,
        )

    def allocate_children(self, width: int, height: int):
        if not self.children:
            return

        inset = 2 + (self.padding * 2)
        child_width = max(width - inset, 0)
        child_height = max(height - inset, 0)
        self.children[0].allocate(child_width, child_height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if not self.children:
            return

        offset = 1 + self.padding
        self.children[0].layout(x + offset, y + offset, context)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width < 2 or rect.height < 2:
            return

        theme = self._resolved_theme(context)
        border = self.BORDER_STYLES[theme.style]
        left = rect.x
        right = rect.x + rect.width - 1
        top = rect.y
        bottom = rect.y + rect.height - 1

        buffer.write(left, top, border["top_left"], theme.fg_color, theme.bg_color)
        buffer.write(right, top, border["top_right"], theme.fg_color, theme.bg_color)
        buffer.write(left, bottom, border["bottom_left"], theme.fg_color, theme.bg_color)
        buffer.write(right, bottom, border["bottom_right"], theme.fg_color, theme.bg_color)

        for x in range(left + 1, right):
            buffer.write(x, top, border["horizontal"], theme.fg_color, theme.bg_color)
            buffer.write(x, bottom, border["horizontal"], theme.fg_color, theme.bg_color)

        for y in range(top + 1, bottom):
            buffer.write(left, y, border["vertical"], theme.fg_color, theme.bg_color)
            buffer.write(right, y, border["vertical"], theme.fg_color, theme.bg_color)

        if self.children:
            self.children[0].paint(buffer, context)
