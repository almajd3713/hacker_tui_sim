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


DEFAULT_STYLE = Style()

class ScreenBuffer:
    """
    A class to represent the 2D screen buffer
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer = [[Cell() for _ in range(width)] for _ in range(height)]
        self._clip_stack: list[tuple[int, int, int, int]] = []
        self._style_cache: dict[tuple[str, str], Style] = {("default", "default"): DEFAULT_STYLE}

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
                cell = self.buffer[y][x]
                cell.char = " "
                cell.style = DEFAULT_STYLE

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
    
    def _resolve_style(self, fg_color: str, bg_color: str) -> Style:
        key = (fg_color, bg_color)
        cached = self._style_cache.get(key)
        if cached is None:
            cached = Style(fg_color=fg_color, bg_color=bg_color)
            self._style_cache[key] = cached
        return cached

    def write(self, x: int, y: int, char: str, fg_color: str = 'default', bg_color: str = 'default', *, style: Style | None = None):
        """
        Write a character to the screen buffer at the specified coordinates.
        """
        if 0 <= x < self.width and 0 <= y < self.height and self._within_clip(x, y):
            cell = self.buffer[y][x]
            cell.char = char
            cell.style = style or self._resolve_style(fg_color, bg_color)

    def write_text(self, x: int, y: int, text: str, fg_color: str = 'default', bg_color: str = 'default', *, style: Style | None = None):
        """
        Write a string of text to the screen buffer starting at the specified coordinates.
        """
        resolved_style = style or self._resolve_style(fg_color, bg_color)
        for i, char in enumerate(text):
            self.write(x + i, y, char, fg_color, bg_color, style=resolved_style)

    def write_text_clipped(self, x: int, y: int, text: str, width: int, fg_color: str = "default", bg_color: str = "default", *, style: Style | None = None):
        self.write_text(x, y, str(text)[: max(width, 0)], fg_color, bg_color, style=style)

    def fill_rect(self, x: int, y: int, width: int, height: int, char: str = " ", fg_color: str = "default", bg_color: str = "default", *, style: Style | None = None):
        resolved_style = style or self._resolve_style(fg_color, bg_color)
        fill = char[:1] if char else " "
        line = fill * max(width, 0)
        for row in range(max(height, 0)):
            self.write_text(x, y + row, line, fg_color, bg_color, style=resolved_style)

    def fill_row(self, x: int, y: int, width: int, fg_color: str = "default", bg_color: str = "default", *, style: Style | None = None):
        self.fill_rect(x, y, width, 1, " ", fg_color, bg_color, style=style)

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

    def to_plain_text(self) -> str:
        return "\n".join("".join(cell.char for cell in row).rstrip() for row in self.buffer)
