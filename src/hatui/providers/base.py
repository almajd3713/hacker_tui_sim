from __future__ import annotations

from dataclasses import dataclass

from hatui.runtime.bindings import resolve_path


@dataclass
class ProviderResult:
    state: str
    value: object = None
    reason: str | None = None


SKIP_RESULT = "skip"
VALUE_RESULT = "value"


class Provider:
    def __init__(self, spec: dict):
        self.spec = spec
        self.name = spec.get("name", spec.get("type", self.__class__.__name__))
        self.target = spec.get("target")
        self.metadata_target = spec.get("metadata_target")
        self.interval = float(spec.get("interval", 0.0) or 0.0)
        self.group = spec.get("group", "default")
        self.depends_on = list(spec.get("depends_on", []) or [])
        self.enabled = spec.get("enabled", True)
        self._last_run = 0.0

    def setup(self, context):
        pass

    def is_enabled(self, context) -> bool:
        if isinstance(self.enabled, bool):
            return self.enabled
        if isinstance(self.enabled, str):
            return bool(resolve_path(context.data, self.enabled, False))
        return bool(self.enabled)

    def should_run(self, context) -> bool:
        if self.interval <= 0:
            return True
        return (context.elapsed_time - self._last_run) >= self.interval

    def update(self, delta_time: float, context):
        if not self.is_enabled(context):
            return ProviderResult(state=SKIP_RESULT, reason="disabled")
        if not self.should_run(context):
            return ProviderResult(state=SKIP_RESULT, reason="interval")
        self._last_run = context.elapsed_time
        return ProviderResult(state=VALUE_RESULT, value=self.provide(delta_time, context))

    def provide(self, delta_time: float, context):
        raise NotImplementedError

    def teardown(self, context):
        pass
