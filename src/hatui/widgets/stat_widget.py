from hatui.core.style import Style, resolve_style
from hatui.core.widget import Widget, WidgetContext


class StatWidget(Widget):
    """Compact readout for a label, primary value, and optional secondary line."""

    def __init__(
        self,
        name: str,
        label: str,
        data_key: str | None = None,
        suffix: str = "",
        fg_color: str | None = None,
        bg_color: str | None = None,
        accent_color: str | None = None,
    ):
        super().__init__(name)
        self.label = label
        self.data_key = data_key
        self.suffix = suffix
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.state["value"] = "0"
        self.state["secondary"] = ""

    @property
    def _schema(self):
        return {
            "label": str,
            "data_key": str,
            "suffix": str,
            "fg_color": str,
            "bg_color": str,
            "accent_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        payload = context.data.get(self.data_key, None) if self.data_key is not None else None
        if isinstance(payload, dict):
            value = payload.get("value", "0")
            secondary = payload.get("secondary", "")
        elif payload is None:
            value = "0"
            secondary = ""
        else:
            value = payload
            secondary = ""

        self.state["value"] = f"{value}{self.suffix}"
        self.state["secondary"] = str(secondary)
        super().update(delta_time, context)

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = min(max(height, 0), 3)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return

        base_style = resolve_style(
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(
                fg_color=context.theme.text.fg_color,
                bg_color=context.theme.text.bg_color,
            ),
        )
        accent_style = resolve_style(
            fg_color=self.accent_color or base_style.fg_color,
            bg_color=base_style.bg_color,
            fallback=base_style,
        )

        buffer.write_text(rect.x, rect.y, self.label[: rect.width], base_style.fg_color, base_style.bg_color)
        if rect.height > 1:
            buffer.write_text(
                rect.x,
                rect.y + 1,
                str(self.state["value"])[: rect.width],
                accent_style.fg_color,
                accent_style.bg_color,
            )
        if rect.height > 2 and self.state["secondary"]:
            buffer.write_text(
                rect.x,
                rect.y + 2,
                str(self.state["secondary"])[: rect.width],
                base_style.fg_color,
                base_style.bg_color,
            )
