from hatui.core.widget import Widget, WidgetContext


class RowWidget(Widget):
    """Lay out children horizontally with an even width split."""

    @property
    def _schema(self):
        return {}

    def allocate_children(self, width: int, height: int):
        child_count = len(self.children)
        if child_count == 0:
            return

        base_width = width // child_count
        remainder = width % child_count

        for index, child in enumerate(self.children):
            child_width = base_width + (1 if index < remainder else 0)
            child.allocate(child_width, height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        cursor_x = x
        for child in self.children:
            child.layout(cursor_x, y, context)
            cursor_x += child.properties["rect"].width

    def paint(self, buffer, context: WidgetContext):
        for child in self.children:
            child.paint(buffer, context)
