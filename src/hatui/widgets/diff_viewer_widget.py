from __future__ import annotations

from difflib import unified_diff

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import trim_text


class DiffViewerWidget(Widget):
    def __init__(
        self,
        name: str,
        left_key: str | None = None,
        right_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
    ):
        super().__init__(name)
        self.left_key = left_key
        self.right_key = right_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.state["lines"] = []

    @property
    def _schema(self):
        return {"left_key": str, "right_key": str, "fg_color": str, "bg_color": str}

    def update(self, delta_time: float, context: WidgetContext):
        left = resolve_path(context.data, self.left_key, "") if self.left_key else ""
        right = resolve_path(context.data, self.right_key, "") if self.right_key else ""
        left_lines = str(left).splitlines()
        right_lines = str(right).splitlines()
        self.state["lines"] = list(unified_diff(left_lines, right_lines, fromfile="left", tofile="right", lineterm=""))
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

        base_style = themed_style(
            context.theme,
            "diff_viewer",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        added_color = resolve_color_token(
            context.theme.widget_slot("diff_viewer", "added_fg_color", context.theme.color("success")),
            context.theme,
            context.theme.color("success"),
        )
        removed_color = resolve_color_token(
            context.theme.widget_slot("diff_viewer", "removed_fg_color", context.theme.color("error")),
            context.theme,
            context.theme.color("error"),
        )
        hint_color = resolve_color_token(
            context.theme.widget_slot("diff_viewer", "hint_fg_color", context.theme.color("warn")),
            context.theme,
            context.theme.color("warn"),
        )

        for row_index, line in enumerate(lines[: rect.height]):
            color = base_style.fg_color
            if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                color = hint_color
            elif line.startswith("+"):
                color = added_color
            elif line.startswith("-"):
                color = removed_color
            buffer.write_text(rect.x, rect.y + row_index, trim_text(line, rect.width), color, base_style.bg_color)
