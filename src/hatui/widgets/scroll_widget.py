from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class ScrollWidget(Widget):
    """Viewport container that clips and offsets a single oversized child."""

    def __init__(
        self,
        name: str,
        child: Widget | None = None,
        scroll_x: int = 0,
        scroll_y: int = 0,
        scroll_x_key: str | None = None,
        scroll_y_key: str | None = None,
        content_width: int | None = None,
        content_height: int | None = None,
        content_width_key: str | None = None,
        content_height_key: str | None = None,
        show_scrollbar: bool = True,
        scrollbar_fg_color: str | None = None,
        scrollbar_bg_color: str | None = None,
    ):
        children = [child] if child is not None else []
        super().__init__(name, children)
        self.scroll_x = max(scroll_x, 0)
        self.scroll_y = max(scroll_y, 0)
        self.scroll_x_key = scroll_x_key
        self.scroll_y_key = scroll_y_key
        self.content_width = content_width
        self.content_height = content_height
        self.content_width_key = content_width_key
        self.content_height_key = content_height_key
        self.show_scrollbar = show_scrollbar
        self.scrollbar_fg_color = scrollbar_fg_color
        self.scrollbar_bg_color = scrollbar_bg_color
        self.state["scroll_x"] = self.scroll_x
        self.state["scroll_y"] = self.scroll_y
        self.state["content_width"] = content_width or 0
        self.state["content_height"] = content_height or 0

    @property
    def _schema(self):
        return {
            "scroll_x": int,
            "scroll_y": int,
            "scroll_x_key": str,
            "scroll_y_key": str,
            "content_width": int,
            "content_height": int,
            "content_width_key": str,
            "content_height_key": str,
            "show_scrollbar": bool,
            "scrollbar_fg_color": str,
            "scrollbar_bg_color": str,
        }

    def default_focusable(self) -> bool:
        return True

    def default_keybindings(self) -> list[dict]:
        return [
            {"key": "up", "action": "scroll_up"},
            {"key": "down", "action": "scroll_down"},
            {"key": "left", "action": "scroll_left"},
            {"key": "right", "action": "scroll_right"},
            {"key": "j", "action": "scroll_down"},
            {"key": "k", "action": "scroll_up"},
            {"key": "g", "action": "scroll_top"},
            {"key": "shift+g", "action": "scroll_bottom"},
        ]

    @property
    def child(self) -> Widget | None:
        return self.children[0] if self.children else None

    def _viewport_width(self) -> int:
        rect = self.properties["rect"]
        reserved = 1 if self.show_scrollbar and rect.width > 1 else 0
        return max(rect.width - reserved, 0)

    def _read_scroll_value(self, key_path: str | None, fallback: int, context: WidgetContext) -> int:
        if key_path is None:
            return fallback
        value = resolve_path(context.data, key_path, fallback)
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return fallback

    def _write_scroll_value(self, axis: str, value: int, context: WidgetContext):
        clamped = max(int(value), 0)
        self.state[f"scroll_{axis}"] = clamped
        key_path = self.scroll_x_key if axis == "x" else self.scroll_y_key
        if key_path is not None:
            self.root.perform_action("store_set", {"path": key_path, "value": clamped}, context)

    def _clamp_scroll(self, context: WidgetContext):
        rect = self.properties["rect"]
        viewport_width = self._viewport_width()
        viewport_height = rect.height
        max_x = max(self.state.get("content_width", 0) - viewport_width, 0)
        max_y = max(self.state.get("content_height", 0) - viewport_height, 0)
        self.state["scroll_x"] = max(0, min(self.state.get("scroll_x", 0), max_x))
        self.state["scroll_y"] = max(0, min(self.state.get("scroll_y", 0), max_y))
        if self.scroll_x_key is not None:
            self.root.perform_action("store_set", {"path": self.scroll_x_key, "value": self.state["scroll_x"]}, context)
        if self.scroll_y_key is not None:
            self.root.perform_action("store_set", {"path": self.scroll_y_key, "value": self.state["scroll_y"]}, context)

    def update(self, delta_time: float, context: WidgetContext):
        self.state["scroll_x"] = self._read_scroll_value(self.scroll_x_key, self.state.get("scroll_x", self.scroll_x), context)
        self.state["scroll_y"] = self._read_scroll_value(self.scroll_y_key, self.state.get("scroll_y", self.scroll_y), context)
        if self.content_width_key is not None:
            self.state["content_width"] = int(resolve_path(context.data, self.content_width_key, self.content_width or 0) or 0)
        elif self.content_width is not None:
            self.state["content_width"] = self.content_width
        if self.content_height_key is not None:
            self.state["content_height"] = int(resolve_path(context.data, self.content_height_key, self.content_height or 0) or 0)
        elif self.content_height is not None:
            self.state["content_height"] = self.content_height

        if self.child is not None:
            self.child.update(delta_time, context)

    def allocate_children(self, width: int, height: int):
        if self.child is None:
            return
        viewport_width = max(width - (1 if self.show_scrollbar and width > 1 else 0), 0)
        measured_width, measured_height = self.child.measure_content(viewport_width, height)
        content_width = max(self.state.get("content_width", 0), measured_width, viewport_width)
        content_height = max(self.state.get("content_height", 0), measured_height, height)
        self.state["content_width"] = content_width
        self.state["content_height"] = content_height
        self.child.allocate(content_width, content_height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if self.child is None:
            return
        self._clamp_scroll(context)
        self.child.layout(x - self.state.get("scroll_x", 0), y - self.state.get("scroll_y", 0), context)

    def _scroll_by(self, dx: int, dy: int, context: WidgetContext):
        self._write_scroll_value("x", self.state.get("scroll_x", 0) + dx, context)
        self._write_scroll_value("y", self.state.get("scroll_y", 0) + dy, context)
        self._clamp_scroll(context)

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if action == "scroll_up":
            self._scroll_by(0, -1, context)
            return True
        if action == "scroll_down":
            self._scroll_by(0, 1, context)
            return True
        if action == "scroll_left":
            self._scroll_by(-1, 0, context)
            return True
        if action == "scroll_right":
            self._scroll_by(1, 0, context)
            return True
        if action == "scroll_top":
            self._write_scroll_value("y", 0, context)
            return True
        if action == "scroll_bottom":
            self._write_scroll_value("y", self.state.get("content_height", 0), context)
            self._clamp_scroll(context)
            return True
        return False

    def _draw_scrollbar(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if not self.show_scrollbar or rect.width <= 1 or rect.height <= 0:
            return

        bar_x = rect.x + rect.width - 1
        viewport_height = rect.height
        content_height = max(self.state.get("content_height", viewport_height), 1)
        scroll_y = self.state.get("scroll_y", 0)
        base_style = themed_style(
            context.theme,
            "scroll",
            fg_color=self.scrollbar_fg_color,
            bg_color=self.scrollbar_bg_color,
            fallback=Style(
                fg_color=self.focus_fg_color or context.theme.border.fg_color,
                bg_color=self.focus_bg_color or context.theme.border.bg_color,
            ) if self.is_focused(context) else Style(
                fg_color=context.theme.border.fg_color,
                bg_color=context.theme.border.bg_color,
            ),
        )

        for offset in range(viewport_height):
            buffer.write(bar_x, rect.y + offset, "│", base_style.fg_color, base_style.bg_color)

        if content_height <= viewport_height:
            thumb_start = 0
            thumb_height = viewport_height
        else:
            thumb_height = max((viewport_height * viewport_height) // content_height, 1)
            max_scroll = max(content_height - viewport_height, 1)
            thumb_start = ((viewport_height - thumb_height) * scroll_y) // max_scroll

        thumb_style = themed_style(
            context.theme,
            "scroll",
            fg_color=(self.focus_fg_color or context.theme.color("focus_fg", "#ffffff")) if self.is_focused(context) else base_style.fg_color,
            bg_color=(self.focus_bg_color or context.theme.color("focus_bg", base_style.bg_color)) if self.is_focused(context) else base_style.bg_color,
            fallback=base_style,
        )
        for offset in range(thumb_height):
            y = rect.y + min(thumb_start + offset, viewport_height - 1)
            buffer.write(bar_x, y, "█", thumb_style.fg_color, thumb_style.bg_color)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0 or self.child is None:
            return
        viewport_width = self._viewport_width()
        with buffer.clip(rect.x, rect.y, viewport_width, rect.height):
            self.child.paint(buffer, context)
        self._draw_scrollbar(buffer, context)
