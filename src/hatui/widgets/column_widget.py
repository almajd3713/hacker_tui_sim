from hatui.core.widget import Widget, WidgetContext


class ColumnWidget(Widget):
    """Lay out children vertically with weighted height allocation."""

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

    def _child_heights(self, height: int) -> list[int]:
        if not self.children:
            return []

        weights = [max(child.layout_weight, 0.0) for child in self.children]
        total_weight = sum(weights) or float(len(self.children))
        raw_heights = [height * ((weight or 1.0) / total_weight) for weight in weights]
        heights = [int(raw_height) for raw_height in raw_heights]
        remainder = height - sum(heights)

        for index in range(remainder):
            heights[index % len(heights)] += 1
        return heights

    def allocate_children(self, width: int, height: int):
        for child, child_height in zip(self.children, self._child_heights(height)):
            child.allocate(width, child_height)

    def layout_children(self, x: int, y: int, context: WidgetContext):
        cursor_y = y
        for child in self.children:
            child.layout(x, cursor_y, context)
            cursor_y += child.properties["rect"].height

    def paint(self, buffer, context: WidgetContext):
        for child in self.children:
            child.paint(buffer, context)
