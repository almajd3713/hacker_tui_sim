from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext


class ModalWidget(Widget):
    """Centered modal surface with optional backdrop and route-pop close keys."""

    def __init__(
        self,
        name: str,
        child: Widget | None = None,
        width: int | None = None,
        height: int | None = None,
        min_width: int = 24,
        min_height: int = 6,
        margin: int = 2,
        backdrop_char: str = " ",
        backdrop_fg_color: str | None = None,
        backdrop_bg_color: str | None = "bright_black",
        show_backdrop: bool = True,
    ):
        children = [child] if child is not None else []
        super().__init__(name, children)
        self.width = width
        self.height = height
        self.min_width = max(min_width, 1)
        self.min_height = max(min_height, 1)
        self.margin = max(margin, 0)
        self.backdrop_char = backdrop_char[:1] if backdrop_char else " "
        self.backdrop_fg_color = backdrop_fg_color
        self.backdrop_bg_color = backdrop_bg_color
        self.show_backdrop = show_backdrop

    @property
    def _schema(self):
        return {
            "width": int,
            "height": int,
            "min_width": int,
            "min_height": int,
            "margin": int,
            "backdrop_char": str,
            "backdrop_fg_color": str,
            "backdrop_bg_color": str,
            "show_backdrop": bool,
        }

    def default_keybindings(self) -> list[dict]:
        return [
            {"key": "escape", "action": "route_pop"},
            {"key": "q", "action": "route_pop"},
        ]

    def configure_interaction(self, spec: dict | None = None):
        super().configure_interaction(spec)
        if spec is None or spec.get("focusable") is None:
            self.focusable = False
        return self

    @property
    def child(self) -> Widget | None:
        return self.children[0] if self.children else None

    def interaction_children(self) -> list[Widget]:
        return self.children

    def _child_size(self, width: int, height: int) -> tuple[int, int]:
        available_width = max(width - (self.margin * 2), 0)
        available_height = max(height - (self.margin * 2), 0)
        child_width = min(self.width if self.width is not None else available_width, available_width)
        child_height = min(self.height if self.height is not None else available_height, available_height)
        child_width = max(min(child_width, available_width), min(self.min_width, available_width) if available_width else 0)
        child_height = max(min(child_height, available_height), min(self.min_height, available_height) if available_height else 0)
        return child_width, child_height

    def allocate_children(self, width: int, height: int):
        if self.child is None:
            return
        child_width, child_height = self._child_size(width, height)
        self.child.allocate(child_width, child_height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if self.child is None:
            return
        rect = self.properties["rect"]
        child_rect = self.child.properties["rect"]
        child_x = x + max((rect.width - child_rect.width) // 2, 0)
        child_y = y + max((rect.height - child_rect.height) // 2, 0)
        self.child.layout(child_x, child_y, context)

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        if self.show_backdrop:
            backdrop_style = themed_style(
                context.theme,
                "modal",
                fg_color=self.backdrop_fg_color,
                bg_color=self.backdrop_bg_color,
                fallback=Style(
                    fg_color=context.theme.text.fg_color,
                    bg_color=self.backdrop_bg_color or context.theme.border.bg_color,
                ),
            )
            for y in range(rect.height):
                for x in range(rect.width):
                    buffer.write(rect.x + x, rect.y + y, self.backdrop_char, backdrop_style.fg_color, backdrop_style.bg_color)

        if self.child is not None:
            self.child.paint(buffer, context)
