from __future__ import annotations

from copy import deepcopy

from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.selection import StoreSelectionBinding, move_selected_index, read_selected_index, sync_selection
from hatui.widgets.visualization import glyph


class TreeWidget(Widget):
    """Selectable hierarchical tree with expand/collapse and optional activation."""

    def __init__(
        self,
        name: str,
        items: list | None = None,
        items_key: str | None = None,
        children_key: str = "children",
        id_key: str = "name",
        label_key: str = "label",
        selected_index: int = 0,
        selected_index_key: str | None = None,
        selected_item_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        selected_fg_color: str | None = None,
        selected_bg_color: str | None = None,
        indent: int = 2,
        leaf_symbol: str = "•",
        collapsed_symbol: str = "▸",
        expanded_symbol: str = "▾",
        auto_expand_root: bool = True,
        activate_action: str | None = None,
        activate_payload: dict | None = None,
        activate_target_field: str = "name",
        activate_payload_key: str = "target",
    ):
        super().__init__(name)
        self.items = list(items or [])
        self.items_key = items_key
        self.children_key = children_key
        self.id_key = id_key
        self.label_key = label_key
        self.selected_index = max(selected_index, 0)
        self.selected_index_key = selected_index_key
        self.selected_item_key = selected_item_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.selected_fg_color = selected_fg_color
        self.selected_bg_color = selected_bg_color
        self.indent = max(int(indent), 1)
        self.leaf_symbol = (leaf_symbol or "•")[:1]
        self.collapsed_symbol = (collapsed_symbol or "▸")[:1]
        self.expanded_symbol = (expanded_symbol or "▾")[:1]
        self.auto_expand_root = auto_expand_root
        self.activate_action = activate_action
        self.activate_payload = dict(activate_payload or {})
        self.activate_target_field = activate_target_field
        self.activate_payload_key = activate_payload_key
        self.state["items"] = list(self.items)
        self.state["visible_items"] = []
        self.state["selected_index"] = self.selected_index
        self.state["expanded_ids"] = set()

    @property
    def _schema(self):
        return {
            "items": list,
            "items_key": str,
            "children_key": str,
            "id_key": str,
            "label_key": str,
            "selected_index": int,
            "selected_index_key": str,
            "selected_item_key": str,
            "fg_color": str,
            "bg_color": str,
            "selected_fg_color": str,
            "selected_bg_color": str,
            "indent": int,
            "leaf_symbol": str,
            "collapsed_symbol": str,
            "expanded_symbol": str,
            "auto_expand_root": bool,
            "activate_action": str,
            "activate_payload": dict,
            "activate_target_field": str,
            "activate_payload_key": str,
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
            {"key": "left", "action": "collapse_or_parent"},
            {"key": "h", "action": "collapse_or_parent"},
            {"key": "right", "action": "expand_or_child"},
            {"key": "l", "action": "expand_or_child"},
            {"key": "enter", "action": "activate_selected"},
            {"key": "space", "action": "activate_selected"},
        ]

    def update(self, delta_time: float, context: WidgetContext):
        items = resolve_path(context.data, self.items_key, []) if self.items_key is not None else self.items
        self.state["items"] = list(items or [])
        self._ensure_auto_expand()
        self.state["visible_items"] = self._flatten_items(self.state["items"])
        self.state["selected_index"] = self._read_selected_index(context)
        self._sync_selection(context)
        super().update(delta_time, context)

    def _read_selected_index(self, context: WidgetContext) -> int:
        return read_selected_index(context, self.selected_index_key, self.state.get("selected_index", self.selected_index))

    def _ensure_auto_expand(self) -> None:
        if not self.auto_expand_root:
            return
        expanded_ids = set(self.state.get("expanded_ids", set()))
        for item in self.state.get("items", []):
            if self._children(item):
                item_id = self._item_id(item)
                if item_id:
                    expanded_ids.add(item_id)
        self.state["expanded_ids"] = expanded_ids

    def _children(self, item) -> list:
        if not isinstance(item, dict):
            return []
        children = item.get(self.children_key, [])
        return list(children) if isinstance(children, list) else []

    def _item_id(self, item) -> str:
        if isinstance(item, dict):
            value = item.get(self.id_key)
            if value is not None:
                return str(value)
        return str(item)

    def _display_text(self, item) -> str:
        if isinstance(item, dict):
            for key in (self.label_key, "label", "text", "title", "name", "value"):
                if key in item:
                    return str(item[key])
        return str(item)

    def _flatten_items(self, items: list, depth: int = 0, parent_id: str | None = None) -> list[dict]:
        rows: list[dict] = []
        expanded_ids = self.state.get("expanded_ids", set())
        for item in items:
            item_id = self._item_id(item)
            children = self._children(item)
            expanded = item_id in expanded_ids
            rows.append(
                {
                    "item": item,
                    "id": item_id,
                    "depth": depth,
                    "parent_id": parent_id,
                    "has_children": bool(children),
                    "expanded": expanded,
                }
            )
            if children and expanded:
                rows.extend(self._flatten_items(children, depth + 1, item_id))
        return rows

    def _sync_selection(self, context: WidgetContext):
        rows = self.state.get("visible_items", [])
        bindings: list[StoreSelectionBinding] = []
        if self.selected_item_key is not None:
            bindings.append(
                StoreSelectionBinding(
                    self.selected_item_key,
                    lambda: deepcopy(self.state.get("visible_items", [])[self.state.get("selected_index", 0)]["item"]),
                )
            )
        self.state["selected_index"] = sync_selection(
            self,
            context,
            rows,
            self.state.get("selected_index", 0),
            index_key=self.selected_index_key,
            bindings=bindings,
        )

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def _move_selection(self, delta: int, context: WidgetContext):
        rows = self.state.get("visible_items", [])
        self.state["selected_index"] = move_selected_index(self.state.get("selected_index", 0), delta, rows)
        self._sync_selection(context)

    def _selected_row(self) -> dict | None:
        rows = self.state.get("visible_items", [])
        if not rows:
            return None
        index = self.state.get("selected_index", 0)
        if 0 <= index < len(rows):
            return rows[index]
        return None

    def _collapse_or_parent(self, context: WidgetContext):
        row = self._selected_row()
        if row is None:
            return
        expanded_ids = set(self.state.get("expanded_ids", set()))
        if row["has_children"] and row["expanded"]:
            expanded_ids.discard(row["id"])
            self.state["expanded_ids"] = expanded_ids
            self.state["visible_items"] = self._flatten_items(self.state.get("items", []))
            self._sync_selection(context)
            return
        if row["parent_id"] is None:
            return
        for index, candidate in enumerate(self.state.get("visible_items", [])):
            if candidate["id"] == row["parent_id"]:
                self.state["selected_index"] = index
                self._sync_selection(context)
                return

    def _expand_or_child(self, context: WidgetContext):
        row = self._selected_row()
        if row is None or not row["has_children"]:
            return
        expanded_ids = set(self.state.get("expanded_ids", set()))
        if not row["expanded"]:
            expanded_ids.add(row["id"])
            self.state["expanded_ids"] = expanded_ids
            self.state["visible_items"] = self._flatten_items(self.state.get("items", []))
            self._sync_selection(context)
            return
        rows = self.state.get("visible_items", [])
        index = self.state.get("selected_index", 0)
        if index + 1 < len(rows) and rows[index + 1]["parent_id"] == row["id"]:
            self.state["selected_index"] = index + 1
            self._sync_selection(context)

    def _activate_selected(self, context: WidgetContext) -> bool:
        if not self.activate_action:
            return False
        row = self._selected_row()
        if row is None:
            return False
        payload = dict(self.activate_payload)
        item = row["item"]
        target_value = None
        if isinstance(item, dict):
            target_value = item.get(self.activate_target_field)
        if target_value is None:
            target_value = row["id"]
        payload[self.activate_payload_key] = target_value
        return self.perform_action(self.activate_action, payload, context)

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
            rows = self.state.get("visible_items", [])
            if rows:
                self.state["selected_index"] = len(rows) - 1
                self._sync_selection(context)
            return True
        if action == "collapse_or_parent":
            self._collapse_or_parent(context)
            return True
        if action == "expand_or_child":
            self._expand_or_child(context)
            return True
        if action == "activate_selected":
            return self._activate_selected(context)
        return False

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "tree",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        selected_style = themed_style(
            context.theme,
            "tree",
            fg_color=self.selected_fg_color or self.focus_fg_color or context.theme.widget_slot("tree", "selected_fg_color", context.theme.color("selection_fg", "#ffffff")),
            bg_color=self.selected_bg_color or self.focus_bg_color or context.theme.widget_slot("tree", "selected_bg_color", context.theme.color("selection_bg", context.theme.border.bg_color)),
            fallback=base_style,
        )

        rows = self.state.get("visible_items", [])[: rect.height]
        selected_index = self.state.get("selected_index", 0)
        for row_index, row in enumerate(rows):
            active = row_index == selected_index
            style = selected_style if active else base_style
            item = row["item"]
            text = self._display_text(item)
            branch = glyph(context, "bullet", "*") if self.leaf_symbol == "•" else self.leaf_symbol
            if row["has_children"]:
                branch = (
                    glyph(context, "expanded", "v") if self.expanded_symbol == "▾" else self.expanded_symbol
                ) if row["expanded"] else (
                    glyph(context, "collapsed", ">") if self.collapsed_symbol == "▸" else self.collapsed_symbol
                )
            prefix = (" " * (row["depth"] * self.indent)) + branch + " "
            line = f"{prefix}{text}"[: rect.width]
            y = rect.y + row_index
            buffer.fill_row(rect.x, y, rect.width, style.fg_color, style.bg_color, style=style)
            buffer.write_text(rect.x, y, line, style.fg_color, style.bg_color, style=style)
