from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class HexDumpWidget(Widget):
    """Read-only hex/ascii memory view."""

    def __init__(
        self,
        name: str,
        data_key: str | None = None,
        bytes_per_row: int = 8,
        fg_color: str | None = None,
        bg_color: str | None = None,
        offset_color: str | None = None,
    ):
        super().__init__(name)
        self.data_key = data_key
        self.bytes_per_row = max(bytes_per_row, 1)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.offset_color = offset_color
        self.state["data"] = []

    @property
    def _schema(self):
        return {
            "data_key": str,
            "bytes_per_row": int,
            "fg_color": str,
            "bg_color": str,
            "offset_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        data = resolve_path(context.data, self.data_key, []) if self.data_key is not None else []
        self.state["data"] = list(data)
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
        data = self.state.get("data", [])
        if rect.width <= 0 or rect.height <= 0 or not data:
            return

        base_style = themed_style(
            context.theme,
            "hex_dump",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        offset_style = themed_style(
            context.theme,
            "hex_dump",
            fg_color=self.offset_color or context.theme.widget_slot("hex_dump", "offset_color", context.theme.border.fg_color),
            bg_color=base_style.bg_color,
            fallback=base_style,
        )

        rows = [data[i : i + self.bytes_per_row] for i in range(0, len(data), self.bytes_per_row)]
        for row_index, chunk in enumerate(rows[: rect.height]):
            offset = f"{row_index * self.bytes_per_row:04x}: "
            hex_part = " ".join(f"{int(value) & 0xff:02x}" for value in chunk)
            ascii_part = "".join(chr(int(value) & 0xff) if 32 <= (int(value) & 0xff) < 127 else "." for value in chunk)

            offset_text = offset[: rect.width]
            buffer.write_text(rect.x, rect.y + row_index, offset_text, offset_style.fg_color, offset_style.bg_color)

            remaining = rect.width - len(offset_text)
            if remaining <= 0:
                continue

            body = f"{hex_part}  {ascii_part}"[:remaining]
            buffer.write_text(rect.x + len(offset_text), rect.y + row_index, body, base_style.fg_color, base_style.bg_color)
