from hatui.core.widget import Widget, WidgetContext
from hatui.core.style import Theme
from hatui.runtime.action_registry import create_default_action_registry
from hatui.runtime.render_policy import RenderPolicy
from hatui.widgets.root_services import DebugSnapshotBuilder, RootInteractionController

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
        render_policy: RenderPolicy | None = None,
    ):
        super().__init__(name, children)
        self.context = WidgetContext(
            name=name,
            version="1.0.0",
            theme=theme or Theme(),
            render_policy=render_policy or RenderPolicy(),
        )
        self.store = store
        self.router = router
        self.action_registry = create_default_action_registry()
        self.interaction = RootInteractionController(self)
        self.debug_snapshots = DebugSnapshotBuilder(self)
        self.state["last_focused_by_route"] = {}
        self.state["_refreshing_interaction"] = False
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

    def dispatch_action(self, action: str, payload: dict, source: Widget, context: WidgetContext) -> bool:
        return self.action_registry.dispatch(action, source, payload, context)

    def sync_focus(self, context: WidgetContext):
        self.interaction.sync_focus(context)

    def sync_runtime_state(self, context: WidgetContext):
        self.interaction.sync_runtime_state(context)

    def publish_debug_snapshot(self, context: WidgetContext):
        self.debug_snapshots.publish(context)

    def focus_first(self, context: WidgetContext) -> bool:
        return self.interaction.focus_first(context)

    def focus_last(self, context: WidgetContext) -> bool:
        return self.interaction.focus_last(context)

    def focus_next(self, context: WidgetContext) -> bool:
        return self.interaction.focus_next(context)

    def focus_prev(self, context: WidgetContext) -> bool:
        return self.interaction.focus_prev(context)

    def focus_widget(self, target: str | None, context: WidgetContext) -> bool:
        return self.interaction.focus_widget(target, context)

    def route_set(self, route: str | None, context: WidgetContext) -> bool:
        return self.interaction.route_set(route, context)

    def route_next(self, context: WidgetContext) -> bool:
        return self.interaction.route_next(context)

    def route_prev(self, context: WidgetContext) -> bool:
        return self.interaction.route_prev(context)

    def route_push(self, route: str | None, context: WidgetContext) -> bool:
        return self.interaction.route_push(route, context)

    def route_pop(self, context: WidgetContext) -> bool:
        return self.interaction.route_pop(context)

    def route_pop_focus_widget(self, target: str | None, context: WidgetContext) -> bool:
        return self.interaction.route_pop_focus_widget(target, context)

    def store_set(self, path: str | None, value, context: WidgetContext) -> bool:
        return self.interaction.store_set(path, value, context)

    def store_toggle(self, path: str | None, context: WidgetContext) -> bool:
        return self.interaction.store_toggle(path, context)

    def dispatch_key_event(self, key: str, modifiers: list[str], context: WidgetContext) -> bool:
        self.interaction.sync_focus(context)
        current: Widget | None = self.interaction.target_widget(context)
        while current is not None:
            if current.dispatch_keybindings(key, modifiers, context):
                self.interaction.sync_focus(context)
                return True
            if current.handle_input(key, modifiers, context):
                self.interaction.sync_focus(context)
                return True
            current = current.parent
        return False
