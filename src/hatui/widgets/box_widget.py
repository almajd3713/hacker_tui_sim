from hatui.core.style import BorderTheme
from hatui.core.widget import Widget, WidgetContext
from hatui.widgets.border_widget import BorderWidget


class BoxWidget(BorderWidget):
    """Bordered container with optional title rendered on the top edge."""

    def __init__(
        self,
        name: str,
        child: Widget | None = None,
        padding: int = 0,
        title: str | None = None,
        title_key: str | None = None,
        title_align: str = "left",
        style: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        font_name: str | None = None,
    ):
        super().__init__(
            name=name,
            child=child,
            padding=padding,
            style=style,
            fg_color=fg_color,
            bg_color=bg_color,
            font_name=font_name,
        )
        self.title = title
        self.title_key = title_key
        self.title_align = title_align
        self.state["title"] = title or ""

    @property
    def _schema(self):
        schema = dict(super()._schema)
        schema.update(
            {
                "title": str,
                "title_key": str,
                "title_align": str,
            }
        )
        return schema

    def update(self, delta_time: float, context: WidgetContext):
        if self.title_key is not None:
            self.state["title"] = str(context.data.get(self.title_key, ""))
        else:
            self.state["title"] = self.title or ""
        super().update(delta_time, context)

    def _title_text(self, width: int) -> str:
        title = self.state.get("title", "")
        if not title or width <= 0:
            return ""
        available = max(width - 4, 0)
        titled = f" {title[:available]} "
        return titled

    def _title_x(self, rect_width: int, title: str, rect_x: int) -> int:
        if self.title_align == "center":
            return rect_x + max((rect_width - len(title)) // 2, 0)
        if self.title_align == "right":
            return rect_x + max(rect_width - len(title) - 1, 0)
        return rect_x + 1

    def paint(self, buffer, context: WidgetContext):
        super().paint(buffer, context)

        rect = self.properties["rect"]
        title = self._title_text(rect.width)
        if not title or rect.width < 4 or rect.height < 1:
            return

        theme = self._resolved_theme(context)
        title_x = self._title_x(rect.width, title, rect.x)
        buffer.write_text(title_x, rect.y, title, theme.fg_color, theme.bg_color)
