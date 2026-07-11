from hatui.core.widget import Widget, WidgetContext
from hatui.core.style import Theme
from hatui.runtime.bindings import set_path

class RootWidget(Widget):
    """
    The RootWidget is the top-level widget in the widget hierarchy.
    It serves as the entry point for rendering and managing the entire widget tree.
    It has a single child widget, which is the main content of the application.
    """
    def __init__(
        self,
        name: str,
        children: list = None,
        theme: Theme | None = None,
        *,
        store=None,
        router=None,
    ):
        super().__init__(name, children)
        self.context = WidgetContext(name=name, version="1.0.0", theme=theme or Theme())
        self.store = store
        self.router = router
        self.configure_interaction(
            {
                "keybindings": [
                    {"key": "tab", "action": "focus_next"},
                    {"key": "shift+tab", "action": "focus_prev"},
                ]
            }
        )
    
    @property
    def _schema(self):
        return {
            "name": str,
            "version": str
        }
    
    def allocate_children(self, width: int, height: int):
        # Root widget has a single child, so allocate it to fill the entire space
        if self.children:
            self.children[0].allocate(width, height)
    
    def layout_children(self, x: int, y: int, context: WidgetContext):
        # Root widget has a single child, so layout it at the specified position
        if self.children:
            self.children[0].layout(x, y, context)

    def paint(self, buffer, context: WidgetContext):
        # Root widget has a single child, so paint it to the buffer
        if self.children:
            self.children[0].paint(buffer, context)

    def _focusable_widgets(self) -> list[Widget]:
        widgets = []
        for child in self.children:
            widgets.extend(child.focusable_widgets())
        return widgets

    def _sync_focus(self, context: WidgetContext):
        focusables = self._focusable_widgets()
        focused = context.focused_widget
        if focusables and focused not in {widget.name for widget in focusables}:
            context.focused_widget = focusables[0].name
        if not focusables:
            context.focused_widget = None
        context.data.setdefault("_ui", {})
        set_path(context.data, "_ui.focused_widget", context.focused_widget)
        if self.store is not None:
            self.store.sync_to_context(context)
        if self.router is not None:
            self.router.sync_to_context(context)

    def focus_first(self, context: WidgetContext) -> bool:
        focusables = self._focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        context.focused_widget = focusables[0].name
        self._sync_focus(context)
        return True

    def focus_last(self, context: WidgetContext) -> bool:
        focusables = self._focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        context.focused_widget = focusables[-1].name
        self._sync_focus(context)
        return True

    def focus_next(self, context: WidgetContext) -> bool:
        focusables = self._focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        names = [widget.name for widget in focusables]
        if context.focused_widget not in names:
            context.focused_widget = names[0]
        else:
            index = names.index(context.focused_widget)
            context.focused_widget = names[(index + 1) % len(names)]
        self._sync_focus(context)
        return True

    def focus_prev(self, context: WidgetContext) -> bool:
        focusables = self._focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        names = [widget.name for widget in focusables]
        if context.focused_widget not in names:
            context.focused_widget = names[-1]
        else:
            index = names.index(context.focused_widget)
            context.focused_widget = names[(index - 1) % len(names)]
        self._sync_focus(context)
        return True

    def focus_widget(self, target: str | None, context: WidgetContext) -> bool:
        if not target:
            return False
        for widget in self._focusable_widgets():
            if widget.name == target:
                context.focused_widget = target
                self._sync_focus(context)
                return True
        return False

    def route_set(self, route: str | None, context: WidgetContext) -> bool:
        if self.router is None or not route:
            return False
        changed = self.router.set_current(route)
        self._sync_focus(context)
        return changed

    def route_next(self, context: WidgetContext) -> bool:
        if self.router is None:
            return False
        changed = self.router.next()
        self._sync_focus(context)
        return changed

    def route_prev(self, context: WidgetContext) -> bool:
        if self.router is None:
            return False
        changed = self.router.previous()
        self._sync_focus(context)
        return changed

    def route_push(self, route: str | None, context: WidgetContext) -> bool:
        if self.router is None or not route:
            return False
        changed = self.router.push(route)
        self._sync_focus(context)
        return changed

    def route_pop(self, context: WidgetContext) -> bool:
        if self.router is None:
            return False
        changed = self.router.pop()
        self._sync_focus(context)
        return changed

    def store_set(self, path: str | None, value, context: WidgetContext) -> bool:
        if self.store is None or not path:
            return False
        self.store.set(path, value)
        self._sync_focus(context)
        return True

    def store_toggle(self, path: str | None, context: WidgetContext) -> bool:
        if self.store is None or not path:
            return False
        self.store.toggle(path)
        self._sync_focus(context)
        return True

    def _target_widget(self, context: WidgetContext) -> Widget:
        self._sync_focus(context)
        if not context.focused_widget:
            return self

        queue = list(self.children)
        while queue:
            widget = queue.pop(0)
            if widget.name == context.focused_widget:
                return widget
            queue.extend(widget.interaction_children())
        return self

    def dispatch_key_event(self, key: str, modifiers: list[str], context: WidgetContext) -> bool:
        self._sync_focus(context)
        current: Widget | None = self._target_widget(context)
        while current is not None:
            if current.dispatch_keybindings(key, modifiers, context):
                self._sync_focus(context)
                return True
            if current.handle_input(key, modifiers, context):
                self._sync_focus(context)
                return True
            current = current.parent
        return False
