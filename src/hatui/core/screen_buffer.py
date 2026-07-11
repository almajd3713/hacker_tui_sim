import sys
from contextlib import contextmanager
from dataclasses import dataclass, field

from hatui.core.style import Style, ansi_sequence


@dataclass
class Cell:
    """
    A class to represent a single cell in the screen buffer, aka a single character.
    """
    char: str = ' '
    style: Style = field(default_factory=Style)

class ScreenBuffer:
    """
    A class to represent the 2D screen buffer
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer = [[Cell() for _ in range(width)] for _ in range(height)]
        self._clip_stack: list[tuple[int, int, int, int]] = []

    def resize(self, width: int, height: int):
        """
        Resize the screen buffer to match the current terminal dimensions.
        """
        self.width = width
        self.height = height
        self.buffer = [[Cell() for _ in range(width)] for _ in range(height)]
        self._clip_stack.clear()

    def clear(self):
        """
        Clear the screen buffer by resetting all cells to default values.
        """
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = Cell()

    def _normalized_clip(self, x: int, y: int, width: int, height: int) -> tuple[int, int, int, int]:
        left = max(x, 0)
        top = max(y, 0)
        right = min(x + max(width, 0), self.width)
        bottom = min(y + max(height, 0), self.height)
        if right < left:
            right = left
        if bottom < top:
            bottom = top
        return left, top, right, bottom

    def push_clip(self, x: int, y: int, width: int, height: int):
        clip = self._normalized_clip(x, y, width, height)
        if self._clip_stack:
            left, top, right, bottom = self._clip_stack[-1]
            clip = (
                max(clip[0], left),
                max(clip[1], top),
                min(clip[2], right),
                min(clip[3], bottom),
            )
        self._clip_stack.append(clip)

    def pop_clip(self):
        if self._clip_stack:
            self._clip_stack.pop()

    @contextmanager
    def clip(self, x: int, y: int, width: int, height: int):
        self.push_clip(x, y, width, height)
        try:
            yield
        finally:
            self.pop_clip()

    def _within_clip(self, x: int, y: int) -> bool:
        if not self._clip_stack:
            return True
        left, top, right, bottom = self._clip_stack[-1]
        return left <= x < right and top <= y < bottom
    
    def write(self, x: int, y: int, char: str, fg_color: str = 'default', bg_color: str = 'default'):
        """
        Write a character to the screen buffer at the specified coordinates.
        """
        if 0 <= x < self.width and 0 <= y < self.height and self._within_clip(x, y):
            self.buffer[y][x] = Cell(char, Style(fg_color=fg_color, bg_color=bg_color))

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
        segments = ["\033[H"]
        for row_index, row in enumerate(self.buffer):
            line = [f"\033[{row_index + 1};1H"]
            active_style = None
            for cell in row:
                style = ansi_sequence(cell.style)
                if style != active_style:
                    line.append(style)
                    active_style = style
                line.append(cell.char)
            line.append("\033[0m")
            segments.append("".join(line))

        frame = "".join(segments) + "\033[0m"
        sys.stdout.write(frame)
        sys.stdout.flush()
