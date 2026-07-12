from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import flatten_object, trim_text


class InspectorWidget(Widget):
    def __init__(
        self,
        name: str,
        data_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        key_color: str | None = None,
        value_color: str | None = None,
    ):
        super().__init__(name)
        self.data_key = data_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.key_color = key_color
        self.value_color = value_color
        self.state["rows"] = []

    @property
    def _schema(self):
        return {
            "data_key": str,
            "fg_color": str,
            "bg_color": str,
            "key_color": str,
            "value_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        payload = resolve_path(context.data, self.data_key, None) if self.data_key else None
        self.state["rows"] = flatten_object(payload) if payload is not None else []
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
        rows = self.state.get("rows", [])
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "inspector",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        key_color = resolve_color_token(
            self.key_color or context.theme.widget_slot("inspector", "key_color", context.theme.color("text_muted")),
            context.theme,
            context.theme.color("text_muted"),
        )
        value_color = resolve_color_token(
            self.value_color or context.theme.widget_slot("inspector", "value_color", base_style.fg_color),
            context.theme,
            base_style.fg_color,
        )

        for row_index, (key, value) in enumerate(rows[: rect.height]):
            y = rect.y + row_index
            split = min(max(rect.width // 3, 10), max(rect.width - 1, 1))
            key_text = trim_text(key.ljust(split), split)
            value_text = trim_text(value, max(rect.width - split - 1, 0))
            buffer.write_text(rect.x, y, key_text, key_color, base_style.bg_color)
            if split < rect.width:
                buffer.write_text(rect.x + split + 1, y, value_text, value_color, base_style.bg_color)
