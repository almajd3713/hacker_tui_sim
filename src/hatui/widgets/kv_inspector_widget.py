from __future__ import annotations

from hatui.core.style import Style, resolve_color_token, themed_style
from hatui.core.widget import Widget, WidgetContext
from hatui.runtime.bindings import resolve_path
from hatui.widgets.visualization import flatten_object, trim_text


class KVInspectorWidget(Widget):
    """Structured key/value inspector with optional grouped sections."""

    def __init__(
        self,
        name: str,
        data_key: str | None = None,
        fg_color: str | None = None,
        bg_color: str | None = None,
        key_color: str | None = None,
        value_color: str | None = None,
        title_color: str | None = None,
    ):
        super().__init__(name)
        self.data_key = data_key
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.key_color = key_color
        self.value_color = value_color
        self.title_color = title_color
        self.state["sections"] = []

    @property
    def _schema(self):
        return {
            "data_key": str,
            "fg_color": str,
            "bg_color": str,
            "key_color": str,
            "value_color": str,
            "title_color": str,
        }

    def update(self, delta_time: float, context: WidgetContext):
        payload = resolve_path(context.data, self.data_key, None) if self.data_key else None
        self.state["sections"] = self._normalize_sections(payload)
        super().update(delta_time, context)

    def _normalize_sections(self, payload) -> list[dict]:
        if payload is None:
            return []
        if isinstance(payload, dict) and isinstance(payload.get("sections"), list):
            sections = []
            for section in payload.get("sections", []):
                title = str(section.get("title", "section"))
                items = []
                for item in section.get("items", []):
                    if isinstance(item, dict):
                        label = str(item.get("label") or item.get("key") or "--")
                        value = str(item.get("value", ""))
                    else:
                        label = str(item)
                        value = ""
                    items.append((label, value))
                sections.append({"title": title, "items": items})
            return sections
        if isinstance(payload, dict):
            sections = []
            for key, value in payload.items():
                if isinstance(value, dict):
                    sections.append({"title": str(key), "items": flatten_object(value)})
                else:
                    sections.append({"title": str(key), "items": [("value", str(value))]})
            return sections
        return [{"title": "value", "items": [("value", str(payload))]}]

    def allocate(self, width: int, height: int):
        rect = self.properties["rect"]
        rect.width = max(width, 0)
        rect.height = max(height, 0)
        self.allocate_children(rect.width, rect.height)

    def allocate_children(self, width: int, height: int):
        pass

    def layout_children(self, x: int, y: int, context: WidgetContext):
        pass

    def paint(self, buffer, context: WidgetContext):
        rect = self.properties["rect"]
        if rect.width <= 0 or rect.height <= 0:
            return
        base_style = themed_style(
            context.theme,
            "kv_inspector",
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            fallback=Style(context.theme.text.fg_color, context.theme.text.bg_color),
        )
        key_color = resolve_color_token(
            self.key_color or context.theme.widget_slot("kv_inspector", "key_color", context.theme.color("text_muted")),
            context.theme,
            context.theme.color("text_muted"),
        )
        value_color = resolve_color_token(
            self.value_color or context.theme.widget_slot("kv_inspector", "value_color", base_style.fg_color),
            context.theme,
            base_style.fg_color,
        )
        title_color = resolve_color_token(
            self.title_color or context.theme.widget_slot("kv_inspector", "title_color", context.theme.color("accent")),
            context.theme,
            context.theme.color("accent"),
        )
        cursor_y = rect.y
        key_width = min(max(rect.width // 3, 10), max(rect.width - 1, 1))
        for section in self.state.get("sections", []):
            if cursor_y >= rect.y + rect.height:
                break
            title = trim_text(f"[{section['title']}]", rect.width)
            buffer.write_text(rect.x, cursor_y, title, title_color, base_style.bg_color)
            cursor_y += 1
            for key, value in section.get("items", []):
                if cursor_y >= rect.y + rect.height:
                    break
                buffer.write_text(rect.x, cursor_y, trim_text(str(key).ljust(key_width), key_width), key_color, base_style.bg_color)
                if key_width + 1 < rect.width:
                    buffer.write_text(
                        rect.x + key_width + 1,
                        cursor_y,
                        trim_text(value, rect.width - key_width - 1),
                        value_color,
                        base_style.bg_color,
                    )
                cursor_y += 1

