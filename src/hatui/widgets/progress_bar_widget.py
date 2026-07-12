from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import glyph


class ProgressBarWidget(Widget):
    """Horizontal progress bar with optional label and percentage."""

    def __init__(
        self,
        name: str,
        label: str = "",
        value_key: str | None = None,
        show_percentage: bool = True,
        fill_char: str = "█",
        empty_char: str = "░",
        fg_color: str | None = None,
        bg_color: str | None = None,
        fill_color: str | None = None,
    ):
        super().__init__(name)
        self.label = label
        self.value_key = value_key
        self.show_percentage = show_percentage
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.state["value"] = 0.0

    @property
    def _schema(self):
        return {
            "label": str,
            "value_key": str,
            "show_percentage": bool,
            "fill_char": str,
            "empty_char": str,
            "fg_color": str,
            "bg_color": str,
            "fill_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        value = resolve_path(context.data, self.value_key, 0.0) if self.value_key is not None else 0.0
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        self.state["value"] = max(0.0, min(numeric, 1.0))
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = 2 if height > 1 else max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = themed_style(
            context.theme,
            "progress_bar",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        fill_style = themed_style(
            context.theme,
            "progress_bar",
            fg_color=self.fill_color or context.theme.widget_slot("progress_bar", "fill_color", base_style.fg_color),
            bg_color=base_style.bg_color,
            fallback=base_style,
        )

        ratio = self.state["value"]
        line_y = rect.y
        if rect.height > 1 and self.label:
            buffer.fill_row(rect.x, rect.y, rect.width, base_style.fg_color, base_style.bg_color, style=base_style)
            label = self.label[: rect.width]
            if self.show_percentage:
                percent = f"{int(ratio * 100):3d}%"
                available = max(rect.width - len(percent) - 1, 0)
                label = label[:available]
                buffer.write_text(rect.x, rect.y, label, base_style.fg_color, base_style.bg_color)
                buffer.write_text(
                    rect.x + rect.width - len(percent),
                    rect.y,
                    percent,
                    base_style.fg_color,
                    base_style.bg_color,
                )
            else:
                buffer.write_text(rect.x, rect.y, label, base_style.fg_color, base_style.bg_color)
            line_y += 1

        fill_width = min(int(round(rect.width * ratio)), rect.width)
        fill_char = self.fill_char if self.fill_char != "█" else glyph(context, "fill", "#")
        empty_char = self.empty_char if self.empty_char != "░" else glyph(context, "empty_block", ".")
        buffer.fill_row(rect.x, line_y, rect.width, base_style.fg_color, base_style.bg_color, style=base_style)
        if fill_width > 0:
            buffer.write_text(rect.x, line_y, fill_char * fill_width, fill_style.fg_color, fill_style.bg_color)
        if fill_width < rect.width:
            buffer.write_text(
                rect.x + fill_width,
                line_y,
                empty_char * (rect.width - fill_width),
                base_style.fg_color,
                base_style.bg_color,
            )
