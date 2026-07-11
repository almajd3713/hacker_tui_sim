from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class BannerWidget(Widget):
    """Stylized multi-line heading block."""

    def __init__(
        self,
        name: str,
        text: str = "",
        text_key: str | None = None,
        accent_char: str = "═",
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.text = text
        self.text_key = text_key
        self.accent_char = accent_char
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["text"] = text

    @property
    def _schema(self):
        return {
            "text": str,
            "text_key": str,
            "accent_char": str,
            "fg_color": str,
            "bg_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["text"] = str(resolve_path(context.data, self.text_key, self.text)) if self.text_key is not None else self.text
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = min(max(height, 0), 3)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

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
        text = str(self.state.get("text", "")).upper()
        middle = " ".join(text)[: rect.width]
        top_bottom = (self.accent_char * rect.width)[: rect.width]

        if rect.height >= 1:
            buffer.write_text(rect.x, rect.y, top_bottom, style.fg_color, style.bg_color)
        if rect.height >= 2:
            buffer.write_text(rect.x, rect.y + 1, middle.center(rect.width), style.fg_color, style.bg_color)
        if rect.height >= 3:
            buffer.write_text(rect.x, rect.y + 2, top_bottom, style.fg_color, style.bg_color)
