from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class AlertWidget(Widget):
    """Highlighted single-line alert callout."""

    LEVEL_STYLES = {
        "info": ("INFO", "cyan"),
        "warn": ("WARN", "yellow"),
        "error": ("ALERT", "bright_red"),
        "success": ("OK", "green"),
    }

    def __init__(
        self,
        name: str,
        message: str = "",
        message_key: str | None = None,
        level: str = "info",
        level_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.message = message
        self.message_key = message_key
        self.level = level
        self.level_key = level_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["message"] = message
        self.state["level"] = level

    @property
    def _schema(self):
        return {
            "message": str,
            "message_key": str,
            "level": str,
            "level_key": str,
            "fg_color": str,
            "bg_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        self.state["message"] = str(resolve_path(context.data, self.message_key, self.message)) if self.message_key is not None else self.message
        self.state["level"] = str(resolve_path(context.data, self.level_key, self.level)) if self.level_key is not None else self.level
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

        level = self.state.get("level", "info")
        tag, level_color = self.LEVEL_STYLES.get(level, ("INFO", "cyan"))
        style = resolve_style(
            fg_color=self.fg_color or level_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        text = f"[{tag}] {self.state.get('message', '')}"[: rect.width]
        buffer.write_text(rect.x, rect.y, text, style.fg_color, style.bg_color)
