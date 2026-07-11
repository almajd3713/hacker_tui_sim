import shutil
import time

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.style import BorderTheme, TextTheme, Theme
from hatui.core.terminal_env import TerminalEnvironment
from hatui.widgets import BoxWidget, LabelWidget, RootWidget


class HatuiApp:
    def __init__(self):
        self.root_widget = RootWidget(
            "root",
            theme=Theme(
                border=BorderTheme(style="rounded", fg_color="bright_black"),
                text=TextTheme(fg_color="#d7d7e0"),
            ),
            children=[
                BoxWidget(
                    "box",
                    title="hatui",
                    padding=1,
                    child=LabelWidget(
                        "text1",
                        text="Use sample_app.py for the full dashboard demo.",
                    ),
                )
            ],
        )

        width, height = self._get_terminal_size()
        self.screen_buffer = ScreenBuffer(width=width, height=height)
        self.environment = TerminalEnvironment()
        self.input_manager = InputManager()
        self._last_frame_time = time.monotonic()
        self._start_time = self._last_frame_time

    def _get_terminal_size(self) -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(80, 24))
        return max(size.columns, 1), max(size.lines, 1)

    def run(self):
        # Begin the application loop
        running = True
        with self.environment.manage():
            try:
                while running:
                    # Poll for input
                    self.input_manager.poll_input(timeout=0.05)

                    width, height = self._get_terminal_size()
                    if (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
                        self.screen_buffer.resize(width, height)

                    self.update()

                    # Allocate and layout the root widget
                    self.root_widget.allocate(self.screen_buffer.width, self.screen_buffer.height)
                    self.root_widget.layout(0, 0, self.root_widget.context)

                    # Reset the previous frame before repainting.
                    self.screen_buffer.clear()

                    # Paint the root widget to the screen buffer
                    self.root_widget.paint(self.screen_buffer, self.root_widget.context)

                    # Flush the screen buffer to the terminal
                    self.screen_buffer.flush()
            except KeyboardInterrupt:
                running = False
                
    def update(self):
        now = time.monotonic()
        self.root_widget.context.delta_time = now - self._last_frame_time
        self.root_widget.context.elapsed_time = now - self._start_time
        self.root_widget.context.frame += 1
        self.root_widget.context.terminal_width = self.screen_buffer.width
        self.root_widget.context.terminal_height = self.screen_buffer.height
        self.root_widget.context.widget_width = self.screen_buffer.width
        self.root_widget.context.widget_height = self.screen_buffer.height
        self.root_widget.update(self.root_widget.context.delta_time, self.root_widget.context)
        self._last_frame_time = now

def main():
    app = HatuiApp()
    app.run()

if __name__ == "__main__":
    main()
