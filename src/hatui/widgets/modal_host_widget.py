from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path


class ModalHostWidget(Widget):
    """Host widget that renders a base screen plus route-driven modal overlays."""

    def __init__(
        self,
        name: str,
        child: Widget | None = None,
        modals: list[tuple[str, Widget]] | None = None,
        route_key: str = "_router.current",
    ):
        children = []
        self.base_child = child
        if child is not None:
            children.append(child)
        self.modals = list(modals or [])
        children.extend(widget for _, widget in self.modals)
        super().__init__(name, children)
        self.route_key = route_key
        self.state["active_modal_route"] = None

    @property
    def _schema(self):
        return {
            "route_key": str,
            "modals": list,
        }

    def _active_modal(self, context: WidgetContext) -> Widget | None:
        route = resolve_path(context.data, self.route_key, None)
        self.state["active_modal_route"] = route
        for modal_route, widget in self.modals:
            if route == modal_route:
                return widget
        return None

    def _root_context(self) -> WidgetContext | None:
        root = self.root
        return getattr(root, "context", None)

    def interaction_children(self) -> list[Widget]:
        context = self._root_context()
        active_modal = self._active_modal(context) if context is not None else None
        if active_modal is not None:
            return [active_modal]
        return [self.base_child] if self.base_child is not None else []

    def focusable_widgets(self) -> list[Widget]:
        context = self._root_context()
        active_modal = self._active_modal(context) if context is not None else None
        if active_modal is not None:
            return active_modal.focusable_widgets()
        if self.base_child is None:
            return []
        return self.base_child.focusable_widgets()

    def allocate_children(self, width: int, height: int):
        if self.base_child is not None:
            self.base_child.allocate(width, height)
        for _, modal in self.modals:
            modal.allocate(width, height)

    def update(self, delta_time: float, context: WidgetContext):
        if self.base_child is not None:
            self.base_child.update(delta_time, context)
        active_modal = self._active_modal(context)
        if active_modal is not None:
            active_modal.update(delta_time, context)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if self.base_child is not None:
            self.base_child.layout(x, y, context)
        active_modal = self._active_modal(context)
        if active_modal is not None:
            active_modal.layout(x, y, context)

    def paint(self, buffer, context: WidgetContext):
        if self.base_child is not None:
            self.base_child.paint(buffer, context)
        active_modal = self._active_modal(context)
        if active_modal is not None:
            active_modal.paint(buffer, context)
