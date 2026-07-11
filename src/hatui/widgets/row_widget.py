from hatui.core.widget import Widget, WidgetContext


class RowWidget(Widget):
    """Lay out children horizontally with weighted width allocation."""

    def __init__(self, name: str, children: list | None = None):
        normalized_children = []
        for child in children or []:
            if isinstance(child, tuple):
                widget, weight = child
                widget.set_layout_weight(weight)
                normalized_children.append(widget)
            else:
                normalized_children.append(child)
        super().__init__(name, normalized_children)

    @property
    def _schema(self):
        return {}

    def _child_widths(self, width: int) -> list[int]:
        if not self.children:
            return []

        weights = [max(child.layout_weight, 0.0) for child in self.children]
        total_weight = sum(weights) or float(len(self.children))
        raw_widths = [width * ((weight or 1.0) / total_weight) for weight in weights]
        widths = [int(raw_width) for raw_width in raw_widths]
        remainder = width - sum(widths)

        for index in range(remainder):
            widths[index % len(widths)] += 1
        return widths

    def allocate_children(self, width: int, height: int):
        for child, child_width in zip(self.children, self._child_widths(width)):
            child.allocate(child_width, height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        cursor_x = x
        for child in self.children:
            child.layout(cursor_x, y, context)
            cursor_x += child.properties["rect"].width

    def paint(self, buffer, context: WidgetContext):
        for child in self.children:
            child.paint(buffer, context)
