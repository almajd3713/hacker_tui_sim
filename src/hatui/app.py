from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

from hatui.core.input_manager import InputManager
from hatui.core.screen_buffer import ScreenBuffer
from hatui.core.terminal_env import TerminalEnvironment
from hatui.runtime.defaults import create_provider_registry, create_widget_registry
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
    ):
        self.spec_path = Path(spec_path)
        self.widget_registry = widget_registry or create_widget_registry()
        self.provider_registry = provider_registry or create_provider_registry()
        self.loader = ScreenSpecLoader(self.widget_registry, self.provider_registry)

        spec = self.loader.load_spec(self.spec_path)
        theme = self.loader.load_theme(spec)
        initial_state = self.loader.load_state(spec)
        router_spec = self.loader.load_router(spec)
        screen = self.loader.load_screen(spec)
        providers = self.loader.load_providers(spec)
        self.store = Store(initial_state=initial_state)
        self.router = Router(
            routes=list(router_spec.get("routes", []) or []),
            initial=router_spec.get("initial"),
        )

        self.root_widget = RootWidget(
            "root",
            children=[screen],
            theme=theme,
            store=self.store,
            router=self.router,
        )
        self.root_widget.focus_first(self.root_widget.context)
        self.root_widget._sync_focus(self.root_widget.context)
        self.provider_manager = ProviderManager(providers)

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
        self.provider_manager.update(context.delta_time, context)
        self.root_widget.update(context.delta_time, context)
        self.root_widget._sync_focus(context)
        self._last_frame_time = now

    def render_frame(self, *, width: int | None = None, height: int | None = None, flush: bool = False) -> ScreenBuffer:
        if width is not None and height is not None and (width, height) != (self.screen_buffer.width, self.screen_buffer.height):
            self.screen_buffer.resize(max(width, 1), max(height, 1))
        self.update()
        self.root_widget.allocate(self.screen_buffer.width, self.screen_buffer.height)
        self.root_widget.layout(0, 0, self.root_widget.context)
        self.root_widget.publish_debug_snapshot(self.root_widget.context)
        self.screen_buffer.clear()
        self.root_widget.paint(self.screen_buffer, self.root_widget.context)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hatui")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("spec", nargs="?", help="path to YAML spec")

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

    app = HatuiApp(spec_path=spec_path)
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
