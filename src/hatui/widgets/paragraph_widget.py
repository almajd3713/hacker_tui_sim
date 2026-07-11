import textwrap

from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class ParagraphWidget(Widget):
    """Multi-line wrapped text clipped to the available rectangle."""

    def __init__(
        self,
        name: str,
        text: str = "",
        text_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        font_name: str | None = None,
    ):
        super().__init__(name)
        self.text = text
        self.text_key = text_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.font_name = font_name
        self.state["text"] = text

    @property
    def _schema(self):
        return {
            "text": str,
            "text_key": str,
            "fg_color": str,
            "bg_color": str,
            "font_name": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        if self.text_key is not None:
            self.state["text"] = str(resolve_path(context.data, self.text_key, ""))
        else:
            self.state["text"] = self.text
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

    def _wrapped_lines(self, width: int) -> list[str]:
        if width <= 0:
            return []

        text = self.state.get("text", "")
        paragraphs = text.splitlines() or [text]
        lines: list[str] = []
        for paragraph in paragraphs:
            if paragraph == "":
                lines.append("")
                continue
            lines.extend(textwrap.wrap(paragraph, width=width, drop_whitespace=False) or [""])
        return lines

    def measure_content(self, width: int, height: int) -> tuple[int, int]:
        lines = self._wrapped_lines(width)
        return max(width, 0), max(len(lines), height, 0)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        lines = self._wrapped_lines(rect.width)[: rect.height]
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
        for index, line in enumerate(lines):
            buffer.write_text(rect.x, rect.y + index, line[: rect.width], style.fg_color, style.bg_color)
