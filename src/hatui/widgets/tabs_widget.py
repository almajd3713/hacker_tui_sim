from hatui.core.style import Style, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class TabsWidget(Widget):
    """Top-level tab container with optional visible tab strip."""

    def __init__(
        self,
        name: str,
        tabs: list[tuple[str, Widget, str]],
        show_tabs: bool = True,
        active_index: int = 0,
        fg_color: str | None = None,
        bg_color: str | None = None,
        active_fg_color: str | None = None,
        active_bg_color: str | None = None,
        route_key: str | None = None,
    ):
        children = [widget for _, widget, _ in tabs]
        super().__init__(name, children)
        self.tabs = tabs
        self.show_tabs = show_tabs
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.active_fg_color = active_fg_color
        self.active_bg_color = active_bg_color
        self.route_key = route_key
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
            "route_key": str,
        }

    @property
    def active_index(self) -> int:
        return self.state["active_index"]

    @property
    def active_child(self) -> Widget | None:
        if not self.children:
            return None
        return self.children[self.active_index]

    @property
    def active_route(self) -> str | None:
        if not self.tabs or self.active_index >= len(self.tabs):
            return None
        return self._tab_route_name(self.active_index)

    def default_focusable(self) -> bool:
        return True

    def default_keybindings(self) -> list[dict]:
        return [
            {"key": "left", "action": "activate_prev"},
            {"key": "right", "action": "activate_next"},
        ]

    def next_tab(self, context: WidgetContext | None = None):
        if self.children:
            self._set_active_index((self.active_index + 1) % len(self.children), context)

    def previous_tab(self, context: WidgetContext | None = None):
        if self.children:
            self._set_active_index((self.active_index - 1) % len(self.children), context)

    def _tab_route_name(self, index: int) -> str:
        _, _, route = self.tabs[index]
        return route

    def _set_active_index(self, index: int, context: WidgetContext | None = None):
        if not self.children:
            return
        index = max(0, min(index, len(self.children) - 1))
        self.state["active_index"] = index
        route = self._tab_route_name(index)
        if self.route_key is not None and context is not None:
            self.root.perform_action("store_set", {"path": self.route_key, "value": route}, context)
        elif context is not None:
            self.root.perform_action("route_set", {"route": route}, context)

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if action == "activate_next":
            self.next_tab(context)
            return True
        if action == "activate_prev":
            self.previous_tab(context)
            return True
        if action == "activate_index":
            index = int(payload.get("index", self.active_index))
            if not self.children:
                return False
            self._set_active_index(index, context)
            return True
        return False

    def interaction_children(self) -> list[Widget]:
        return [self.active_child] if self.active_child is not None else []

    def update(self, delta_time: float, context: WidgetContext):
        routes = {index: route for index, (_, _, route) in enumerate(self.tabs)}
        self.state["routes"] = routes
        if self.route_key is not None:
            route = resolve_path(context.data, self.route_key, None)
        else:
            route = resolve_path(context.data, "_router.current", None)
        if route:
            route_names = list(routes.values())
            if route in route_names:
                self.state["active_index"] = route_names.index(route)
        if self.active_child is not None:
            self.active_child.update(delta_time, context)

    def allocate_children(self, width: int, height: int):
        if not self.active_child:
            return
        tab_bar_height = 1 if self.show_tabs and height > 0 else 0
        self.active_child.allocate(width, max(height - tab_bar_height, 0))

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if not self.active_child:
            return
        child_y = y + (1 if self.show_tabs and self.properties["rect"].height > 0 else 0)
        self.active_child.layout(x, child_y, context)

    def _strip_styles(self, context: WidgetContext) -> tuple[Style, Style]:
        focused_fg = self.focus_fg_color if self.is_focused(context) and self.focus_fg_color is not None else None
        focused_bg = self.focus_bg_color if self.is_focused(context) and self.focus_bg_color is not None else None
        base = themed_style(
            context.theme,
            "tabs",
            fg_color=focused_fg or self.fg_color,
            bg_color=focused_bg or self.bg_color,
            fallback=Style(
                fg_color=context.theme.border.fg_color,
                bg_color=context.theme.border.bg_color,
            ),
        )
        active = themed_style(
            context.theme,
            "tabs",
            fg_color=focused_fg or self.active_fg_color,
            bg_color=focused_bg or self.active_bg_color,
            fg_slot="active_fg_color",
            bg_slot="active_bg_color",
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
            for index, (title, _, _) in enumerate(self.tabs):
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
