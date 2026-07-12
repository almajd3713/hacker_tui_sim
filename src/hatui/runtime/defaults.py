from __future__ import annotations

from copy import deepcopy

from hatui.providers import (
    ClockProvider,
    CommandOutputProvider,
    ComposeProvider,
    ConstantProvider,
    DemoLogsProvider,
    EnvProvider,
    EventStreamProvider,
    FileProvider,
    FrameProvider,
    GridHistoryProvider,
    HostInfoProvider,
    HttpJsonProvider,
    NormalizeStateProvider,
    RandomProvider,
    RecordsProvider,
    RollingWindowProvider,
    BucketProvider,
    SystemStatsProvider,
    TemplateProvider,
    ThresholdProvider,
    TransformProvider,
    WaveformProvider,
)
from hatui.runtime.registries import ProviderRegistry, WidgetRegistry
from hatui.widgets import (
    AlertWidget,
    AlertStackWidget,
    BannerWidget,
    BorderWidget,
    BoxWidget,
    CenterWidget,
    ChartWidget,
    CodeBlockWidget,
    ColumnWidget,
    DividerWidget,
    DiffViewerWidget,
    EventFeedWidget,
    FlowWidget,
    GaugeWidget,
    HeatmapWidget,
    HistogramWidget,
    HexDumpWidget,
    InspectorWidget,
    KVInspectorWidget,
    LabelWidget,
    ListWidget,
    LogWidget,
    MenuWidget,
    MetricGridWidget,
    MiniChartWidget,
    ModalHostWidget,
    ModalWidget,
    ParagraphWidget,
    ProgressBarWidget,
    RowWidget,
    ScrollWidget,
    SparklineWidget,
    StatusMatrixWidget,
    StatusStripWidget,
    StatWidget,
    SignalStripWidget,
    TableWidget,
    TabsWidget,
    TextWidget,
    TimelineWidget,
    TreeWidget,
)

GENERIC_WIDGET_KEYS = {"focusable", "selectable", "focus_fg_color", "focus_bg_color", "keybindings"}


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


def _build_modal_host(spec: dict, loader):
    child_spec = spec.get("child") or spec.get("screen")
    child = loader.build_widget(child_spec) if child_spec is not None else None
    modals = []
    for modal_spec in spec.get("modals", []):
        route = modal_spec.get("route")
        child_spec = modal_spec.get("child") or modal_spec.get("screen") or modal_spec.get("modal")
        if not route or child_spec is None:
            raise ValueError("Modal host entries require 'route' and 'child'/'screen'/'modal'")
        modals.append((route, loader.build_widget(child_spec)))
    kwargs = _clean(spec, {"type", "weight", "child", "screen", "modals", *GENERIC_WIDGET_KEYS})
    return ModalHostWidget(child=child, modals=modals, **kwargs)


def _build_plain(spec: dict, loader, widget_cls):
    kwargs = _clean(spec, {"type", "weight", *GENERIC_WIDGET_KEYS})
    return widget_cls(**kwargs)


def create_widget_registry() -> WidgetRegistry:
    registry = WidgetRegistry()
    registry.register("row", _build_row, widget_cls=RowWidget, allowed_keys={"children"}, required_keys={"children"})
    registry.register("column", _build_column, widget_cls=ColumnWidget, allowed_keys={"children"}, required_keys={"children"})
    registry.register("tabs", _build_tabs, widget_cls=TabsWidget, allowed_keys={"tabs"}, required_keys={"tabs"})
    registry.register("modal_host", _build_modal_host, widget_cls=ModalHostWidget, allowed_keys={"child", "screen", "modals"}, required_keys={"modals"})
    registry.register("box", lambda spec, loader: _build_single_child(spec, loader, BoxWidget), widget_cls=BoxWidget, allowed_keys={"child"})
    registry.register("border", lambda spec, loader: _build_single_child(spec, loader, BorderWidget), widget_cls=BorderWidget, allowed_keys={"child"})
    registry.register("center", _build_center, widget_cls=CenterWidget, allowed_keys={"child"})
    registry.register("scroll", lambda spec, loader: _build_single_child(spec, loader, ScrollWidget), widget_cls=ScrollWidget, allowed_keys={"child"})
    registry.register("modal", lambda spec, loader: _build_single_child(spec, loader, ModalWidget), widget_cls=ModalWidget, allowed_keys={"child"})

    registry.register("text", lambda spec, loader: _build_plain(spec, loader, TextWidget), widget_cls=TextWidget)
    registry.register("label", lambda spec, loader: _build_plain(spec, loader, LabelWidget), widget_cls=LabelWidget)
    registry.register("list", lambda spec, loader: _build_plain(spec, loader, ListWidget), widget_cls=ListWidget)
    registry.register("tree", lambda spec, loader: _build_plain(spec, loader, TreeWidget), widget_cls=TreeWidget)
    registry.register("menu", lambda spec, loader: _build_plain(spec, loader, MenuWidget), widget_cls=ListWidget)
    registry.register("paragraph", lambda spec, loader: _build_plain(spec, loader, ParagraphWidget), widget_cls=ParagraphWidget)
    registry.register("banner", lambda spec, loader: _build_plain(spec, loader, BannerWidget), widget_cls=BannerWidget)
    registry.register("alert", lambda spec, loader: _build_plain(spec, loader, AlertWidget), widget_cls=AlertWidget)
    registry.register("status_strip", lambda spec, loader: _build_plain(spec, loader, StatusStripWidget), widget_cls=StatusStripWidget)
    registry.register("signal_strip", lambda spec, loader: _build_plain(spec, loader, SignalStripWidget), widget_cls=SignalStripWidget)
    registry.register("status_matrix", lambda spec, loader: _build_plain(spec, loader, StatusMatrixWidget), widget_cls=StatusMatrixWidget)
    registry.register("alert_stack", lambda spec, loader: _build_plain(spec, loader, AlertStackWidget), widget_cls=ListWidget, allowed_keys={"source_width"})
    registry.register("kv_inspector", lambda spec, loader: _build_plain(spec, loader, KVInspectorWidget), widget_cls=KVInspectorWidget)

    registry.register("stat", lambda spec, loader: _build_plain(spec, loader, StatWidget), widget_cls=StatWidget)
    registry.register("progress_bar", lambda spec, loader: _build_plain(spec, loader, ProgressBarWidget), widget_cls=ProgressBarWidget)
    registry.register("sparkline", lambda spec, loader: _build_plain(spec, loader, SparklineWidget), widget_cls=SparklineWidget)
    registry.register("histogram", lambda spec, loader: _build_plain(spec, loader, HistogramWidget), widget_cls=HistogramWidget)
    registry.register("mini_chart", lambda spec, loader: _build_plain(spec, loader, MiniChartWidget), widget_cls=MiniChartWidget)
    registry.register("metric_grid", lambda spec, loader: _build_plain(spec, loader, MetricGridWidget), widget_cls=MetricGridWidget)
    registry.register("line_chart", lambda spec, loader: _build_plain({**spec, "mode": "line"}, loader, ChartWidget), widget_cls=ChartWidget)
    registry.register("area_chart", lambda spec, loader: _build_plain({**spec, "mode": "area"}, loader, ChartWidget), widget_cls=ChartWidget)
    registry.register("bar_chart", lambda spec, loader: _build_plain({**spec, "mode": "bar"}, loader, ChartWidget), widget_cls=ChartWidget)
    registry.register("gauge", lambda spec, loader: _build_plain(spec, loader, GaugeWidget), widget_cls=GaugeWidget)
    registry.register("heatmap", lambda spec, loader: _build_plain(spec, loader, HeatmapWidget), widget_cls=HeatmapWidget)
    registry.register("timeline", lambda spec, loader: _build_plain(spec, loader, TimelineWidget), widget_cls=TimelineWidget)
    registry.register("event_feed", lambda spec, loader: _build_plain(spec, loader, EventFeedWidget), widget_cls=EventFeedWidget)
    registry.register("inspector", lambda spec, loader: _build_plain(spec, loader, InspectorWidget), widget_cls=InspectorWidget)
    registry.register("diff_viewer", lambda spec, loader: _build_plain(spec, loader, DiffViewerWidget), widget_cls=DiffViewerWidget)
    registry.register("flow", lambda spec, loader: _build_plain(spec, loader, FlowWidget), widget_cls=FlowWidget)

    registry.register("log", lambda spec, loader: _build_plain(spec, loader, LogWidget), widget_cls=LogWidget)
    registry.register("table", lambda spec, loader: _build_plain(spec, loader, TableWidget), widget_cls=TableWidget)
    registry.register("code_block", lambda spec, loader: _build_plain(spec, loader, CodeBlockWidget), widget_cls=CodeBlockWidget)
    registry.register("hex_dump", lambda spec, loader: _build_plain(spec, loader, HexDumpWidget), widget_cls=HexDumpWidget)
    registry.register("divider", lambda spec, loader: _build_plain(spec, loader, DividerWidget), widget_cls=DividerWidget)
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
    registry.register("event_stream", EventStreamProvider)
    registry.register("grid_history", GridHistoryProvider)
    registry.register("normalize_state", NormalizeStateProvider)
    registry.register("bucket", BucketProvider)
    return registry
