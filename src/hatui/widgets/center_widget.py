from hatui.core.widget import Widget, WidgetContext


class CenterWidget(Widget):
    """Position a single child in the center of the available rectangle."""

    @property
    def _schema(self):
        return {}

    def allocate_children(self, width: int, height: int):
        if self.children:
            self.children[0].allocate(width, height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        if not self.children:
            return

        child = self.children[0]
        child_rect = child.properties["rect"]
        parent_rect = self.properties["rect"]

        child_x = x + max((parent_rect.width - child_rect.width) // 2, 0)
        child_y = y + max((parent_rect.height - child_rect.height) // 2, 0)
        child.layout(child_x, child_y, context)

    def paint(self, buffer, context: WidgetContext):
        if self.children:
            self.children[0].paint(buffer, context)
