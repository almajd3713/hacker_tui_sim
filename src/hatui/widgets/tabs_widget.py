from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class TabsWidget(Widget):
    """Top-level tab container with optional visible tab strip."""

    def __init__(
        self,
        name: str,
        tabs: list[tuple[str, Widget]],
        show_tabs: bool = True,
        active_index: int = 0,
        fg_color: str | None = None,
        bg_color: str | None = None,
        active_fg_color: str | None = None,
        active_bg_color: str | None = None,
    ):
        children = [widget for _, widget in tabs]
        super().__init__(name, children)
        self.tabs = tabs
        self.show_tabs = show_tabs
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.active_fg_color = active_fg_color
        self.active_bg_color = active_bg_color
        self.state["active_index"] = max(0, min(active_index, len(tabs) - 1)) if tabs else 0

    @property
    def _schema(self):
        return {
            "tabs": list,
            "show_tabs": bool,
            "active_index": int,
            "fg_color": str,
            "bg_color": str,
            "active_fg_color": str,
            "active_bg_color": str,
        }

    @property
    def active_index(self) -> int:
        return self.state["active_index"]

    @property
    def active_child(self) -> Widget | None:
        if not self.children:
            return None
        return self.children[self.active_index]

    def next_tab(self):
        if self.children:
            self.state["active_index"] = (self.active_index + 1) % len(self.children)

    def previous_tab(self):
        if self.children:
            self.state["active_index"] = (self.active_index - 1) % len(self.children)

    def allocate_children(self, width: int, height: int):
        if not self.active_child:
            return
        tab_bar_height = 1 if self.show_tabs and height > 0 else 0
        self.active_child.allocate(width, max(height - tab_bar_height, 0))

    def update(self, delta_time: float, context: WidgetContext):
        if self.active_child is not None:
            self.active_child.update(delta_time, context)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if not self.active_child:
            return
        child_y = y + (1 if self.show_tabs and self.properties["rect"].height > 0 else 0)
        self.active_child.layout(x, child_y, context)

    def _strip_styles(self, context: WidgetContext) -> tuple[Style, Style]:
        base = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.border.fg_color,
                bg_color=context.theme.border.bg_color,
            ),
        )
        active = resolve_style(
            fg_color=self.active_fg_color,
            bg_color=self.active_bg_color,
            fallback=Style(
                fg_color="#ffffff",
                bg_color="#3a3f58",
            ),
        )
        return base, active

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        if self.show_tabs:
            base_style, active_style = self._strip_styles(context)
            for x in range(rect.width):
                buffer.write(rect.x + x, rect.y, " ", base_style.fg_color, base_style.bg_color)

            cursor_x = rect.x
            for index, (title, _) in enumerate(self.tabs):
                label = f"[{title}]" if index == self.active_index else f" {title} "
                style = active_style if index == self.active_index else base_style
                clipped = label[: max(rect.x + rect.width - cursor_x, 0)]
                if not clipped:
                    break
                buffer.write_text(cursor_x, rect.y, clipped, style.fg_color, style.bg_color)
                cursor_x += len(clipped)
                if cursor_x < rect.x + rect.width:
                    buffer.write(cursor_x, rect.y, " ", base_style.fg_color, base_style.bg_color)
                    cursor_x += 1

        if self.active_child:
            self.active_child.paint(buffer, context)
