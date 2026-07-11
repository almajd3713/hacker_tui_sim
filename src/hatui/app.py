from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.terminal_env import TerminalEnvironment
from hatui.runtime.defaults import create_provider_registry, create_widget_registry
from hatui.runtime.loader import ScreenSpecLoader
from hatui.runtime.provider_manager import ProviderManager
from hatui.widgets.root_widget import RootWidget


class HatuiApp:
    def __init__(
        self,
        spec_path: str | Path,
        *,
        widget_registry=None,
        provider_registry=None,
    ):
        self.spec_path = Path(spec_path)
        self.widget_registry = widget_registry or create_widget_registry()
        self.provider_registry = provider_registry or create_provider_registry()
        self.loader = ScreenSpecLoader(self.widget_registry, self.provider_registry)

        spec = self.loader.load_spec(self.spec_path)
        theme = self.loader.load_theme(spec)
        screen = self.loader.load_screen(spec)
        providers = self.loader.load_providers(spec)

        self.root_widget = RootWidget("root", children=[screen], theme=theme)
        self.root_widget.focus_first(self.root_widget.context)
        self.provider_manager = ProviderManager(providers)

        width, height = self._get_terminal_size()
        self.screen_buffer = ScreenBuffer(width=width, height=height)
        self.environment = TerminalEnvironment()
        self.input_manager = InputManager()
        self._last_frame_time = time.monotonic()
        self._start_time = self._last_frame_time

    def _get_terminal_size(self) -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(100, 32))
        return max(size.columns, 1), max(size.lines, 1)

    def run(self):
        running = True
        with self.environment.manage():
            self.provider_manager.setup(self.root_widget.context)
            try:
                while running:
                    key_event = self.input_manager.poll_input(timeout=0.05)
                    if key_event is not None:
                        key, modifiers = key_event
                        self.root_widget.context.last_key = key
                        self.root_widget.context.last_modifiers = list(modifiers)
                        self.root_widget.dispatch_key_event(key, modifiers, self.root_widget.context)

                    width, height = self._get_terminal_size()
                    if (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
                        self.screen_buffer.resize(width, height)

                    self.update()
                    self.root_widget.allocate(self.screen_buffer.width, self.screen_buffer.height)
                    self.root_widget.layout(0, 0, self.root_widget.context)
                    self.screen_buffer.clear()
                    self.root_widget.paint(self.screen_buffer, self.root_widget.context)
                    self.screen_buffer.flush()
            except KeyboardInterrupt:
                running = False
            finally:
                self.provider_manager.teardown(self.root_widget.context)

    def update(self):
        now = time.monotonic()
        context = self.root_widget.context
        context.delta_time = now - self._last_frame_time
        context.elapsed_time = now - self._start_time
        context.frame += 1
        context.terminal_width = self.screen_buffer.width
        context.terminal_height = self.screen_buffer.height
        context.widget_width = self.screen_buffer.width
        context.widget_height = self.screen_buffer.height
        self.provider_manager.update(context.delta_time, context)
        self.root_widget.update(context.delta_time, context)
        self._last_frame_time = now


def main():
    default_spec = Path(__file__).resolve().parents[2] / "screens" / "dashboard.yaml"
    spec_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_spec
    app = HatuiApp(spec_path=spec_path)
    app.run()


if __name__ == "__main__":
    main()
