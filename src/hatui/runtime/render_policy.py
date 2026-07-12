from __future__ import annotations

from dataclasses import dataclass


UNICODE_TRANSLATION = str.maketrans(
    {
        "╭": "+",
        "╮": "+",
        "╰": "+",
        "╯": "+",
        "┌": "+",
        "┐": "+",
        "└": "+",
        "┘": "+",
        "│": "|",
        "─": "-",
        "═": "=",
        "█": "#",
        "▇": "#",
        "▆": "#",
        "▅": "#",
        "▄": "#",
        "▃": "*",
        "▂": "*",
        "▁": ".",
        "░": ".",
        "▒": ":",
        "▓": "#",
        "»": ">",
        "▸": ">",
        "▾": "v",
        "•": "*",
        "●": "*",
        "╲": "\\",
        "╱": "/",
    }
)


UNICODE_CHARS = {
    "horizontal": "─",
    "vertical": "│",
    "point": "●",
    "bullet": "•",
    "collapsed": "▸",
    "expanded": "▾",
    "diag_down": "╲",
    "diag_up": "╱",
    "fill": "█",
    "scroll_track": "│",
    "scroll_thumb": "█",
    "empty_block": "░",
}

ASCII_CHARS = {
    "horizontal": "-",
    "vertical": "|",
    "point": "*",
    "bullet": "*",
    "collapsed": ">",
    "expanded": "v",
    "diag_down": "\\",
    "diag_up": "/",
    "fill": "#",
    "scroll_track": "|",
    "scroll_thumb": "#",
    "empty_block": ".",
}

UNICODE_LEVELS = {
    "spark": "▁▂▃▄▅▆▇█",
    "block": " ▁▂▃▄▅▆▇█",
    "shade": " ░▒▓█",
}

ASCII_LEVELS = {
    "spark": ".:-=+*#",
    "block": " .:-=+*#",
    "shade": " .:*#",
}

UNICODE_BORDERS = {
    "ascii": {
        "top_left": "+",
        "top_right": "+",
        "bottom_left": "+",
        "bottom_right": "+",
        "horizontal": "-",
        "vertical": "|",
    },
    "sharp": {
        "top_left": "┌",
        "top_right": "┐",
        "bottom_left": "└",
        "bottom_right": "┘",
        "horizontal": "─",
        "vertical": "│",
    },
    "rounded": {
        "top_left": "╭",
        "top_right": "╮",
        "bottom_left": "╰",
        "bottom_right": "╯",
        "horizontal": "─",
        "vertical": "│",
    },
}

ASCII_BORDER = {
    "top_left": "+",
    "top_right": "+",
    "bottom_left": "+",
    "bottom_right": "+",
    "horizontal": "-",
    "vertical": "|",
}


@dataclass(frozen=True)
class RenderPolicy:
    glyph_mode: str = "unicode"

    @property
    def is_ascii(self) -> bool:
        return self.glyph_mode == "ascii"

    def char(self, name: str, default: str = " ") -> str:
        source = ASCII_CHARS if self.is_ascii else UNICODE_CHARS
        return source.get(name, default)

    def levels(self, name: str, default: str = "") -> str:
        source = ASCII_LEVELS if self.is_ascii else UNICODE_LEVELS
        return source.get(name, default)

    def border(self, style: str) -> dict[str, str]:
        if self.is_ascii:
            return dict(ASCII_BORDER)
        return dict(UNICODE_BORDERS.get(style, UNICODE_BORDERS["sharp"]))

    def translate(self, text: str) -> str:
        if self.is_ascii:
            return text.translate(UNICODE_TRANSLATION)
        return text
