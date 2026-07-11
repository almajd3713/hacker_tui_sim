from hatui.core.widget import Widget, WidgetContext


class ColumnWidget(Widget):
    """Lay out children vertically with an even height split."""

    @property
    def _schema(self):
        return {}

    def allocate_children(self, width: int, height: int):
        child_count = len(self.children)
        if child_count == 0:
            return

        base_height = height // child_count
        remainder = height % child_count

        for index, child in enumerate(self.children):
            child_height = base_height + (1 if index < remainder else 0)
            child.allocate(width, child_height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        cursor_y = y
        for child in self.children:
            child.layout(x, cursor_y, context)
            cursor_y += child.properties["rect"].height

    def paint(self, buffer, context: WidgetContext):
        for child in self.children:
            child.paint(buffer, context)
