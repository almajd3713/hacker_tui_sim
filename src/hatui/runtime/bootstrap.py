from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hatui.runtime.loader import ScreenSpecLoader
from hatui.runtime.provider_manager import ProviderManager
from hatui.runtime.render_policy import RenderPolicy
from hatui.runtime.router import Router
from hatui.runtime.store import Store
from hatui.widgets.root_widget import RootWidget


@dataclass
class BootstrapResult:
    store: Store
    router: Router
    root_widget: RootWidget
    provider_manager: ProviderManager
    loaded_files: list[Path]
    dev_spec: dict[str, Any]


def merge_state(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = deepcopy(value)
            continue
        if isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_state(dict(merged[key]), value)
        else:
            merged[key] = deepcopy(value)
    return merged


def build_runtime(
    *,
    spec_path: Path,
    loader: ScreenSpecLoader,
    preserved_state: dict[str, Any] | None = None,
    preserved_stack: list[str] | None = None,
    preserved_focus: str | None = None,
    preserved_focus_map: dict[str, str] | None = None,
    glyph_mode: str = "unicode",
) -> BootstrapResult:
    spec = loader.load_spec(spec_path)
    theme = loader.load_theme(spec)
    initial_state = loader.load_state(spec)
    router_spec = loader.load_router(spec)
    dev_spec = loader.load_dev(spec)
    screen = loader.load_screen(spec)
    providers = loader.load_providers(spec)

    merged_state = merge_state(initial_state, preserved_state or {})
    store = Store(initial_state=merged_state)
    router = Router(
        routes=list(router_spec.get("routes", []) or []),
        initial=router_spec.get("initial"),
    )
    if preserved_stack:
        stack = [route for route in preserved_stack if router.has_route(route)]
        if not stack and router.current:
            stack = [router.current]
        if stack:
            router.stack = stack

    root_widget = RootWidget(
        "root",
        children=[screen],
        theme=theme,
        store=store,
        router=router,
        render_policy=RenderPolicy(glyph_mode=glyph_mode),
    )
    if preserved_focus_map:
        root_widget.state["last_focused_by_route"] = dict(preserved_focus_map)
    if preserved_focus:
        root_widget.context.focused_widget = preserved_focus
    root_widget.focus_first(root_widget.context)
    if preserved_focus:
        root_widget.context.focused_widget = preserved_focus
    root_widget.sync_focus(root_widget.context)

    return BootstrapResult(
        store=store,
        router=router,
        root_widget=root_widget,
        provider_manager=ProviderManager(providers),
        loaded_files=list(loader.last_loaded_files),
        dev_spec=dev_spec,
    )
