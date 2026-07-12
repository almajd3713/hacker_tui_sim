from hatui.core.widget import WidgetContext
from hatui.widgets.list_widget import ListWidget


class MenuWidget(ListWidget):
    """Selectable list that can dispatch item actions."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)

    def default_keybindings(self) -> list[dict]:
        bindings = super().default_keybindings()
        bindings.extend(
            [
                {"key": "enter", "action": "activate_selected"},
                {"key": "space", "action": "activate_selected"},
            ]
        )
        return bindings

    def handle_action(self, action: str, payload: dict, context: WidgetContext) -> bool:
        if action == "activate_selected":
            item = self.selected_item()
            if not isinstance(item, dict):
                return False
            action_name = item.get("action")
            if not action_name:
                return False
            action_payload = dict(item.get("payload", {}) or {})
            return self.perform_action(str(action_name), action_payload, context)
        return super().handle_action(action, payload, context)
