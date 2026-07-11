from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List

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
        self.children: List[Widget] = children if children is not None else []
    
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
