from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

from hatui.runtime.bootstrap import build_runtime
from hatui.runtime.cli import build_parser, normalize_argv, resolve_spec_context, write_cli_text
from hatui.runtime.defaults import create_provider_registry, create_widget_registry
from hatui.runtime.engine import AppEngine
from hatui.runtime.loader import ScreenSpecLoader
from hatui.runtime.watcher import SpecWatcher


class HatuiApp:
    def __init__(
        self,
        spec_path: str | Path,
        *,
        widget_registry=None,
        provider_registry=None,
        watch: bool = False,
        bundled_demo: bool = False,
    ):
        self.spec_path = Path(spec_path)
        self.is_bundled_demo = bundled_demo
        self.widget_registry = widget_registry or create_widget_registry()
        self.provider_registry = provider_registry or create_provider_registry()
        self.loader = ScreenSpecLoader(self.widget_registry, self.provider_registry)
        self.engine = AppEngine()
        self.watcher = SpecWatcher(cli_watch=watch, allow_watch=not bundled_demo)
        self.loaded_files: list[Path] = []
        self._bootstrap_runtime()

    @property
    def screen_buffer(self):
        return self.engine.screen_buffer

    @property
    def input_manager(self):
        return self.engine.input_manager

    @property
    def environment(self):
        return self.engine.environment

    def _bootstrap_runtime(
        self,
        *,
        preserved_state: dict | None = None,
        preserved_stack: list[str] | None = None,
        preserved_focus: str | None = None,
        preserved_focus_map: dict[str, str] | None = None,
    ) -> None:
        runtime = build_runtime(
            spec_path=self.spec_path,
            loader=self.loader,
            preserved_state=preserved_state,
            preserved_stack=preserved_stack,
            preserved_focus=preserved_focus,
            preserved_focus_map=preserved_focus_map,
        )
        self.store = runtime.store
        self.router = runtime.router
        self.root_widget = runtime.root_widget
        self.provider_manager = runtime.provider_manager
        self.loaded_files = runtime.loaded_files
        self.watcher.configure(
            spec_path=self.spec_path,
            loaded_files=self.loaded_files,
            dev_spec=runtime.dev_spec,
        )

    def debug_snapshot(self) -> dict[str, object]:
        watch = self.watcher.snapshot()
        return {
            "watch_enabled": watch.enabled,
            "watch_interval_s": watch.interval_s,
            "watch_debounce_s": watch.debounce_s,
            "watched_files": watch.watched_files,
            "watched_file_count": len(watch.watched_files),
            "pending_reload": watch.pending_reload,
            "pending_changed_files": watch.pending_changed_files,
            "reload_count": watch.reload_count,
            "last_reload_at": watch.last_reload_at,
            "last_reload_error": watch.last_reload_error,
            **self.engine.stats.as_dict(),
        }

    def render_frame(self, *, width: int | None = None, height: int | None = None, flush: bool = False):
        return self.engine.render_frame(self, width=width, height=height, flush=flush)

    def preview(self, *, width: int = 100, height: int = 32, frames: int = 1, route: str | None = None) -> str:
        if route:
            self.root_widget.route_set(route, self.root_widget.context)
        self.engine.activate_providers(self)
        try:
            for _ in range(max(frames, 1)):
                self.render_frame(width=width, height=height, flush=False)
            return self.screen_buffer.to_plain_text()
        finally:
            self.engine.deactivate_providers(self)

    def reload(self) -> None:
        previous_state = deepcopy(self.store.state)
        previous_stack = list(self.router.stack)
        previous_focus = self.root_widget.context.focused_widget
        previous_focus_map = dict(self.root_widget.state.get("last_focused_by_route", {}))
        old_store = self.store
        old_router = self.router
        old_root_widget = self.root_widget
        old_provider_manager = self.provider_manager
        old_loaded_files = list(self.loaded_files)
        watcher_state = self.watcher.capture_state()
        providers_active = self.engine.providers_active
        self.engine.deactivate_providers(self)
        try:
            self._bootstrap_runtime(
                preserved_state=previous_state,
                preserved_stack=previous_stack,
                preserved_focus=previous_focus,
                preserved_focus_map=previous_focus_map,
            )
            if providers_active:
                self.engine.activate_providers(self)
            self.watcher.mark_reload_success(round(self.engine.elapsed_time, 3))
        except Exception:
            self.store = old_store
            self.router = old_router
            self.root_widget = old_root_widget
            self.provider_manager = old_provider_manager
            self.loaded_files = old_loaded_files
            self.watcher.restore_state(watcher_state)
            if providers_active:
                self.engine.activate_providers(self)
            raise

    def run(self):
        with self.environment.manage():
            self.engine.activate_providers(self)
            try:
                while True:
                    self.engine.dispatch_input(self)
                    self.engine.resize_to_terminal()
                    if self.watcher.should_reload():
                        try:
                            self.reload()
                        except Exception as exc:
                            self.watcher.mark_reload_error(str(exc))
                    self.render_frame(flush=True)
            except KeyboardInterrupt:
                pass
            finally:
                self.engine.deactivate_providers(self)


def main():
    argv = normalize_argv()
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command or "run"
    spec_arg = getattr(args, "spec", None)
    spec_context, is_bundled_demo = resolve_spec_context(spec_arg)

    with spec_context as spec_path:
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

        app = HatuiApp(
            spec_path=spec_path,
            watch=bool(getattr(args, "watch", False)),
            bundled_demo=is_bundled_demo,
        )
        if command == "preview":
            preview_text = app.preview(
                width=max(args.width, 1),
                height=max(args.height, 1),
                frames=max(args.frames, 1),
                route=args.route,
            )
            write_cli_text(preview_text)
            return
        app.run()


if __name__ == "__main__":
    main()
