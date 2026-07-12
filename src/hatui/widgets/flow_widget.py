from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import trim_text


class FlowWidget(Widget):
    def __init__(
        self,
        name: str,
        edges_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.edges_key = edges_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["edges"] = []

    @property
    def _schema(self):
        return {"edges_key": str, "fg_color": str, "bg_color": str}

    def update(self, delta_time: float, context: WidgetContext):
        payload = resolve_path(context.data, self.edges_key, []) if self.edges_key else []
        self.state["edges"] = list(payload) if isinstance(payload, list) else []
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
        edges = self.state.get("edges", [])
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "flow",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        active_color = resolve_color_token(
            context.theme.widget_slot("flow", "active_fg_color", context.theme.color("accent")),
            context.theme,
            context.theme.color("accent"),
        )
        idle_color = resolve_color_token(
            context.theme.widget_slot("flow", "idle_fg_color", context.theme.color("text_muted")),
            context.theme,
            context.theme.color("text_muted"),
        )

        for row_index, edge in enumerate(edges[: rect.height]):
            if not isinstance(edge, dict):
                line = str(edge)
                color = base_style.fg_color
            else:
                label = f" {edge.get('label')}" if edge.get("label") else ""
                line = f"{edge.get('from', '?')} -> {edge.get('to', '?')}{label}"
                state = edge.get("state", "idle")
                color = active_color if state in {"active", "online", "open"} else idle_color
            buffer.write_text(rect.x, rect.y + row_index, trim_text(line, rect.width), color, base_style.bg_color)
