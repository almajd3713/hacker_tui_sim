from __future__ import annotations

from copy import deepcopy

from hatui.providers import (
    ClockProvider,
    CommandOutputProvider,
    ComposeProvider,
    ConstantProvider,
    DemoLogsProvider,
    EnvProvider,
    FileProvider,
    FrameProvider,
    HostInfoProvider,
    HttpJsonProvider,
    RandomProvider,
    RecordsProvider,
    RollingWindowProvider,
    SystemStatsProvider,
    TemplateProvider,
    ThresholdProvider,
    TransformProvider,
    WaveformProvider,
)
from hatui.runtime.registries import ProviderRegistry, WidgetRegistry
from hatui.widgets import (
    AlertWidget,
    BannerWidget,
    BorderWidget,
    BoxWidget,
    CenterWidget,
    CodeBlockWidget,
    ColumnWidget,
    DividerWidget,
    HexDumpWidget,
    LabelWidget,
    LogWidget,
    MetricGridWidget,
    MiniChartWidget,
    ParagraphWidget,
    ProgressBarWidget,
    RowWidget,
    ScrollWidget,
    SparklineWidget,
    StatusStripWidget,
    StatWidget,
    TableWidget,
    TabsWidget,
    TextWidget,
)

GENERIC_WIDGET_KEYS = {"focusable", "focus_fg_color", "focus_bg_color", "keybindings"}


def _clean(spec: dict, excluded: set[str]) -> dict:
    return {key: deepcopy(value) for key, value in spec.items() if key not in excluded}


def _build_single_child(spec: dict, loader, widget_cls):
    kwargs = _clean(spec, {"type", "weight", "child", *GENERIC_WIDGET_KEYS})
    child = loader.build_widget(spec["child"]) if "child" in spec else None
    return widget_cls(child=child, **kwargs)


def _build_center(spec: dict, loader):
    kwargs = _clean(spec, {"type", "weight", "child", *GENERIC_WIDGET_KEYS})
    child = loader.build_widget(spec["child"]) if "child" in spec else None
    children = [child] if child is not None else []
    return CenterWidget(children=children, **kwargs)


def _build_row(spec: dict, loader):
    children = []
    for child_spec in spec.get("children", []):
        child = loader.build_widget(child_spec)
        children.append((child, child_spec.get("weight", 1)))
    kwargs = _clean(spec, {"type", "weight", "children", *GENERIC_WIDGET_KEYS})
    return RowWidget(children=children, **kwargs)


def _build_column(spec: dict, loader):
    children = []
    for child_spec in spec.get("children", []):
        child = loader.build_widget(child_spec)
        children.append((child, child_spec.get("weight", 1)))
    kwargs = _clean(spec, {"type", "weight", "children", *GENERIC_WIDGET_KEYS})
    return ColumnWidget(children=children, **kwargs)


def _build_tabs(spec: dict, loader):
    tabs = []
    for tab_spec in spec.get("tabs", []):
        title = tab_spec["title"]
        route = tab_spec.get("route", title.lower())
        child_spec = tab_spec.get("child") or tab_spec.get("screen")
        if child_spec is None:
            raise ValueError("Tab spec requires 'child' or 'screen'")
        tabs.append((title, loader.build_widget(child_spec), route))
    kwargs = _clean(spec, {"type", "weight", "tabs", *GENERIC_WIDGET_KEYS})
    return TabsWidget(tabs=tabs, **kwargs)


def _build_plain(spec: dict, loader, widget_cls):
    kwargs = _clean(spec, {"type", "weight", *GENERIC_WIDGET_KEYS})
    return widget_cls(**kwargs)


def create_widget_registry() -> WidgetRegistry:
    registry = WidgetRegistry()
    registry.register("row", _build_row)
    registry.register("column", _build_column)
    registry.register("tabs", _build_tabs)
    registry.register("box", lambda spec, loader: _build_single_child(spec, loader, BoxWidget))
    registry.register("border", lambda spec, loader: _build_single_child(spec, loader, BorderWidget))
    registry.register("center", _build_center)
    registry.register("scroll", lambda spec, loader: _build_single_child(spec, loader, ScrollWidget))

    registry.register("text", lambda spec, loader: _build_plain(spec, loader, TextWidget))
    registry.register("label", lambda spec, loader: _build_plain(spec, loader, LabelWidget))
    registry.register("paragraph", lambda spec, loader: _build_plain(spec, loader, ParagraphWidget))
    registry.register("banner", lambda spec, loader: _build_plain(spec, loader, BannerWidget))
    registry.register("alert", lambda spec, loader: _build_plain(spec, loader, AlertWidget))
    registry.register("status_strip", lambda spec, loader: _build_plain(spec, loader, StatusStripWidget))

    registry.register("stat", lambda spec, loader: _build_plain(spec, loader, StatWidget))
    registry.register("progress_bar", lambda spec, loader: _build_plain(spec, loader, ProgressBarWidget))
    registry.register("sparkline", lambda spec, loader: _build_plain(spec, loader, SparklineWidget))
    registry.register("mini_chart", lambda spec, loader: _build_plain(spec, loader, MiniChartWidget))
    registry.register("metric_grid", lambda spec, loader: _build_plain(spec, loader, MetricGridWidget))

    registry.register("log", lambda spec, loader: _build_plain(spec, loader, LogWidget))
    registry.register("table", lambda spec, loader: _build_plain(spec, loader, TableWidget))
    registry.register("code_block", lambda spec, loader: _build_plain(spec, loader, CodeBlockWidget))
    registry.register("hex_dump", lambda spec, loader: _build_plain(spec, loader, HexDumpWidget))
    registry.register("divider", lambda spec, loader: _build_plain(spec, loader, DividerWidget))
    return registry


def create_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("constant", ConstantProvider)
    registry.register("clock", ClockProvider)
    registry.register("frame", FrameProvider)
    registry.register("random", RandomProvider)
    registry.register("waveform", WaveformProvider)
    registry.register("demo_logs", DemoLogsProvider)
    registry.register("env", EnvProvider)
    registry.register("file", FileProvider)
    registry.register("host_info", HostInfoProvider)
    registry.register("system_stats", SystemStatsProvider)
    registry.register("command_output", CommandOutputProvider)
    registry.register("http_json", HttpJsonProvider)
    registry.register("transform", TransformProvider)
    registry.register("template", TemplateProvider)
    registry.register("compose", ComposeProvider)
    registry.register("records", RecordsProvider)
    registry.register("rolling_window", RollingWindowProvider)
    registry.register("threshold", ThresholdProvider)
    return registry
