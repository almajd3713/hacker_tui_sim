from typing import Any

from hatui.runtime.bindings import set_path


class ProviderManager:
    def __init__(self, providers: list[Any]):
        self.providers = providers

    def setup(self, context):
        for provider in self.providers:
            provider.setup(context)

    def update(self, delta_time: float, context):
        provider_status = context.data.setdefault("_providers", {})
        for provider in self.providers:
            try:
                value = provider.update(delta_time, context)
                provider_status[provider.name] = {"status": "ok", "error": None}
                if provider.target and value is not None:
                    set_path(context.data, provider.target, value)
            except Exception as exc:
                provider_status[provider.name] = {"status": "error", "error": str(exc)}

    def teardown(self, context):
        for provider in self.providers:
            provider.teardown(context)
