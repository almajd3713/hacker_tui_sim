from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Style:
    fg_color: str = "default"
    bg_color: str = "default"
    font_name: Optional[str] = None


@dataclass(frozen=True)
class BorderTheme:
    style: str = "sharp"
    fg_color: str = "bright_black"
    bg_color: str = "default"
    font_name: Optional[str] = None


@dataclass(frozen=True)
class TextTheme:
    fg_color: str = "default"
    bg_color: str = "default"
    font_name: Optional[str] = None


@dataclass(frozen=True)
class Theme:
    border: BorderTheme = BorderTheme()
    text: TextTheme = TextTheme()


FG_COLOR_CODES = {
    "default": "39",
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
}

BG_COLOR_CODES = {
    "default": "49",
    "black": "40",
    "red": "41",
    "green": "42",
    "yellow": "43",
    "blue": "44",
    "magenta": "45",
    "cyan": "46",
    "white": "47",
    "bright_black": "100",
    "bright_red": "101",
    "bright_green": "102",
    "bright_yellow": "103",
    "bright_blue": "104",
    "bright_magenta": "105",
    "bright_cyan": "106",
    "bright_white": "107",
}


def ansi_color_code(color: str, is_background: bool = False) -> str:
    color_map = BG_COLOR_CODES if is_background else FG_COLOR_CODES
    if color in color_map:
        return color_map[color]

    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
        prefix = "48" if is_background else "38"
        return f"{prefix};2;{red};{green};{blue}"

    return color_map["default"]


def ansi_sequence(style: Style) -> str:
    fg_code = ansi_color_code(style.fg_color, is_background=False)
    bg_code = ansi_color_code(style.bg_color, is_background=True)
    return f"\033[{fg_code};{bg_code}m"


def resolve_style(
    fg_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    font_name: Optional[str] = None,
    fallback: Optional[Style] = None,
) -> Style:
    fallback = fallback or Style()
    return Style(
        fg_color=fallback.fg_color if fg_color is None else fg_color,
        bg_color=fallback.bg_color if bg_color is None else bg_color,
        font_name=fallback.font_name if font_name is None else font_name,
    )
