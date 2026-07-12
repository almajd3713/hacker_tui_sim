from __future__ import annotations

from collections import deque
from time import perf_counter
from typing import Any

from hatui.providers.base import SKIP_RESULT, VALUE_RESULT
from hatui.runtime.bindings import set_path


class ProviderManager:
    def __init__(self, providers: list[Any]):
        self.providers = self._order_providers(providers)

    def setup(self, context):
        provider_status = context.data.setdefault("_providers", {})
        for provider in self.providers:
            provider_status.setdefault(provider.name, self._status_template(provider))
            provider.setup(context)

    def update(self, delta_time: float, context):
        provider_status = context.data.setdefault("_providers", {})
        for provider in self.providers:
            status = provider_status.setdefault(provider.name, self._status_template(provider))
            blocked_by = self._blocked_dependencies(provider, provider_status)
            if blocked_by:
                status["status"] = "blocked"
                status["blocked_by"] = blocked_by
                status["error"] = None
                status["last_reason"] = "dependency_error"
                status["blocked"] += 1
                self._write_metadata(provider, context, status)
                continue

            started = perf_counter()
            try:
                result = provider.update(delta_time, context)
                status["blocked_by"] = []
                status["last_duration_ms"] = round((perf_counter() - started) * 1000.0, 3)

                if result.state == SKIP_RESULT:
                    status["status"] = "waiting"
                    status["error"] = None
                    status["last_reason"] = result.reason
                    status["skips"] += 1
                    self._write_metadata(provider, context, status)
                    continue

                if result.state != VALUE_RESULT:
                    raise ValueError(f"Unknown provider result state: {result.state}")

                status["status"] = "ok"
                status["error"] = None
                status["last_reason"] = None
                status["attempts"] += 1
                status["successes"] += 1
                status["last_run_at"] = round(context.elapsed_time, 3)
                status["last_success_at"] = round(context.elapsed_time, 3)
                if provider.target and result.value is not None:
                    set_path(context.data, provider.target, result.value)
                self._write_metadata(provider, context, status)
            except Exception as exc:
                status["status"] = "error"
                status["error"] = str(exc)
                status["last_reason"] = "exception"
                status["attempts"] += 1
                status["errors"] += 1
                status["last_run_at"] = round(context.elapsed_time, 3)
                status["last_duration_ms"] = round((perf_counter() - started) * 1000.0, 3)
                self._write_metadata(provider, context, status)

    def teardown(self, context):
        for provider in self.providers:
            provider.teardown(context)

    def _order_providers(self, providers: list[Any]) -> list[Any]:
        by_name: dict[str, Any] = {}
        for provider in providers:
            if provider.name in by_name:
                raise ValueError(f"Duplicate provider name: {provider.name}")
            by_name[provider.name] = provider

        indegree = {provider.name: 0 for provider in providers}
        outgoing = {provider.name: [] for provider in providers}
        for provider in providers:
            for dependency in provider.depends_on:
                if dependency not in by_name:
                    raise ValueError(f"Provider '{provider.name}' depends on unknown provider '{dependency}'")
                indegree[provider.name] += 1
                outgoing[dependency].append(provider.name)

        queue = deque(provider.name for provider in providers if indegree[provider.name] == 0)
        ordered_names: list[str] = []
        while queue:
            name = queue.popleft()
            ordered_names.append(name)
            for dependent in outgoing[name]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)

        if len(ordered_names) != len(providers):
            unresolved = sorted(name for name, degree in indegree.items() if degree > 0)
            raise ValueError(f"Provider dependency cycle detected: {', '.join(unresolved)}")

        return [by_name[name] for name in ordered_names]

    def _blocked_dependencies(self, provider, provider_status: dict[str, dict[str, Any]]) -> list[str]:
        blocked: list[str] = []
        for dependency in provider.depends_on:
            dependency_status = provider_status.get(dependency, {})
            if dependency_status.get("status") in {"error", "blocked"}:
                blocked.append(dependency)
        return blocked

    def _status_template(self, provider) -> dict[str, Any]:
        return {
            "name": provider.name,
            "group": provider.group,
            "target": provider.target,
            "depends_on": list(provider.depends_on),
            "status": "idle",
            "error": None,
            "blocked_by": [],
            "attempts": 0,
            "successes": 0,
            "errors": 0,
            "skips": 0,
            "blocked": 0,
            "last_reason": None,
            "last_run_at": None,
            "last_success_at": None,
            "last_duration_ms": None,
        }

    def _write_metadata(self, provider, context, status: dict[str, Any]):
        if provider.metadata_target:
            set_path(context.data, provider.metadata_target, dict(status))
