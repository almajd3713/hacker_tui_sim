from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class StatusStripWidget(Widget):
    """One-line dense status/footer strip."""

    def __init__(
        self,
        name: str,
        segments_key: str | None = None,
        separator: str = " | ",
        fg_color: str | None = None,
        bg_color: str | None = "bright_black",
    ):
        super().__init__(name)
        self.segments_key = segments_key
        self.separator = separator
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["segments"] = []

    @property
    def _schema(self):
        return {
            "segments_key": str,
            "separator": str,
            "fg_color": str,
            "bg_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["segments"] = list(context.data.get(self.segments_key, [])) if self.segments_key is not None else []
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

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color="default" if self.bg_color is None else self.bg_color,
            ),
        )
        for x in range(rect.width):
            buffer.write(rect.x + x, rect.y, " ", base_style.fg_color, base_style.bg_color)

        cursor_x = rect.x
        for index, segment in enumerate(self.state.get("segments", [])):
            if cursor_x >= rect.x + rect.width:
                break
            if index > 0:
                sep = self.separator[: rect.x + rect.width - cursor_x]
                buffer.write_text(cursor_x, rect.y, sep, base_style.fg_color, base_style.bg_color)
                cursor_x += len(sep)
            if isinstance(segment, dict):
                text = str(segment.get("text", ""))
                fg = segment.get("fg_color", base_style.fg_color)
                bg = segment.get("bg_color", base_style.bg_color)
            else:
                text = str(segment)
                fg = base_style.fg_color
                bg = base_style.bg_color
            clipped = text[: rect.x + rect.width - cursor_x]
            buffer.write_text(cursor_x, rect.y, clipped, fg, bg)
            cursor_x += len(clipped)
