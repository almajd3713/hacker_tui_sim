from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class LogWidget(Widget):
    """Append-only log view that renders the most recent lines first."""

    LEVEL_COLORS = {
        "info": None,
        "warn": "yellow",
        "error": "bright_red",
        "success": "green",
    }

    def __init__(
        self,
        name: str,
        lines_key: str | None = None,
        max_lines: int = 200,
        show_timestamp: bool = False,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.lines_key = lines_key
        self.max_lines = max_lines
        self.show_timestamp = show_timestamp
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["lines"] = []

    @property
    def _schema(self):
        return {
            "lines_key": str,
            "max_lines": int,
            "show_timestamp": bool,
            "fg_color": str,
            "bg_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        lines = resolve_path(context.data, self.lines_key, []) if self.lines_key is not None else []
        self.state["lines"] = list(lines)[-self.max_lines :]
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

    def _format_line(self, entry) -> tuple[str, str | None]:
        if isinstance(entry, dict):
            text = str(entry.get("text", ""))
            level = entry.get("level", "info")
            if self.show_timestamp and entry.get("timestamp"):
                text = f"[{entry['timestamp']}] {text}"
            return text, self.LEVEL_COLORS.get(level)
        return str(entry), None

    def measure_content(self, width: int, height: int) -> tuple[int, int]:
        return max(width, 0), max(len(self.state.get("lines", [])), height, 0)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "log",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        visible = self.state.get("lines", [])[-rect.height :]
        start_y = rect.y + max(rect.height - len(visible), 0)

        for index, entry in enumerate(visible):
            text, level_color = self._format_line(entry)
            themed_level = context.theme.widget_slot("log", f"{entry.get('level', 'info') if isinstance(entry, dict) else 'info'}_fg_color", None)
            line_style = themed_style(
                context.theme,
                "log",
                fg_color=themed_level or level_color or base_style.fg_color,
                bg_color=base_style.bg_color,
                fallback=base_style,
            )
            buffer.write_text(
                rect.x,
                start_y + index,
                text[: rect.width],
                line_style.fg_color,
                line_style.bg_color,
            )
