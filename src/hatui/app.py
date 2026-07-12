from __future__ import annotations

import argparse
import glob
import shutil
import sys
import time
from pathlib import Path
from copy import deepcopy

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.terminal_env import TerminalEnvironment
from hatui.runtime.defaults import create_provider_registry, create_widget_registry
from hatui.runtime.bindings import set_path
from hatui.runtime.loader import ScreenSpecLoader
from hatui.runtime.provider_manager import ProviderManager
from hatui.runtime.router import Router
from hatui.runtime.store import Store
from hatui.widgets.root_widget import RootWidget


class HatuiApp:
    def __init__(
        self,
        spec_path: str | Path,
        *,
        widget_registry=None,
        provider_registry=None,
        watch: bool = False,
    ):
        self.spec_path = Path(spec_path)
        self.watch = watch
        self.widget_registry = widget_registry or create_widget_registry()
        self.provider_registry = provider_registry or create_provider_registry()
        self.loader = ScreenSpecLoader(self.widget_registry, self.provider_registry)
        self.loaded_files: list[Path] = []
        self.extra_watch_files: list[Path] = []
        self._watched_mtimes: dict[Path, float] = {}
        self._last_watch_check = 0.0
        self._watch_interval = 0.35
        self._watch_debounce = 0.2
        self._pending_reload_since: float | None = None
        self._pending_changed_files: list[str] = []
        self._reload_count = 0
        self._last_reload_at: float | None = None
        self._last_reload_error: str | None = None
        self._last_frame_stats: dict[str, float] = {
            "provider_ms": 0.0,
            "widget_update_ms": 0.0,
            "focus_sync_ms": 0.0,
            "allocate_ms": 0.0,
            "layout_ms": 0.0,
            "paint_ms": 0.0,
            "frame_ms": 0.0,
        }
        self._bootstrap_runtime()

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

                    self._reload_if_changed()
                    self.render_frame(flush=True)
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
        provider_started = time.perf_counter()
        self.provider_manager.update(context.delta_time, context)
        provider_ms = (time.perf_counter() - provider_started) * 1000.0
        widget_started = time.perf_counter()
        self.root_widget.update(context.delta_time, context)
        widget_update_ms = (time.perf_counter() - widget_started) * 1000.0
        focus_started = time.perf_counter()
        self.root_widget._sync_focus(context)
        focus_sync_ms = (time.perf_counter() - focus_started) * 1000.0
        self._last_frame_stats["provider_ms"] = round(provider_ms, 3)
        self._last_frame_stats["widget_update_ms"] = round(widget_update_ms, 3)
        self._last_frame_stats["focus_sync_ms"] = round(focus_sync_ms, 3)
        self._last_frame_time = now

    def render_frame(self, *, width: int | None = None, height: int | None = None, flush: bool = False) -> ScreenBuffer:
        frame_started = time.perf_counter()
        if width is not None and height is not None and (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
            self.screen_buffer.resize(max(width, 1), max(height, 1))
        self.update()
        allocate_started = time.perf_counter()
        self.root_widget.allocate(self.screen_buffer.width, self.screen_buffer.height)
        self._last_frame_stats["allocate_ms"] = round((time.perf_counter() - allocate_started) * 1000.0, 3)
        layout_started = time.perf_counter()
        self.root_widget.layout(0, 0, self.root_widget.context)
        self._last_frame_stats["layout_ms"] = round((time.perf_counter() - layout_started) * 1000.0, 3)
        self.root_widget.publish_debug_snapshot(self.root_widget.context)
        self._publish_app_debug()
        self.screen_buffer.clear()
        paint_started = time.perf_counter()
        self.root_widget.paint(self.screen_buffer, self.root_widget.context)
        self._last_frame_stats["paint_ms"] = round((time.perf_counter() - paint_started) * 1000.0, 3)
        self._last_frame_stats["frame_ms"] = round((time.perf_counter() - frame_started) * 1000.0, 3)
        self.root_widget.publish_debug_snapshot(self.root_widget.context)
        self._publish_app_debug()
        if flush:
            self.screen_buffer.flush()
        return self.screen_buffer

    def preview(self, *, width: int = 100, height: int = 32, frames: int = 1, route: str | None = None) -> str:
        if route:
            self.root_widget.route_set(route, self.root_widget.context)
        self.provider_manager.setup(self.root_widget.context)
        try:
            for _ in range(max(frames, 1)):
                self.render_frame(width=width, height=height, flush=False)
            return self.screen_buffer.to_plain_text()
        finally:
            self.provider_manager.teardown(self.root_widget.context)

    def reload(self) -> None:
        old_store = self.store
        old_router = self.router
        old_root_widget = self.root_widget
        old_provider_manager = self.provider_manager
        old_loaded_files = list(self.loaded_files)
        old_watched_mtimes = dict(self._watched_mtimes)
        previous_state = deepcopy(self.store.state)
        previous_stack = list(self.router.stack)
        previous_focus = self.root_widget.context.focused_widget
        previous_focus_map = dict(self.root_widget.state.get("last_focused_by_route", {}))
        old_provider_manager.teardown(old_root_widget.context)
        try:
            self._bootstrap_runtime(
                preserved_state=previous_state,
                preserved_stack=previous_stack,
                preserved_focus=previous_focus,
                preserved_focus_map=previous_focus_map,
            )
            self.provider_manager.setup(self.root_widget.context)
            self._reload_count += 1
            self._last_reload_at = round(time.monotonic() - self._start_time, 3)
            self._last_reload_error = None
        except Exception:
            self.store = old_store
            self.router = old_router
            self.root_widget = old_root_widget
            self.provider_manager = old_provider_manager
            self.loaded_files = old_loaded_files
            self._watched_mtimes = old_watched_mtimes
            self.provider_manager.setup(self.root_widget.context)
            raise

    def _bootstrap_runtime(
        self,
        *,
        preserved_state: dict | None = None,
        preserved_stack: list[str] | None = None,
        preserved_focus: str | None = None,
        preserved_focus_map: dict[str, str] | None = None,
    ) -> None:
        spec = self.loader.load_spec(self.spec_path)
        theme = self.loader.load_theme(spec)
        initial_state = self.loader.load_state(spec)
        router_spec = self.loader.load_router(spec)
        dev_spec = self.loader.load_dev(spec)
        screen = self.loader.load_screen(spec)
        providers = self.loader.load_providers(spec)
        self.loaded_files = list(self.loader.last_loaded_files)
        self._apply_watch_config(dev_spec)
        self._refresh_watched_files()

        merged_state = deepcopy(initial_state)
        if preserved_state:
            merged_state = self._merge_state(merged_state, preserved_state)
        self.store = Store(initial_state=merged_state)
        self.router = Router(
            routes=list(router_spec.get("routes", []) or []),
            initial=router_spec.get("initial"),
        )
        if preserved_stack:
            stack = [route for route in preserved_stack if self.router.has_route(route)]
            if not stack and self.router.current:
                stack = [self.router.current]
            if stack:
                self.router.stack = stack

        self.root_widget = RootWidget(
            "root",
            children=[screen],
            theme=theme,
            store=self.store,
            router=self.router,
        )
        if preserved_focus_map:
            self.root_widget.state["last_focused_by_route"] = dict(preserved_focus_map)
        if preserved_focus:
            self.root_widget.context.focused_widget = preserved_focus
        self.root_widget.focus_first(self.root_widget.context)
        if preserved_focus:
            self.root_widget.context.focused_widget = preserved_focus
        self.root_widget._sync_focus(self.root_widget.context)
        self.provider_manager = ProviderManager(providers)

    def _merge_state(self, base: dict, incoming: dict) -> dict:
        for key, value in incoming.items():
            if key not in base:
                base[key] = deepcopy(value)
                continue
            if isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_state(dict(base[key]), value)
            else:
                base[key] = deepcopy(value)
        return base

    def _refresh_watched_files(self) -> None:
        self._watched_mtimes = {}
        watched = self._collect_watched_files()
        for path in watched:
            try:
                self._watched_mtimes[path] = path.stat().st_mtime
            except FileNotFoundError:
                self._watched_mtimes[path] = 0.0

    def _reload_if_changed(self) -> None:
        if not self.watch:
            return
        now = time.monotonic()
        if now - self._last_watch_check < self._watch_interval:
            return
        self._last_watch_check = now
        changed_files = self._changed_watched_files()
        if not changed_files:
            self._pending_reload_since = None
            self._pending_changed_files = []
            return
        self._pending_changed_files = [str(path) for path in changed_files]
        if self._pending_reload_since is None:
            self._pending_reload_since = now
            return
        if now - self._pending_reload_since < self._watch_debounce:
            return
        try:
            self.reload()
        except Exception as exc:
            self._last_reload_error = str(exc)
        finally:
            self._pending_reload_since = None
            self._pending_changed_files = []

    def _changed_watched_files(self) -> list[Path]:
        changed: list[Path] = []
        for path, recorded_mtime in list(self._watched_mtimes.items()):
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                current_mtime = 0.0
            if current_mtime != recorded_mtime:
                changed.append(path)
        return changed

    def _publish_app_debug(self) -> None:
        context = self.root_widget.context
        set_path(
            context.data,
            "_debug.stats",
            {
                "watch_enabled": self.watch,
                "watch_interval_s": self._watch_interval,
                "watch_debounce_s": self._watch_debounce,
                "watched_files": [str(path) for path in self._collect_watched_files()],
                "watched_file_count": len(self._collect_watched_files()),
                "pending_reload": self._pending_reload_since is not None,
                "pending_changed_files": list(self._pending_changed_files),
                "reload_count": self._reload_count,
                "last_reload_at": self._last_reload_at,
                "last_reload_error": self._last_reload_error,
                **self._last_frame_stats,
            },
        )

    def _apply_watch_config(self, dev_spec: dict) -> None:
        watch_spec = dict(dev_spec.get("watch", {}) or {})
        if "enabled" in watch_spec:
            self.watch = bool(watch_spec["enabled"]) or self.watch
        if "interval" in watch_spec:
            self._watch_interval = max(float(watch_spec["interval"]), 0.05)
        if "debounce" in watch_spec:
            self._watch_debounce = max(float(watch_spec["debounce"]), 0.0)
        self.extra_watch_files = self._resolve_watch_paths(watch_spec.get("paths", []))

    def _resolve_watch_paths(self, patterns: list[str]) -> list[Path]:
        resolved: list[Path] = []
        base_dir = self.spec_path.resolve().parent
        for pattern in patterns:
            absolute_pattern = str((base_dir / pattern).resolve()) if not Path(pattern).is_absolute() else pattern
            matches = [Path(item).resolve() for item in glob.glob(absolute_pattern, recursive=True)]
            if matches:
                resolved.extend(matches)
            else:
                resolved.append(Path(absolute_pattern).resolve())
        unique: list[Path] = []
        seen: set[Path] = set()
        for path in resolved:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    def _collect_watched_files(self) -> list[Path]:
        combined = list(self.loaded_files) + list(self.extra_watch_files)
        unique: list[Path] = []
        seen: set[Path] = set()
        for path in combined:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hatui")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("spec", nargs="?", help="path to YAML spec")
    run_parser.add_argument("--watch", action="store_true", help="reload spec when watched files change")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("spec", nargs="?", help="path to YAML spec")

    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("spec", nargs="?", help="path to YAML spec")
    preview_parser.add_argument("--route")
    preview_parser.add_argument("--width", type=int, default=100)
    preview_parser.add_argument("--height", type=int, default=32)
    preview_parser.add_argument("--frames", type=int, default=1)
    return parser


def main():
    default_spec = Path(__file__).resolve().parents[2] / "screens" / "dashboard.yaml"
    argv = sys.argv[1:]
    if argv and argv[0] not in {"run", "validate", "preview"}:
        argv = ["run", *argv]
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command or "run"
    spec_arg = getattr(args, "spec", None)

    spec_path = Path(spec_arg) if spec_arg else default_spec

    if command == "validate":
        loader = ScreenSpecLoader(create_widget_registry(), create_provider_registry())
        messages = loader.validate_spec(spec_path)
        errors = [message for message in messages if message.level == "error"]
        if errors:
            for message in errors:
                print(message.format(), file=sys.stderr)
            raise SystemExit(1)
        print(f"Valid Hatui spec: {spec_path}")
        return

    app = HatuiApp(spec_path=spec_path, watch=bool(getattr(args, "watch", False)))
    if command == "preview":
        print(
            app.preview(
                width=max(args.width, 1),
                height=max(args.height, 1),
                frames=max(args.frames, 1),
                route=args.route,
            )
        )
        return
    app.run()


if __name__ == "__main__":
    main()
