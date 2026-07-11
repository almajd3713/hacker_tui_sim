from __future__ import annotations

import time


class Provider:
    def __init__(self, spec: dict):
        self.spec = spec
        self.name = spec.get("name", spec.get("type", self.__class__.__name__))
        self.target = spec.get("target")
        self.interval = float(spec.get("interval", 0.0) or 0.0)
        self._last_run = 0.0

    def setup(self, context):
        pass

    def should_run(self, context) -> bool:
        if self.interval <= 0:
            return True
        return (context.elapsed_time - self._last_run) >= self.interval

    def update(self, delta_time: float, context):
        if not self.should_run(context):
            return None
        self._last_run = context.elapsed_time
        return self.provide(delta_time, context)

    def provide(self, delta_time: float, context):
        raise NotImplementedError

    def teardown(self, context):
        pass
