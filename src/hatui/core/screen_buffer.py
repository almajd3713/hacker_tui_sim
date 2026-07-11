import sys
from dataclasses import dataclass

from hatui.core.style import Style, ansi_sequence


@dataclass
class Cell:
    """
    A class to represent a single cell in the screen buffer, aka a single character.
    """
    char: str = ' '
    style: Style = Style()

class ScreenBuffer:
    """
    A class to represent the 2D screen buffer
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer = [[Cell() for _ in range(width)] for _ in range(height)]

    def resize(self, width: int, height: int):
        """
        Resize the screen buffer to match the current terminal dimensions.
        """
        self.width = width
        self.height = height
        self.buffer = [[Cell() for _ in range(width)] for _ in range(height)]

    def clear(self):
        """
        Clear the screen buffer by resetting all cells to default values.
        """
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = Cell()
    
    def write(self, x: int, y: int, char: str, fg_color: str = 'default', bg_color: str = 'default'):
        """
        Write a character to the screen buffer at the specified coordinates.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = Cell(char, Style(fg_color=fg_color, bg_color=bg_color))
        else:
            raise ValueError(f"Coordinates ({x}, {y}) are out of bounds for buffer size ({self.width}, {self.height}).")

    def write_text(self, x: int, y: int, text: str, fg_color: str = 'default', bg_color: str = 'default'):
        """
        Write a string of text to the screen buffer starting at the specified coordinates.
        """
        for i, char in enumerate(text):
            self.write(x + i, y, char, fg_color, bg_color)

    def flush(self):
        """
        Flush the screen buffer to the terminal.
        """
        lines = []
        for row in self.buffer:
            line = []
            active_style = None
            for cell in row:
                style = ansi_sequence(cell.style)
                if style != active_style:
                    line.append(style)
                    active_style = style
                line.append(cell.char)
            line.append("\033[0m")
            lines.append("".join(line))

        frame = "\033[H" + "\n".join(lines) + "\033[0m"
        sys.stdout.write(frame)
        sys.stdout.flush()
