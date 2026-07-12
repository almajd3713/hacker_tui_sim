from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.selection import StoreSelectionBinding, move_selected_index, read_selected_index, sync_selection


class TableWidget(Widget):
    """Structured read-only table with headers and aligned columns."""

    def __init__(
        self,
        name: str,
        columns: list[dict],
        rows_key: str | None = None,
        show_header: bool = True,
        selectable: bool = False,
        selected_index: int = 0,
        selected_index_key: str | None = None,
        selected_row_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        header_color: str | None = None,
        selected_fg_color: str | None = None,
        selected_bg_color: str | None = None,
    ):
        super().__init__(name)
        self.columns = columns
        self.rows_key = rows_key
        self.show_header = show_header
        self.selectable = selectable
        self.selected_index = max(selected_index, 0)
        self.selected_index_key = selected_index_key
        self.selected_row_key = selected_row_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.header_color = header_color
        self.selected_fg_color = selected_fg_color
        self.selected_bg_color = selected_bg_color
        self.state["rows"] = []
        self.state["selected_index"] = self.selected_index

    @property
    def _schema(self):
        return {
            "columns": list,
            "rows_key": str,
            "show_header": bool,
            "selectable": bool,
            "selected_index": int,
            "selected_index_key": str,
            "selected_row_key": str,
            "fg_color": str,
            "bg_color": str,
            "header_color": str,
            "selected_fg_color": str,
            "selected_bg_color": str,
        }

    def default_focusable(self) -> bool:
        return self.selectable

    def default_keybindings(self) -> list[dict]:
        if not self.selectable:
            return []
        return [
            {"key": "up", "action": "select_prev"},
            {"key": "down", "action": "select_next"},
            {"key": "j", "action": "select_next"},
            {"key": "k", "action": "select_prev"},
            {"key": "g", "action": "select_first"},
            {"key": "shift+g", "action": "select_last"},
        ]

    def _sync_selection(self, context: WidgetContext):
        rows = self.state.get("rows", [])
        bindings: list[StoreSelectionBinding] = []
        if self.selected_row_key is not None:
            bindings.append(
                StoreSelectionBinding(
                    self.selected_row_key,
                    lambda: self.state.get("rows", [])[self.state.get("selected_index", 0)],
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

    def update(self, delta_time: float, context: WidgetContext):
        rows = resolve_path(context.data, self.rows_key, []) if self.rows_key is not None else []
        self.state["rows"] = list(rows)
        if self.selected_index_key is not None:
            self.state["selected_index"] = read_selected_index(
                context,
                self.selected_index_key,
                self.state.get("selected_index", self.selected_index),
            )
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

    def _column_widths(self, total_width: int) -> list[int]:
        if not self.columns or total_width <= 0:
            return []

        separators = len(self.columns) - 1
        fixed = sum(col.get("width", 0) for col in self.columns if col.get("width") is not None)
        flex_columns = [col for col in self.columns if col.get("width") is None]
        available = max(total_width - separators - fixed, 0)
        flex_width = available // len(flex_columns) if flex_columns else 0
        remainder = available % len(flex_columns) if flex_columns else 0

        widths = []
        flex_index = 0
        for col in self.columns:
            width = col.get("width")
            if width is None:
                width = flex_width + (1 if flex_index < remainder else 0)
                flex_index += 1
            widths.append(max(width, 1))
        return widths

    def _format_cell(self, value, width: int, align: str) -> str:
        text = str(value)[:width]
        if align == "right":
            return text.rjust(width)
        if align == "center":
            return text.center(width)
        return text.ljust(width)

    def measure_content(self, width: int, height: int) -> tuple[int, int]:
        header_rows = 1 if self.show_header else 0
        return max(width, 0), max(len(self.state.get("rows", [])) + header_rows, height, 0)

    def _move_selection(self, delta: int, context: WidgetContext):
        rows = self.state.get("rows", [])
        self.state["selected_index"] = move_selected_index(self.state.get("selected_index", 0), delta, rows)
        self._sync_selection(context)

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if not self.selectable:
            return False
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
            rows = self.state.get("rows", [])
            if rows:
                self.state["selected_index"] = len(rows) - 1
                self._sync_selection(context)
            return True
        return False

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0 or not self.columns:
            return

        base_style = themed_style(
            context.theme,
            "table",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        header_style = themed_style(
            context.theme,
            "table",
            fg_color=self.header_color or context.theme.widget_slot("table", "header_color", context.theme.border.fg_color),
            bg_color=base_style.bg_color,
            fallback=base_style,
        )
        selected_style = themed_style(
            context.theme,
            "table",
            fg_color=self.selected_fg_color or self.focus_fg_color or context.theme.widget_slot("table", "selected_fg_color", context.theme.color("selection_fg", "#ffffff")),
            bg_color=self.selected_bg_color or self.focus_bg_color or context.theme.widget_slot("table", "selected_bg_color", context.theme.color("selection_bg", context.theme.border.bg_color)),
            fallback=base_style,
        )

        widths = self._column_widths(rect.width)
        if not widths:
            return

        y = rect.y
        if self.show_header and y < rect.y + rect.height:
            parts = []
            for column, width in zip(self.columns, widths):
                parts.append(self._format_cell(column.get("title", ""), width, column.get("align", "left")))
            header = " ".join(parts)[: rect.width]
            buffer.fill_row(rect.x, y, rect.width, header_style.fg_color, header_style.bg_color, style=header_style)
            buffer.write_text(rect.x, y, header, header_style.fg_color, header_style.bg_color, style=header_style)
            y += 1

        rows = self.state.get("rows", [])
        visible_capacity = max(rect.y + rect.height - y, 0)
        start_index = 0
        if self.selectable and visible_capacity > 0 and rows:
            selected_index = self.state.get("selected_index", 0)
            start_index = min(max(selected_index - visible_capacity + 1, 0), max(len(rows) - visible_capacity, 0))
        visible_rows = rows[start_index : start_index + visible_capacity]
        for row_offset, row in enumerate(visible_rows):
            if y >= rect.y + rect.height:
                break

            parts = []
            for column, width in zip(self.columns, widths):
                key = column.get("key", "")
                align = column.get("align", "left")
                parts.append(self._format_cell(row.get(key, ""), width, align))
            row_style = selected_style if self.selectable and (start_index + row_offset) == self.state.get("selected_index", 0) else base_style
            buffer.fill_row(rect.x, y, rect.width, row_style.fg_color, row_style.bg_color, style=row_style)
            buffer.write_text(rect.x, y, " ".join(parts)[: rect.width], row_style.fg_color, row_style.bg_color, style=row_style)
            y += 1
