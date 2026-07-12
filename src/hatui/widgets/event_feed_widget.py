from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import trim_text


class EventFeedWidget(Widget):
    def __init__(
        self,
        name: str,
        events_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.events_key = events_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["events"] = []

    @property
    def _schema(self):
        return {"events_key": str, "fg_color": str, "bg_color": str}

    def update(self, delta_time: float, context: WidgetContext):
        payload = resolve_path(context.data, self.events_key, []) if self.events_key else []
        self.state["events"] = list(payload) if isinstance(payload, list) else []
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
        events = self.state.get("events", [])
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "event_feed",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        visible = events[-rect.height :]
        for row_index, event in enumerate(visible):
            level = event.get("level", "info") if isinstance(event, dict) else "info"
            color = resolve_color_token(
                context.theme.widget_slot("event_feed", f"{level}_fg_color", context.theme.color(level, base_style.fg_color)),
                context.theme,
                base_style.fg_color,
            )
            if isinstance(event, dict):
                timestamp = str(event.get("timestamp", "--:--:--"))
                source = str(event.get("source", "sys"))[:8].ljust(8)
                message = event.get("message") or event.get("text") or ""
                line = f"{timestamp} {source} {message}"
            else:
                line = str(event)
            buffer.write_text(rect.x, rect.y + row_index, trim_text(line, rect.width), color, base_style.bg_color)
