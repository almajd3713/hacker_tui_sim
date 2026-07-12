from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


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


DEFAULT_COLORS = {
    "text": "default",
    "text_muted": "bright_black",
    "surface": "default",
    "surface_alt": "bright_black",
    "border": "bright_black",
    "accent": "bright_cyan",
    "accent_alt": "bright_magenta",
    "focus_fg": "bright_white",
    "focus_bg": "bright_black",
    "selection_fg": "bright_white",
    "selection_bg": "bright_black",
    "info": "cyan",
    "warn": "yellow",
    "error": "bright_red",
    "success": "green",
}

DEFAULT_FONTS = {
    "text": None,
    "border": None,
    "heading": None,
    "mono": None,
}

DEFAULT_SPACING = {
    "xs": 0,
    "sm": 1,
    "md": 2,
    "lg": 3,
}

THEME_PRESETS: dict[str, dict[str, Any]] = {
    "clean_ops": {
        "border": {"style": "sharp", "fg_color": "@border", "bg_color": "@surface", "font_name": "@font:border"},
        "text": {"fg_color": "@text", "bg_color": "@surface", "font_name": "@font:text"},
        "colors": {
            "text": "#d7d7e0",
            "text_muted": "#5a5a78",
            "surface": "default",
            "surface_alt": "#1d2533",
            "border": "#5a5a78",
            "accent": "#59d0ff",
            "accent_alt": "#cbb7ff",
            "focus_fg": "#59d0ff",
            "focus_bg": "#1d2533",
            "selection_fg": "#10131a",
            "selection_bg": "#59d0ff",
            "info": "#59d0ff",
            "warn": "#ffd166",
            "error": "#ff4d6d",
            "success": "#4de0a8",
        },
        "widgets": {
            "tabs": {"fg_color": "@text_muted", "bg_color": "@surface", "active_fg_color": "@focus_fg", "active_bg_color": "@surface_alt"},
            "status_strip": {"fg_color": "@text", "bg_color": "@surface_alt"},
            "stat": {"accent_color": "@accent"},
            "metric_grid": {"accent_color": "@accent"},
            "progress_bar": {"fill_color": "@accent"},
            "alert": {"info_fg_color": "@info", "warn_fg_color": "@warn", "error_fg_color": "@error", "success_fg_color": "@success"},
            "table": {"header_color": "@text", "selected_fg_color": "@selection_fg", "selected_bg_color": "@selection_bg"},
            "list": {"selected_fg_color": "@selection_fg", "selected_bg_color": "@selection_bg"},
            "menu": {"selected_fg_color": "@selection_fg", "selected_bg_color": "@selection_bg"},
            "scroll": {"scrollbar_fg_color": "@border", "scrollbar_bg_color": "@surface_alt"},
            "log": {"warn_fg_color": "@warn", "error_fg_color": "@error", "success_fg_color": "@success"},
            "code_block": {"line_number_color": "@text_muted"},
            "hex_dump": {"offset_color": "@text_muted"},
            "divider": {"fg_color": "@border", "bg_color": "@surface"},
            "modal": {"backdrop_bg_color": "#11131a"},
        },
    },
    "crt": {
        "border": {"style": "rounded", "fg_color": "@border", "bg_color": "@surface"},
        "text": {"fg_color": "@text", "bg_color": "@surface"},
        "colors": {
            "text": "#9fffb4",
            "text_muted": "#4f8f63",
            "surface": "#041508",
            "surface_alt": "#0d2212",
            "border": "#4f8f63",
            "accent": "#7bff7b",
            "accent_alt": "#d7ff87",
            "focus_fg": "#041508",
            "focus_bg": "#7bff7b",
            "selection_fg": "#041508",
            "selection_bg": "#9fffb4",
            "info": "#7bff7b",
            "warn": "#d7ff87",
            "error": "#ff7b7b",
            "success": "#9fffb4",
        },
    },
}


@dataclass(frozen=True)
class Theme:
    border: BorderTheme = field(default_factory=BorderTheme)
    text: TextTheme = field(default_factory=TextTheme)
    colors: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLORS))
    fonts: dict[str, Optional[str]] = field(default_factory=lambda: dict(DEFAULT_FONTS))
    spacing: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_SPACING))
    widgets: dict[str, dict[str, Any]] = field(default_factory=dict)
    preset: str | None = None

    def color(self, key: str, default: str = "default") -> str:
        return resolve_color_token(f"@{key}", self, default)

    def font(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return resolve_font_token(f"@font:{key}", self, default)

    def widget_slot(self, widget: str, slot: str, default: Any = None) -> Any:
        value = self.widgets.get(widget, {}).get(slot, default)
        if isinstance(value, str):
            if value.startswith("@font:"):
                return resolve_font_token(value, self, default)
            return resolve_color_token(value, self, default)
        return value


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


def merge_theme_spec(theme_spec: dict[str, Any]) -> dict[str, Any]:
    preset_name = theme_spec.get("preset", "clean_ops")
    preset = THEME_PRESETS.get(preset_name, {})
    merged = {
        "preset": preset_name if preset else theme_spec.get("preset"),
        "border": dict(preset.get("border", {})),
        "text": dict(preset.get("text", {})),
        "colors": {**DEFAULT_COLORS, **preset.get("colors", {}), **theme_spec.get("colors", {})},
        "fonts": {**DEFAULT_FONTS, **preset.get("fonts", {}), **theme_spec.get("fonts", {})},
        "spacing": {**DEFAULT_SPACING, **preset.get("spacing", {}), **theme_spec.get("spacing", {})},
        "widgets": _merge_nested_dict(preset.get("widgets", {}), theme_spec.get("widgets", {})),
    }
    merged["border"].update(theme_spec.get("border", {}))
    merged["text"].update(theme_spec.get("text", {}))
    return merged


def build_theme(theme_spec: dict[str, Any]) -> Theme:
    merged = merge_theme_spec(theme_spec)
    temp_theme = Theme(
        colors=dict(merged["colors"]),
        fonts=dict(merged["fonts"]),
        spacing=dict(merged["spacing"]),
        widgets=_resolve_widget_tokens(merged["widgets"], merged["colors"], merged["fonts"]),
        preset=merged.get("preset"),
    )
    border_spec = merged["border"]
    text_spec = merged["text"]
    border = BorderTheme(
        style=border_spec.get("style", "sharp"),
        fg_color=resolve_color_token(border_spec.get("fg_color"), temp_theme, DEFAULT_COLORS["border"]),
        bg_color=resolve_color_token(border_spec.get("bg_color"), temp_theme, DEFAULT_COLORS["surface"]),
        font_name=resolve_font_token(border_spec.get("font_name"), temp_theme, temp_theme.fonts.get("border")),
    )
    text = TextTheme(
        fg_color=resolve_color_token(text_spec.get("fg_color"), temp_theme, DEFAULT_COLORS["text"]),
        bg_color=resolve_color_token(text_spec.get("bg_color"), temp_theme, DEFAULT_COLORS["surface"]),
        font_name=resolve_font_token(text_spec.get("font_name"), temp_theme, temp_theme.fonts.get("text")),
    )
    return Theme(
        border=border,
        text=text,
        colors=temp_theme.colors,
        fonts=temp_theme.fonts,
        spacing=temp_theme.spacing,
        widgets=temp_theme.widgets,
        preset=temp_theme.preset,
    )


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


def resolve_color_token(value: Optional[str], theme: Theme, default: str = "default") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        return value
    if value.startswith("@font:"):
        return default
    if value.startswith("@"):
        return theme.colors.get(value[1:], default)
    return value


def resolve_font_token(value: Optional[str], theme: Theme, default: Optional[str] = None) -> Optional[str]:
    if value is None:
        return default
    if isinstance(value, str) and value.startswith("@font:"):
        return theme.fonts.get(value.split(":", 1)[1], default)
    return value


def resolve_style(
    fg_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    font_name: Optional[str] = None,
    fallback: Optional[Style] = None,
    theme: Optional[Theme] = None,
) -> Style:
    fallback = fallback or Style()
    if theme is not None:
        fg_color = resolve_color_token(fg_color, theme, fallback.fg_color) if fg_color is not None else fallback.fg_color
        bg_color = resolve_color_token(bg_color, theme, fallback.bg_color) if bg_color is not None else fallback.bg_color
        font_name = resolve_font_token(font_name, theme, fallback.font_name) if font_name is not None else fallback.font_name
    return Style(
        fg_color=fallback.fg_color if fg_color is None else fg_color,
        bg_color=fallback.bg_color if bg_color is None else bg_color,
        font_name=fallback.font_name if font_name is None else font_name,
    )


def themed_style(
    theme: Theme,
    widget: str,
    *,
    fg_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    font_name: Optional[str] = None,
    fg_slot: str = "fg_color",
    bg_slot: str = "bg_color",
    font_slot: str = "font_name",
    fallback: Optional[Style] = None,
) -> Style:
    return resolve_style(
        fg_color=fg_color if fg_color is not None else theme.widget_slot(widget, fg_slot, None),
        bg_color=bg_color if bg_color is not None else theme.widget_slot(widget, bg_slot, None),
        font_name=font_name if font_name is not None else theme.widget_slot(widget, font_slot, None),
        fallback=fallback,
        theme=theme,
    )


def _merge_nested_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key in set(left) | set(right):
        left_value = left.get(key)
        right_value = right.get(key)
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            merged[key] = _merge_nested_dict(left_value, right_value)
        elif key in right:
            merged[key] = right_value
        else:
            merged[key] = left_value
    return merged


def _resolve_widget_tokens(widgets: dict[str, dict[str, Any]], colors: dict[str, str], fonts: dict[str, Optional[str]]) -> dict[str, dict[str, Any]]:
    temp_theme = Theme(colors=dict(colors), fonts=dict(fonts))
    resolved: dict[str, dict[str, Any]] = {}
    for widget, slots in widgets.items():
        resolved[widget] = {}
        for slot, value in slots.items():
            if isinstance(value, str) and value.startswith("@font:"):
                resolved[widget][slot] = resolve_font_token(value, temp_theme, None)
            elif isinstance(value, str):
                resolved[widget][slot] = resolve_color_token(value, temp_theme, value)
            else:
                resolved[widget][slot] = value
    return resolved
