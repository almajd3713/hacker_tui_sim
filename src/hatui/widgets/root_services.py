from __future__ import annotations

from dataclasses import dataclass

from hatui.runtime.bindings import set_path


@dataclass(slots=True)
class RootInteractionController:
    root: object

    def focusable_widgets(self) -> list:
        widgets = []
        for child in self.root.children:
            widgets.extend(child.focusable_widgets())
        return widgets

    def current_route(self) -> str | None:
        router = getattr(self.root, "router", None)
        if router is None:
            return None
        return router.current

    def sync_runtime_state(self, context) -> None:
        if self.root.store is not None:
            self.root.store.sync_to_context(context)
        if self.root.router is not None:
            self.root.router.sync_to_context(context)

    def refresh_interaction_state(self, context) -> None:
        self.sync_runtime_state(context)
        self.root.state["_refreshing_interaction"] = True
        try:
            self.root.update_children(0.0, context)
        finally:
            self.root.state["_refreshing_interaction"] = False

    def remember_focus(self, route: str | None, focused_widget: str | None) -> None:
        if not route or not focused_widget:
            return
        self.root.state.setdefault("last_focused_by_route", {})
        self.root.state["last_focused_by_route"][route] = focused_widget

    def restore_focus(self, route: str | None, names: list[str], context) -> bool:
        if not route:
            return False
        target = self.root.state.get("last_focused_by_route", {}).get(route)
        if target in names:
            context.focused_widget = target
            return True
        return False

    def sync_focus(self, context) -> None:
        self.refresh_interaction_state(context)
        focusables = self.focusable_widgets()
        focusable_names = [widget.name for widget in focusables]
        focused = context.focused_widget
        route = self.current_route()
        if focusables and focused not in set(focusable_names):
            if not self.restore_focus(route, focusable_names, context):
                context.focused_widget = focusables[0].name
        if not focusables:
            context.focused_widget = None
        if context.focused_widget in focusable_names:
            self.remember_focus(route, context.focused_widget)
        context.data.setdefault("_ui", {})
        set_path(context.data, "_ui.focused_widget", context.focused_widget)
        set_path(
            context.data,
            "_ui.last_focused_by_route",
            dict(self.root.state.get("last_focused_by_route", {})),
        )
        self.sync_runtime_state(context)

    def focus_first(self, context) -> bool:
        focusables = self.focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        context.focused_widget = focusables[0].name
        self.sync_focus(context)
        return True

    def focus_last(self, context) -> bool:
        focusables = self.focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        context.focused_widget = focusables[-1].name
        self.sync_focus(context)
        return True

    def focus_next(self, context) -> bool:
        focusables = self.focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        names = [widget.name for widget in focusables]
        if context.focused_widget not in names:
            context.focused_widget = names[0]
        else:
            index = names.index(context.focused_widget)
            context.focused_widget = names[(index + 1) % len(names)]
        self.sync_focus(context)
        return True

    def focus_prev(self, context) -> bool:
        focusables = self.focusable_widgets()
        if not focusables:
            context.focused_widget = None
            return False
        names = [widget.name for widget in focusables]
        if context.focused_widget not in names:
            context.focused_widget = names[-1]
        else:
            index = names.index(context.focused_widget)
            context.focused_widget = names[(index - 1) % len(names)]
        self.sync_focus(context)
        return True

    def focus_widget(self, target: str | None, context) -> bool:
        if not target:
            return False
        for widget in self.focusable_widgets():
            if widget.name == target:
                context.focused_widget = target
                self.sync_focus(context)
                return True
        return False

    def route_set(self, route: str | None, context) -> bool:
        if self.root.router is None or not route:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.set_current(route)
        self.sync_focus(context)
        return changed

    def route_next(self, context) -> bool:
        if self.root.router is None:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.next()
        self.sync_focus(context)
        return changed

    def route_prev(self, context) -> bool:
        if self.root.router is None:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.previous()
        self.sync_focus(context)
        return changed

    def route_push(self, route: str | None, context) -> bool:
        if self.root.router is None or not route:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.push(route)
        self.sync_focus(context)
        return changed

    def route_pop(self, context) -> bool:
        if self.root.router is None:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.pop()
        self.sync_focus(context)
        return changed

    def route_pop_focus_widget(self, target: str | None, context) -> bool:
        if self.root.router is None:
            return False
        self.remember_focus(self.current_route(), context.focused_widget)
        changed = self.root.router.pop()
        if not changed:
            return False
        self.sync_focus(context)
        return self.focus_widget(target, context)

    def store_set(self, path: str | None, value, context) -> bool:
        if self.root.store is None or not path:
            return False
        self.root.store.set(path, value)
        if self.root.state.get("_refreshing_interaction"):
            self.sync_runtime_state(context)
            return True
        self.sync_focus(context)
        return True

    def store_toggle(self, path: str | None, context) -> bool:
        if self.root.store is None or not path:
            return False
        self.root.store.toggle(path)
        if self.root.state.get("_refreshing_interaction"):
            self.sync_runtime_state(context)
            return True
        self.sync_focus(context)
        return True

    def target_widget(self, context):
        self.sync_focus(context)
        if not context.focused_widget:
            return self.root

        queue = list(self.root.children)
        while queue:
            widget = queue.pop(0)
            if widget.name == context.focused_widget:
                return widget
            queue.extend(widget.interaction_children())
        return self.root


@dataclass(slots=True)
class DebugSnapshotBuilder:
    root: object

    def publish(self, context) -> None:
        focusables = self.root.interaction.focusable_widgets()
        snapshot = {
            "route": self.root.interaction.current_route(),
            "focused_widget": context.focused_widget,
            "last_key": context.last_key,
            "last_modifiers": list(context.last_modifiers),
            "focusables": [widget.name for widget in focusables],
            "widget_tree": [self.widget_snapshot(child, context) for child in self.root.children],
            "widget_tree_lines": self.widget_tree_lines(self.root.children, context),
        }
        set_path(context.data, "_debug", snapshot)

    def widget_snapshot(self, widget, context) -> dict:
        rect = widget.properties["rect"]
        focusable = bool(widget.focusable)
        focused = widget.name == context.focused_widget
        label = (
            f"{'*' if focused else ' '} {'+' if focusable else '-'} "
            f"{widget.name}<{widget.__class__.__name__}> [{rect.x},{rect.y} {rect.width}x{rect.height}]"
        )
        return {
            "name": widget.name,
            "widget_name": widget.name,
            "type": widget.__class__.__name__,
            "label": label,
            "focused": focused,
            "focusable": focusable,
            "rect": {
                "x": rect.x,
                "y": rect.y,
                "width": rect.width,
                "height": rect.height,
            },
            "children": [self.widget_snapshot(child, context) for child in widget.children],
        }

    def widget_tree_lines(self, widgets: list, context, depth: int = 0) -> list[str]:
        lines: list[str] = []
        for widget in widgets:
            rect = widget.properties["rect"]
            marker = "*" if widget.name == context.focused_widget else " "
            focusable = " +" if widget.focusable else " -"
            lines.append(
                f"{'  ' * depth}{marker}{focusable} {widget.name}<{widget.__class__.__name__}>"
                f" [{rect.x},{rect.y} {rect.width}x{rect.height}]"
            )
            lines.extend(self.widget_tree_lines(widget.children, context, depth + 1))
        return lines
