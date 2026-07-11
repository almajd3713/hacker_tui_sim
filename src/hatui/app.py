import shutil

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.terminal_env import TerminalEnvironment
from hatui.widgets.root_widget import RootWidget
from hatui.widgets.text_widget import TextWidget


class HatuiApp:
    def __init__(self):
        self.root_widget = RootWidget("root", children=[
            TextWidget("text1", text="Hello, World!")
        ])

        width, height = self._get_terminal_size()
        self.screen_buffer = ScreenBuffer(width=width, height=height)
        self.environment = TerminalEnvironment()
        self.input_manager = InputManager()

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

def main():
    app = HatuiApp()
    app.run()

if __name__ == "__main__":
    main()
