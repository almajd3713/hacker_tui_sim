from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class CodeBlockWidget(Widget):
    """Read-only multi-line code or console block."""

    def __init__(
        self,
        name: str,
        code: str = "",
        code_key: str | None = None,
        show_line_numbers: bool = False,
        fg_color: str | None = None,
        bg_color: str | None = None,
        line_number_color: str | None = None,
    ):
        super().__init__(name)
        self.code = code
        self.code_key = code_key
        self.show_line_numbers = show_line_numbers
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.line_number_color = line_number_color
        self.state["lines"] = code.splitlines()

    @property
    def _schema(self):
        return {
            "code": str,
            "code_key": str,
            "show_line_numbers": bool,
            "fg_color": str,
            "bg_color": str,
            "line_number_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        code = context.data.get(self.code_key, self.code) if self.code_key is not None else self.code
        self.state["lines"] = str(code).splitlines()
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
        lines = self.state.get("lines", [])
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        number_style = resolve_style(
            fg_color=self.line_number_color or context.theme.border.fg_color,
            bg_color=base_style.bg_color,
            fallback=base_style,
        )

        visible = lines[: rect.height]
        number_width = len(str(len(visible))) + 1 if self.show_line_numbers and visible else 0

        for index, line in enumerate(visible):
            x = rect.x
            if number_width > 0:
                number = f"{index + 1:>{number_width - 1}} "
                buffer.write_text(x, rect.y + index, number[: rect.width], number_style.fg_color, number_style.bg_color)
                x += min(number_width, rect.width)
            available = max(rect.width - (x - rect.x), 0)
            if available > 0:
                buffer.write_text(x, rect.y + index, line[:available], base_style.fg_color, base_style.bg_color)
