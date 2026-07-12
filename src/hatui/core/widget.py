from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, List

from hatui.core.actions import KeyBinding, normalize_chord, parse_keybinding
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.style import Theme

from .context import Context

@dataclass
class WidgetContext(Context):
    """
    A class to represent the context of a widget.
    """
    theme: Theme = field(default_factory=Theme)

    # Terminal properties
    widget_width: int = None
    widget_height:int = None

@dataclass
class WidgetRect:
    """
    A class to represent the rectangle of a widget.
    """
    x: int
    y: int
    width: int
    height: int

class Widget(ABC):
    """
    Base class for all widgets. It is responsible for:
    - Storing widget state and properties
    - Provide dynamic rendering capabilities, with responsive layout and styling
    - Handling user interactions and events
    
    3 Phases to render a widget:
    - allocate: Determine the size of its children and updates them
    - layout: Determine the position of its children and updates them
    - paint: Render the widget and its children to the screen buffer
    """
    @property
    @abstractmethod
    def _schema(self):
        """
        Returns the schema for the widget, which defines its properties and their types.
        """
        pass
    
    def __init__(self, name: str, children: List['Widget'] = None):
        self.name = name
        self.properties = dict(
            rect=WidgetRect(x=0, y=0, width=0, height=0)
        )
        self.state = {}
        self.layout_weight = 1
        self.parent: Widget | None = None
        self.children: List[Widget] = []
        self.focusable = False
        self.focus_fg_color: str | None = None
        self.focus_bg_color: str | None = None
        self.keybindings: list[KeyBinding] = []
        for child in children or []:
            self.add_child(child)

    def set_layout_weight(self, weight: int | float):
        self.layout_weight = max(float(weight), 0.0)
        return self

    def add_child(self, child: 'Widget'):
        child.parent = self
        self.children.append(child)
        return child

    def default_focusable(self) -> bool:
        return False

    def default_keybindings(self) -> list[dict[str, Any]]:
        return []

    def configure_interaction(self, spec: dict[str, Any] | None = None):
        spec = spec or {}
        bindings = [parse_keybinding(item) for item in self.default_keybindings()]
        bindings.extend(parse_keybinding(item) for item in spec.get("keybindings", []))
        self.keybindings = bindings

        focusable = spec.get("focusable")
        selectable = spec.get("selectable")
        if focusable is not None:
            self.focusable = bool(focusable)
        elif selectable is not None:
            self.focusable = bool(selectable)
        else:
            self.focusable = self.default_focusable() or bool(self.keybindings)

        self.focus_fg_color = spec.get("focus_fg_color")
        self.focus_bg_color = spec.get("focus_bg_color")
        return self

    @property
    def root(self) -> 'Widget':
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def interaction_children(self) -> list['Widget']:
        return self.children

    def focusable_widgets(self) -> list['Widget']:
        widgets = [self] if self.focusable else []
        for child in self.interaction_children():
            widgets.extend(child.focusable_widgets())
        return widgets

    def is_focused(self, context: Context) -> bool:
        return context.focused_widget == self.name

    def _binding_matches(self, binding: KeyBinding, key: str, modifiers: list[str]) -> bool:
        return binding.chord == normalize_chord(key, modifiers)

    def dispatch_keybindings(self, key: str, modifiers: list[str], context: Context) -> bool:
        for binding in self.keybindings:
            if self._binding_matches(binding, key, modifiers):
                if not binding.action:
                    return True
                payload = deepcopy(binding.payload)
                return self.perform_action(binding.action, payload, context)
        return False

    def perform_action(self, action: str, payload: dict[str, Any], context: Context) -> bool:
        root = self.root
        if action == "focus_next" and hasattr(root, "focus_next"):
            return bool(root.focus_next(context))
        if action == "focus_prev" and hasattr(root, "focus_prev"):
            return bool(root.focus_prev(context))
        if action == "focus_first" and hasattr(root, "focus_first"):
            return bool(root.focus_first(context))
        if action == "focus_last" and hasattr(root, "focus_last"):
            return bool(root.focus_last(context))
        if action == "focus_widget" and hasattr(root, "focus_widget"):
            return bool(root.focus_widget(payload.get("target"), context))
        if action == "route_set" and hasattr(root, "route_set"):
            return bool(root.route_set(payload.get("route"), context))
        if action == "route_next" and hasattr(root, "route_next"):
            return bool(root.route_next(context))
        if action == "route_prev" and hasattr(root, "route_prev"):
            return bool(root.route_prev(context))
        if action == "route_push" and hasattr(root, "route_push"):
            return bool(root.route_push(payload.get("route"), context))
        if action == "route_pop" and hasattr(root, "route_pop"):
            return bool(root.route_pop(context))
        if action == "route_pop_focus_widget" and hasattr(root, "route_pop_focus_widget"):
            return bool(root.route_pop_focus_widget(payload.get("target"), context))
        if action == "store_set" and hasattr(root, "store_set"):
            return bool(root.store_set(payload.get("path"), payload.get("value"), context))
        if action == "store_toggle" and hasattr(root, "store_toggle"):
            return bool(root.store_toggle(payload.get("path"), context))
        return self.handle_action(action, payload, context)

    def handle_action(self, action: str, payload: dict[str, Any], context: Context) -> bool:
        return False
    
    def allocate(self, width: int, height: int):
        """
        ? Parent Call
        Allocate the size of the widget based on the given constraints.
        """
        self.properties["rect"].width = width
        self.properties["rect"].height = height

        self.allocate_children(width, height)

    def update(self, delta_time: float, context: Context):
        """
        ? Parent call.
        Update the widget state for the current frame.
        """
        self.update_children(delta_time, context)

    def update_children(self, delta_time: float, context: Context):
        for child in self.children:
            child.update(delta_time, context)

    def measure_content(self, width: int, height: int) -> tuple[int, int]:
        return max(width, 0), max(height, 0)

    def handle_input(self, key: str, modifiers: list[str], context: Context) -> bool:
        return False
    
    @abstractmethod
    def allocate_children(self, width: int, height: int):
        """
        ? Parent Call
        Allocate the size of the widget's children based on the given constraints.
        """
        pass
    
    def layout(self, x: int, y: int, context: Context):
        """
        ? Parent Call
        Layout the widget at the given position (x, y).
        """
        self.properties["rect"].x = x
        self.properties["rect"].y = y
        
        self.layout_children(x, y, context)
        
    @abstractmethod
    def layout_children(self, x: int, y: int, context: Context):
        """
        ? Parent Call
        Layout the widget's children at the given position (x, y).
        """
        pass

    @abstractmethod
    def paint(self, buffer: ScreenBuffer, context: Context):
        """
        ? Parent Call
        Paint the widget to the given screen buffer.
        """
        # Implement painting logic here
        pass
