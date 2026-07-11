from hatui.core.widget import Widget, WidgetContext

class TextWidget(Widget):
    """
    A simple text widget that displays a string of text.
    """
    def __init__(self, name: str, text: str):
        super().__init__(name)
        self.text = text

    @property
    def _schema(self):
        return {
            "text": str
        }

    def allocate_children(self, width: int, height: int):
        # Text widget does not have children, so no allocation needed
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        # Text widget does not have children, so no layout needed
        pass

    def paint(self, buffer, context: WidgetContext):
        # Render the text to the buffer at the specified position
        buffer.write_text(self.properties["rect"].x, self.properties["rect"].y, self.text)
