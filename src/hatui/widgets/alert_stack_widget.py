from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import WidgetContext
from hatui.widgets.list_widget import ListWidget
from hatui.widgets.visualization import trim_text


class AlertStackWidget(ListWidget):
    """Severity-oriented alert list for operational incident panes."""

    def __init__(self, name: str, source_width: int = 8, **kwargs):
        super().__init__(name, **kwargs)
        self.source_width = max(int(source_width), 0)

    @property
    def _schema(self):
        schema = dict(super()._schema)
        schema["source_width"] = int
        return schema

    def _alert_color(self, item: dict, context: WidgetContext, default: str) -> str:
        severity = str(item.get("level") or item.get("severity") or item.get("state") or "info").lower()
        return resolve_color_token(
            context.theme.widget_slot("alert_stack", f"{severity}_fg_color", context.theme.color(severity, default)),
            context.theme,
            default,
        )

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "alert_stack",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        selected_style = themed_style(
            context.theme,
            "alert_stack",
            fg_color=self.selected_fg_color or self.focus_fg_color or context.theme.widget_slot("alert_stack", "selected_fg_color", context.theme.color("selection_fg")),
            bg_color=self.selected_bg_color or self.focus_bg_color or context.theme.widget_slot("alert_stack", "selected_bg_color", context.theme.color("selection_bg")),
            fallback=base_style,
        )
        items = self.state.get("items", [])[: rect.height]
        selected_index = self.state.get("selected_index", 0)
        for row_index, item in enumerate(items):
            if not isinstance(item, dict):
                item = {"label": str(item), "level": "info"}
            active = row_index == selected_index
            fg = selected_style.fg_color if active else self._alert_color(item, context, base_style.fg_color)
            bg = selected_style.bg_color if active else base_style.bg_color
            timestamp = str(item.get("timestamp", "--:--:--"))
            source = trim_text(item.get("source", "sys"), self.source_width).ljust(self.source_width)
            message = item.get("message") or item.get("text") or item.get("label") or ""
            line = trim_text(f"{timestamp} {source} {message}", rect.width)
            fill = " " * rect.width
            buffer.write_text(rect.x, rect.y + row_index, fill, fg, bg)
            buffer.write_text(rect.x, rect.y + row_index, line, fg, bg)

