from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class ListWidget(Widget):
    """Selectable vertical list with optional store-backed selection."""

    def __init__(
        self,
        name: str,
        items: list | None = None,
        items_key: str | None = None,
        selected_index: int = 0,
        selected_index_key: str | None = None,
        selected_value_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        selected_fg_color: str | None = None,
        selected_bg_color: str | None = None,
        bullet: str = "› ",
        show_bullet: bool = True,
    ):
        super().__init__(name)
        self.items = list(items or [])
        self.items_key = items_key
        self.selected_index = max(selected_index, 0)
        self.selected_index_key = selected_index_key
        self.selected_value_key = selected_value_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.selected_fg_color = selected_fg_color
        self.selected_bg_color = selected_bg_color
        self.bullet = bullet
        self.show_bullet = show_bullet
        self.state["items"] = list(self.items)
        self.state["selected_index"] = self.selected_index

    @property
    def _schema(self):
        return {
            "items": list,
            "items_key": str,
            "selected_index": int,
            "selected_index_key": str,
            "selected_value_key": str,
            "fg_color": str,
            "bg_color": str,
            "selected_fg_color": str,
            "selected_bg_color": str,
            "bullet": str,
            "show_bullet": bool,
        }

    def default_focusable(self) -> bool:
        return True

    def default_keybindings(self) -> list[dict]:
        return [
            {"key": "up", "action": "select_prev"},
            {"key": "down", "action": "select_next"},
            {"key": "j", "action": "select_next"},
            {"key": "k", "action": "select_prev"},
            {"key": "g", "action": "select_first"},
            {"key": "shift+g", "action": "select_last"},
        ]

    def _read_selected_index(self, context: WidgetContext) -> int:
        if self.selected_index_key is None:
            return self.state.get("selected_index", self.selected_index)
        value = resolve_path(context.data, self.selected_index_key, self.state.get("selected_index", self.selected_index))
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return self.state.get("selected_index", self.selected_index)

    def _sync_selection(self, context: WidgetContext):
        items = self.state.get("items", [])
        if not items:
            self.state["selected_index"] = 0
            return
        self.state["selected_index"] = max(0, min(self.state.get("selected_index", 0), len(items) - 1))
        if self.selected_index_key is not None:
            self.root.perform_action(
                "store_set",
                {"path": self.selected_index_key, "value": self.state["selected_index"]},
                context,
            )
        if self.selected_value_key is not None:
            self.root.perform_action(
                "store_set",
                {"path": self.selected_value_key, "value": self.selected_item()},
                context,
            )

    def update(self, delta_time: float, context: WidgetContext):
        if self.items_key is not None:
            self.state["items"] = list(resolve_path(context.data, self.items_key, []))
        else:
            self.state["items"] = list(self.items)
        self.state["selected_index"] = self._read_selected_index(context)
        self._sync_selection(context)
        super().update(delta_time, context)

    def selected_item(self):
        items = self.state.get("items", [])
        if not items:
            return None
        index = self.state.get("selected_index", 0)
        if index < 0 or index >= len(items):
            return None
        return items[index]

    def _display_text(self, item) -> str:
        if isinstance(item, dict):
            for key in ("label", "text", "title", "name", "value"):
                if key in item:
                    return str(item[key])
        return str(item)

    def _move_selection(self, delta: int, context: WidgetContext):
        items = self.state.get("items", [])
        if not items:
            return
        self.state["selected_index"] = max(0, min(self.state.get("selected_index", 0) + delta, len(items) - 1))
        self._sync_selection(context)

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if action == "select_prev":
            self._move_selection(-1, context)
            return True
        if action == "select_next":
            self._move_selection(1, context)
            return True
        if action == "select_first":
            self.state["selected_index"] = 0
            self._sync_selection(context)
            return True
        if action == "select_last":
            items = self.state.get("items", [])
            if items:
                self.state["selected_index"] = len(items) - 1
                self._sync_selection(context)
            return True
        return False

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def measure_content(self, width: int, height: int) -> tuple[int, int]:
        return max(width, 0), max(len(self.state.get("items", [])), height, 0)

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
                bg_color=context.theme.text.bg_color,
            ),
        )
        selected_style = resolve_style(
            fg_color=self.selected_fg_color or self.focus_fg_color or "#ffffff",
            bg_color=self.selected_bg_color or self.focus_bg_color or context.theme.border.bg_color,
            fallback=base_style,
        )

        items = self.state.get("items", [])[: rect.height]
        selected_index = self.state.get("selected_index", 0)
        bullet = self.bullet if self.show_bullet else ""
        bullet_width = len(bullet)

        for row_index, item in enumerate(items):
            active = row_index == selected_index
            style = selected_style if active else base_style
            prefix = bullet if active else (" " * bullet_width if bullet_width else "")
            text = self._display_text(item)
            line = f"{prefix}{text}"[: rect.width]
            buffer.write_text(rect.x, rect.y + row_index, line, style.fg_color, style.bg_color)
