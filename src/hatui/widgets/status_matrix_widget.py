from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import trim_text


class StatusMatrixWidget(Widget):
    """Dense selectable grid of operational entities."""

    def __init__(
        self,
        name: str,
        items: list | None = None,
        items_key: str | None = None,
        columns: int = 2,
        density: str = "compact",
        selectable: bool = False,
        selected_index: int = 0,
        selected_index_key: str | None = None,
        selected_item_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        active_fg_color: str | None = None,
        active_bg_color: str | None = None,
    ):
        super().__init__(name)
        self.items = list(items or [])
        self.items_key = items_key
        self.columns = max(int(columns), 1)
        self.density = density
        self.selectable = selectable
        self.selected_index = max(int(selected_index), 0)
        self.selected_index_key = selected_index_key
        self.selected_item_key = selected_item_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.active_fg_color = active_fg_color
        self.active_bg_color = active_bg_color
        self.state["items"] = list(self.items)
        self.state["selected_index"] = self.selected_index

    @property
    def _schema(self):
        return {
            "items": list,
            "items_key": str,
            "columns": int,
            "density": str,
            "selectable": bool,
            "selected_index": int,
            "selected_index_key": str,
            "selected_item_key": str,
            "fg_color": str,
            "bg_color": str,
            "active_fg_color": str,
            "active_bg_color": str,
        }

    def default_focusable(self) -> bool:
        return self.selectable

    def default_keybindings(self) -> list[dict]:
        if not self.selectable:
            return []
        return [
            {"key": "left", "action": "select_left"},
            {"key": "right", "action": "select_right"},
            {"key": "up", "action": "select_up"},
            {"key": "down", "action": "select_down"},
            {"key": "h", "action": "select_left"},
            {"key": "l", "action": "select_right"},
            {"key": "k", "action": "select_up"},
            {"key": "j", "action": "select_down"},
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
            self.root.perform_action("store_set", {"path": self.selected_index_key, "value": self.state["selected_index"]}, context)
        if self.selected_item_key is not None:
            self.root.perform_action("store_set", {"path": self.selected_item_key, "value": self.selected_item()}, context)

    def selected_item(self):
        items = self.state.get("items", [])
        index = self.state.get("selected_index", 0)
        if not items or index < 0 or index >= len(items):
            return None
        return items[index]

    def update(self, delta_time: float, context: WidgetContext):
        self.state["items"] = list(resolve_path(context.data, self.items_key, [])) if self.items_key is not None else list(self.items)
        self.state["selected_index"] = self._read_selected_index(context)
        self._sync_selection(context)
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

    def _cell_height(self) -> int:
        return 1 if self.density == "compact" else 2

    def _move_selection(self, delta: int, context: WidgetContext):
        items = self.state.get("items", [])
        if not items:
            return
        self.state["selected_index"] = max(0, min(self.state.get("selected_index", 0) + delta, len(items) - 1))
        self._sync_selection(context)

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if not self.selectable:
            return False
        if action == "select_left":
            self._move_selection(-1, context)
            return True
        if action == "select_right":
            self._move_selection(1, context)
            return True
        if action == "select_up":
            self._move_selection(-self.columns, context)
            return True
        if action == "select_down":
            self._move_selection(self.columns, context)
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

    def _item_color(self, item: dict, context: WidgetContext, default: str) -> str:
        severity = str(item.get("severity") or item.get("state") or "info").lower()
        slot = f"{severity}_fg_color"
        return resolve_color_token(context.theme.widget_slot("status_matrix", slot, context.theme.color(severity, default)), context.theme, default)

    def _item_bg(self, item: dict, context: WidgetContext, default: str) -> str:
        severity = str(item.get("severity") or item.get("state") or "").lower()
        slot = f"{severity}_bg_color"
        return resolve_color_token(context.theme.widget_slot("status_matrix", slot, default), context.theme, default)

    def _line_text(self, item: dict, width: int, detail: bool = False) -> str:
        label = str(item.get("label") or item.get("name") or item.get("title") or item.get("id") or "--")
        value = item.get("value")
        meta = item.get("meta")
        state = str(item.get("state", "")).upper()
        if detail:
            detail_text = meta if meta is not None else value if value is not None else state
            return trim_text(detail_text or "", width)
        if value is not None:
            return trim_text(f"{state[:1]} {label} {value}", width)
        if meta is not None:
            return trim_text(f"{state[:1]} {label} {meta}", width)
        return trim_text(f"{state[:1]} {label}", width)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "status_matrix",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        selected_style = themed_style(
            context.theme,
            "status_matrix",
            fg_color=self.active_fg_color or self.focus_fg_color or context.theme.widget_slot("status_matrix", "active_fg_color", context.theme.color("selection_fg")),
            bg_color=self.active_bg_color or self.focus_bg_color or context.theme.widget_slot("status_matrix", "active_bg_color", context.theme.color("selection_bg")),
            fallback=base_style,
        )

        items = self.state.get("items", [])
        cell_height = self._cell_height()
        rows_visible = max(rect.height // cell_height, 1)
        visible_capacity = rows_visible * self.columns
        selected_index = self.state.get("selected_index", 0)
        start_row = 0
        if self.selectable and visible_capacity > 0 and items:
            selected_row = selected_index // self.columns
            start_row = min(max(selected_row - rows_visible + 1, 0), max((len(items) - 1) // self.columns - rows_visible + 1, 0))
        start_index = start_row * self.columns
        visible_items = items[start_index : start_index + visible_capacity]
        cell_width = max(rect.width // self.columns, 1)

        for offset, item in enumerate(visible_items):
            if not isinstance(item, dict):
                item = {"label": str(item), "state": "info"}
            absolute_index = start_index + offset
            column = offset % self.columns
            row = offset // self.columns
            x = rect.x + column * cell_width
            y = rect.y + row * cell_height
            width = rect.width - column * cell_width if column == self.columns - 1 else cell_width
            active = self.selectable and absolute_index == selected_index
            fg = selected_style.fg_color if active else self._item_color(item, context, base_style.fg_color)
            bg = selected_style.bg_color if active else self._item_bg(item, context, base_style.bg_color)
            for line_offset in range(cell_height):
                if y + line_offset >= rect.y + rect.height:
                    break
                fill = " " * width
                buffer.write_text(x, y + line_offset, fill, fg, bg)
            buffer.write_text(x, y, self._line_text(item, width), fg, bg)
            if cell_height > 1 and y + 1 < rect.y + rect.height:
                buffer.write_text(x, y + 1, self._line_text(item, width, detail=True), fg, bg)

