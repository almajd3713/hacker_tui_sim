from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class LabelWidget(Widget):
    """Single-line text with alignment and overflow control."""

    def __init__(
        self,
        name: str,
        text: str = "",
        text_key: str | None = None,
        align: str = "left",
        overflow: str = "clip",
        fg_color: str | None = None,
        bg_color: str | None = None,
        font_name: str | None = None,
    ):
        super().__init__(name)
        self.text = text
        self.text_key = text_key
        self.align = align
        self.overflow = overflow
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.font_name = font_name
        self.state["text"] = text

    @property
    def _schema(self):
        return {
            "text": str,
            "text_key": str,
            "align": str,
            "overflow": str,
            "fg_color": str,
            "bg_color": str,
            "font_name": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        if self.text_key is not None:
            self.state["text"] = str(context.data.get(self.text_key, ""))
        else:
            self.state["text"] = self.text
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

    def _resolve_text(self, width: int) -> str:
        text = self.state.get("text", "")
        if width <= 0:
            return ""

        if len(text) <= width:
            return text

        if self.overflow == "ellipsis" and width >= 1:
            return text[: max(width - 1, 0)] + ("…" if width > 0 else "")

        return text[:width]

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        content = self._resolve_text(rect.width)
        if self.align == "center":
            x = rect.x + max((rect.width - len(content)) // 2, 0)
        elif self.align == "right":
            x = rect.x + max(rect.width - len(content), 0)
        else:
            x = rect.x

        style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            font_name=self.font_name,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
                font_name=context.theme.text.font_name,
            ),
        )
        buffer.write_text(x, rect.y, content, style.fg_color, style.bg_color)
