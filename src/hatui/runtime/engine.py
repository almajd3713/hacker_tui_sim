from __future__ import annotations

import shutil
import time
from dataclasses import dataclass

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.terminal_env import TerminalEnvironment
from hatui.runtime.bindings import set_path


@dataclass
class FrameStats:
    provider_ms: float = 0.0
    widget_update_ms: float = 0.0
    focus_sync_ms: float = 0.0
    allocate_ms: float = 0.0
    layout_ms: float = 0.0
    paint_ms: float = 0.0
    frame_ms: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "provider_ms": self.provider_ms,
            "widget_update_ms": self.widget_update_ms,
            "focus_sync_ms": self.focus_sync_ms,
            "allocate_ms": self.allocate_ms,
            "layout_ms": self.layout_ms,
            "paint_ms": self.paint_ms,
            "frame_ms": self.frame_ms,
        }


class AppEngine:
    def __init__(self):
        width, height = self.get_terminal_size()
        self.screen_buffer = ScreenBuffer(width=width, height=height)
        self.environment = TerminalEnvironment()
        self.input_manager = InputManager()
        self.stats = FrameStats()
        self._last_frame_time = time.monotonic()
        self._start_time = self._last_frame_time
        self._providers_active = False

    @staticmethod
    def get_terminal_size() -> tuple[int, int]:
        size = shutil.get_terminal_size(fallback=(100, 32))
        return max(size.columns, 1), max(size.lines, 1)

    @property
    def elapsed_time(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def providers_active(self) -> bool:
        return self._providers_active

    def resize_to_terminal(self) -> None:
        width, height = self.get_terminal_size()
        if (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
            self.screen_buffer.resize(width, height)

    def activate_providers(self, app) -> None:
        if self._providers_active:
            return
        app.provider_manager.setup(app.root_widget.context)
        self._providers_active = True

    def deactivate_providers(self, app) -> None:
        if not self._providers_active:
            return
        app.provider_manager.teardown(app.root_widget.context)
        self._providers_active = False

    def dispatch_input(self, app) -> None:
        key_event = self.input_manager.poll_input(timeout=0.05)
        if key_event is None:
            return
        key, modifiers = key_event
        app.root_widget.context.last_key = key
        app.root_widget.context.last_modifiers = list(modifiers)
        app.root_widget.dispatch_key_event(key, modifiers, app.root_widget.context)

    def render_frame(self, app, *, width: int | None = None, height: int | None = None, flush: bool = False):
        frame_started = time.perf_counter()
        if width is not None and height is not None and (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
            self.screen_buffer.resize(max(width, 1), max(height, 1))

        self._update_runtime(app)

        allocate_started = time.perf_counter()
        app.root_widget.allocate(self.screen_buffer.width, self.screen_buffer.height)
        self.stats.allocate_ms = round((time.perf_counter() - allocate_started) * 1000.0, 3)

        layout_started = time.perf_counter()
        app.root_widget.layout(0, 0, app.root_widget.context)
        self.stats.layout_ms = round((time.perf_counter() - layout_started) * 1000.0, 3)

        self.screen_buffer.clear()
        paint_started = time.perf_counter()
        app.root_widget.paint(self.screen_buffer, app.root_widget.context)
        self.stats.paint_ms = round((time.perf_counter() - paint_started) * 1000.0, 3)
        self.stats.frame_ms = round((time.perf_counter() - frame_started) * 1000.0, 3)

        app.root_widget.publish_debug_snapshot(app.root_widget.context)
        set_path(app.root_widget.context.data, "_debug.stats", app.debug_snapshot())

        if flush:
            self.screen_buffer.flush()
        return self.screen_buffer

    def _update_runtime(self, app) -> None:
        now = time.monotonic()
        context = app.root_widget.context
        context.delta_time = now - self._last_frame_time
        context.elapsed_time = now - self._start_time
        context.frame += 1
        context.terminal_width = self.screen_buffer.width
        context.terminal_height = self.screen_buffer.height
        context.widget_width = self.screen_buffer.width
        context.widget_height = self.screen_buffer.height

        provider_started = time.perf_counter()
        app.provider_manager.update(context.delta_time, context)
        self.stats.provider_ms = round((time.perf_counter() - provider_started) * 1000.0, 3)

        widget_started = time.perf_counter()
        app.root_widget.update(context.delta_time, context)
        self.stats.widget_update_ms = round((time.perf_counter() - widget_started) * 1000.0, 3)

        focus_started = time.perf_counter()
        app.root_widget._sync_focus(context)
        self.stats.focus_sync_ms = round((time.perf_counter() - focus_started) * 1000.0, 3)
        self._last_frame_time = now
