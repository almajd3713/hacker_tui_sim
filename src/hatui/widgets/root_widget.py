from hatui.core.widget import Widget, WidgetContext
from hatui.core.style import Theme

class RootWidget(Widget):
    """
    The RootWidget is the top-level widget in the widget hierarchy.
    It serves as the entry point for rendering and managing the entire widget tree.
    It has a single child widget, which is the main content of the application.
    """
    def __init__(self, name: str, children: list = None, theme: Theme | None = None):
        super().__init__(name, children)
        self.context = WidgetContext(name=name, version="1.0.0", theme=theme or Theme())
    
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
