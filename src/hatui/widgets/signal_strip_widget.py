from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import trim_text


class SignalStripWidget(Widget):
    """Compact indicator strip for named operational signals."""

    def __init__(
        self,
        name: str,
        items_key: str | None = None,
        separator: str = " ",
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.items_key = items_key
        self.separator = separator
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["items"] = []

    @property
    def _schema(self):
        return {"items_key": str, "separator": str, "fg_color": str, "bg_color": str}

    def update(self, delta_time: float, context: WidgetContext):
        self.state["items"] = list(resolve_path(context.data, self.items_key, [])) if self.items_key is not None else []
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
        base_style = themed_style(
            context.theme,
            "signal_strip",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        cursor_x = rect.x
        for item_index, item in enumerate(self.state.get("items", [])):
            if cursor_x >= rect.x + rect.width:
                break
            if item_index > 0:
                separator = self.separator[: rect.x + rect.width - cursor_x]
                buffer.write_text(cursor_x, rect.y, separator, base_style.fg_color, base_style.bg_color)
                cursor_x += len(separator)
            if not isinstance(item, dict):
                item = {"label": str(item), "severity": "info"}
            severity = str(item.get("severity") or item.get("state") or "info").lower()
            signal_color = resolve_color_token(
                context.theme.widget_slot("signal_strip", f"{severity}_fg_color", context.theme.color(severity, base_style.fg_color)),
                context.theme,
                base_style.fg_color,
            )
            marker = str(item.get("marker", "■"))[:1]
            text = trim_text(f"{marker}{item.get('label', '')}", rect.x + rect.width - cursor_x)
            buffer.write_text(cursor_x, rect.y, text, signal_color, base_style.bg_color)
            cursor_x += len(text)

