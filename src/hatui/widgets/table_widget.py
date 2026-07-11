from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class TableWidget(Widget):
    """Structured read-only table with headers and aligned columns."""

    def __init__(
        self,
        name: str,
        columns: list[dict],
        rows_key: str | None = None,
        show_header: bool = True,
        fg_color: str | None = None,
        bg_color: str | None = None,
        header_color: str | None = None,
    ):
        super().__init__(name)
        self.columns = columns
        self.rows_key = rows_key
        self.show_header = show_header
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.header_color = header_color
        self.state["rows"] = []

    @property
    def _schema(self):
        return {
            "columns": list,
            "rows_key": str,
            "show_header": bool,
            "fg_color": str,
            "bg_color": str,
            "header_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        rows = resolve_path(context.data, self.rows_key, []) if self.rows_key is not None else []
        self.state["rows"] = list(rows)
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

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0 or not self.columns:
            return

        base_style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        header_style = resolve_style(
            fg_color=self.header_color or context.theme.border.fg_color,
            bg_color=base_style.bg_color,
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
            buffer.write_text(rect.x, y, header, header_style.fg_color, header_style.bg_color)
            y += 1

        visible_rows = self.state.get("rows", [])[: max(rect.y + rect.height - y, 0)]
        for row in visible_rows:
            if y >= rect.y + rect.height:
                break

            parts = []
            for column, width in zip(self.columns, widths):
                key = column.get("key", "")
                align = column.get("align", "left")
                parts.append(self._format_cell(row.get(key, ""), width, align))
            buffer.write_text(rect.x, y, " ".join(parts)[: rect.width], base_style.fg_color, base_style.bg_color)
            y += 1
