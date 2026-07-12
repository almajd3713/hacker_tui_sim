from __future__ import annotations

import json
import math
import os
import platform
import random
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

from hatui.providers.base import Provider
from hatui.providers.helpers import render_template, resolve_items, resolve_mapping, resolve_value_spec


class ConstantProvider(Provider):
    spec_schema = {"value": object}

    def provide(self, delta_time: float, context):
        return self.spec.get("value")


class ClockProvider(Provider):
    def provide(self, delta_time: float, context):
        now = time.time()
        local = time.localtime(now)
        utc = time.gmtime(now)
        return {
            "timestamp": now,
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S", local),
            "time": time.strftime("%H:%M:%S", local),
            "date": time.strftime("%Y-%m-%d", local),
            "utc_time": time.strftime("%H:%M:%S", utc),
        }


class FrameProvider(Provider):
    def provide(self, delta_time: float, context):
        return {
            "frame": context.frame,
            "delta_time": context.delta_time,
            "elapsed_time": context.elapsed_time,
            "terminal_width": context.terminal_width,
            "terminal_height": context.terminal_height,
        }


class RandomProvider(Provider):
    spec_schema = {
        "mode": str,
        "min": float,
        "max": float,
        "choices": list,
        "count": int,
        "step": float,
    }

    def provide(self, delta_time: float, context):
        mode = self.spec.get("mode", "float")
        if mode == "int":
            return random.randint(int(self.spec.get("min", 0)), int(self.spec.get("max", 100)))
        if mode == "choice":
            return random.choice(list(self.spec.get("choices", [])))
        if mode == "series":
            count = int(self.spec.get("count", 16))
            minimum = float(self.spec.get("min", 0.0))
            maximum = float(self.spec.get("max", 1.0))
            return [random.uniform(minimum, maximum) for _ in range(count)]
        minimum = float(self.spec.get("min", 0.0))
        maximum = float(self.spec.get("max", 1.0))
        return random.uniform(minimum, maximum)


class WaveformProvider(Provider):
    spec_schema = {
        "phase": float,
        "frequency": float,
        "amplitude": float,
        "offset": float,
        "waveform": str,
        "count": int,
        "step": float,
    }

    def provide(self, delta_time: float, context):
        phase = float(self.spec.get("phase", 0.0))
        frequency = float(self.spec.get("frequency", 1.0))
        amplitude = float(self.spec.get("amplitude", 1.0))
        offset = float(self.spec.get("offset", 0.0))
        waveform = self.spec.get("waveform", "sine")
        count = int(self.spec.get("count", 0))

        def sample(value: float) -> float:
            angle = (context.elapsed_time + phase + value) * frequency
            if waveform == "triangle":
                base = 2 * abs(2 * (angle - math.floor(angle + 0.5))) - 1
            elif waveform == "saw":
                base = 2 * (angle - math.floor(angle + 0.5))
            else:
                base = math.sin(angle)
            return offset + amplitude * base

        if count > 0:
            step = float(self.spec.get("step", 0.25))
            return [sample(index * step) for index in range(count)]
        return sample(0.0)


class DemoLogsProvider(Provider):
    spec_schema = {"messages": list, "max_lines": int}

    def setup(self, context):
        self.messages = self.spec.get(
            "messages",
            [
                {"level": "info", "text": "Link state nominal; passive scan continuing."},
                {"level": "warn", "text": "Signal jitter crossed advisory threshold."},
                {"level": "success", "text": "Remote cache sync completed without drift."},
                {"level": "error", "text": "Packet loss spike detected on relay-03."},
            ],
        )
        self.index = 0
        self.lines: list[dict] = []

    def provide(self, delta_time: float, context):
        message = dict(self.messages[self.index % len(self.messages)])
        message.setdefault("timestamp", time.strftime("%H:%M:%S", time.localtime()))
        self.lines.append(message)
        self.lines = self.lines[-int(self.spec.get("max_lines", 80)) :]
        self.index += 1
        return list(self.lines)


class EnvProvider(Provider):
    spec_schema = {"key": str, "keys": list, "default": object}

    def provide(self, delta_time: float, context):
        key = self.spec.get("key")
        keys = self.spec.get("keys")
        if key is not None:
            return os.environ.get(key, self.spec.get("default"))
        if keys is not None:
            return {item: os.environ.get(item) for item in keys}
        return dict(os.environ)


class FileProvider(Provider):
    spec_schema = {"path": str, "mode": str}
    required_spec_keys = {"path"}

    def provide(self, delta_time: float, context):
        path = Path(self.spec["path"])
        mode = self.spec.get("mode", "text")
        if mode == "lines":
            return path.read_text(encoding="utf-8").splitlines()
        if mode == "json":
            return json.loads(path.read_text(encoding="utf-8"))
        return path.read_text(encoding="utf-8")


class HostInfoProvider(Provider):
    def provide(self, delta_time: float, context):
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cwd": os.getcwd(),
            "pid": os.getpid(),
        }


class SystemStatsProvider(Provider):
    spec_schema = {"path": str}

    def provide(self, delta_time: float, context):
        stats = {
            "cpu_count": os.cpu_count(),
            "loadavg": None,
            "disk": {},
            "memory": {},
        }
        if hasattr(os, "getloadavg"):
            load = os.getloadavg()
            stats["loadavg"] = {"1m": load[0], "5m": load[1], "15m": load[2]}
        usage = shutil.disk_usage(self.spec.get("path", os.getcwd()))
        stats["disk"] = {"total": usage.total, "used": usage.used, "free": usage.free}
        try:
            import resource

            max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            stats["memory"] = {"rss_kb": max_rss}
        except Exception:
            stats["memory"] = {}
        return stats


class CommandOutputProvider(Provider):
    spec_schema = {"command": str, "mode": str}
    required_spec_keys = {"command"}

    def provide(self, delta_time: float, context):
        result = subprocess.run(
            self.spec["command"],
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        mode = self.spec.get("mode", "stdout")
        if mode == "json":
            return json.loads(result.stdout)
        if mode == "lines":
            return result.stdout.splitlines()
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.rstrip("\n"),
            "stderr": result.stderr.rstrip("\n"),
        }


class HttpJsonProvider(Provider):
    spec_schema = {"url": str, "timeout": float}
    required_spec_keys = {"url"}

    def provide(self, delta_time: float, context):
        with urllib.request.urlopen(self.spec["url"], timeout=float(self.spec.get("timeout", 5.0))) as response:
            return json.loads(response.read().decode("utf-8"))


class TransformProvider(Provider):
    spec_schema = {
        "items": list,
        "mapping": dict,
        "template": str,
        "source": str,
        "default": object,
        "formatter": str,
        "operations": list,
    }

    def provide(self, delta_time: float, context):
        if "items" in self.spec:
            return resolve_items(self.spec.get("items", []), context.data)
        if "mapping" in self.spec and "template" in self.spec:
            return render_template(self.spec.get("template", ""), self.spec.get("mapping", {}), context.data)
        if "mapping" in self.spec:
            return resolve_mapping(self.spec.get("mapping", {}), context.data)
        return resolve_value_spec(
            {
                "source": self.spec.get("source"),
                "default": self.spec.get("default"),
                "formatter": self.spec.get("formatter"),
                "template": self.spec.get("template"),
                "operations": self.spec.get("operations", []),
            },
            context.data,
        )


class TemplateProvider(Provider):
    spec_schema = {"template": str, "mapping": dict}
    required_spec_keys = {"template"}

    def provide(self, delta_time: float, context):
        return render_template(self.spec.get("template", ""), self.spec.get("mapping", {}), context.data)


class ComposeProvider(Provider):
    spec_schema = {"mapping": dict}
    required_spec_keys = {"mapping"}

    def provide(self, delta_time: float, context):
        return resolve_mapping(self.spec.get("mapping", {}), context.data)


class RecordsProvider(Provider):
    spec_schema = {"items": list}
    required_spec_keys = {"items"}

    def provide(self, delta_time: float, context):
        return resolve_items(self.spec.get("items", []), context.data)


class RollingWindowProvider(Provider):
    spec_schema = {"source": str, "default": object, "size": int}
    required_spec_keys = {"source"}

    def setup(self, context):
        self.values: list = []

    def provide(self, delta_time: float, context):
        source = resolve_value_spec(
            {"source": self.spec.get("source"), "default": self.spec.get("default")},
            context.data,
        )
        self.values.append(source)
        self.values = self.values[-int(self.spec.get("size", 32)) :]
        return list(self.values)


class ThresholdProvider(Provider):
    spec_schema = {
        "source": str,
        "default": object,
        "value": float,
        "operator": str,
        "true": object,
        "false": object,
    }
    required_spec_keys = {"source"}

    def provide(self, delta_time: float, context):
        value = resolve_value_spec(
            {"source": self.spec.get("source"), "default": self.spec.get("default")},
            context.data,
        )
        compare = float(self.spec.get("value", 0))
        try:
            actual = float(value)
        except (TypeError, ValueError):
            actual = 0.0
        operator = self.spec.get("operator", "gt")
        if operator == "gte":
            matched = actual >= compare
        elif operator == "lt":
            matched = actual < compare
        elif operator == "lte":
            matched = actual <= compare
        elif operator == "eq":
            matched = actual == compare
        elif operator == "ne":
            matched = actual != compare
        else:
            matched = actual > compare
        true_value = self.spec.get("true", self.spec.get(True))
        false_value = self.spec.get("false", self.spec.get(False))
        return true_value if matched else false_value


class NormalizeStateProvider(Provider):
    spec_schema = {
        "source": str,
        "default": object,
        "state_key": str,
        "severity_key": str,
        "state_map": dict,
        "severity_map": dict,
        "severity_by_state": dict,
        "default_state": str,
        "default_severity": str,
    }
    required_spec_keys = {"source"}

    def provide(self, delta_time: float, context):
        source = resolve_value_spec(
            {"source": self.spec.get("source"), "default": self.spec.get("default", [])},
            context.data,
        )
        state_key = self.spec.get("state_key", "state")
        severity_key = self.spec.get("severity_key", "severity")
        state_map = dict(self.spec.get("state_map", {}) or {})
        severity_map = dict(self.spec.get("severity_map", {}) or {})
        severity_by_state = dict(self.spec.get("severity_by_state", {}) or {})
        default_state = self.spec.get("default_state", "unknown")
        default_severity = self.spec.get("default_severity", "info")
        if isinstance(source, list):
            return [
                self._normalize_item(
                    item,
                    state_key=state_key,
                    severity_key=severity_key,
                    state_map=state_map,
                    severity_map=severity_map,
                    severity_by_state=severity_by_state,
                    default_state=default_state,
                    default_severity=default_severity,
                )
                for item in source
            ]
        if isinstance(source, dict):
            return self._normalize_item(
                source,
                state_key=state_key,
                severity_key=severity_key,
                state_map=state_map,
                severity_map=severity_map,
                severity_by_state=severity_by_state,
                default_state=default_state,
                default_severity=default_severity,
            )
        return source

    def _normalize_item(
        self,
        item,
        *,
        state_key: str,
        severity_key: str,
        state_map: dict,
        severity_map: dict,
        severity_by_state: dict,
        default_state: str,
        default_severity: str,
    ):
        if not isinstance(item, dict):
            return item
        normalized = dict(item)
        raw_state = str(item.get(state_key, default_state)).lower()
        raw_severity = str(item.get(severity_key, "")).lower()
        state = state_map.get(raw_state, raw_state or default_state)
        severity = severity_map.get(raw_severity, raw_severity) if raw_severity else severity_by_state.get(state, default_severity)
        if not severity:
            severity = severity_by_state.get(state, default_severity)
        normalized[state_key] = state
        normalized[severity_key] = severity
        return normalized


class BucketProvider(Provider):
    spec_schema = {
        "source": str,
        "default": object,
        "value_key": str,
        "bucket_count": int,
        "min": float,
        "max": float,
        "precision": int,
    }
    required_spec_keys = {"source"}

    def provide(self, delta_time: float, context):
        source = resolve_value_spec(
            {"source": self.spec.get("source"), "default": self.spec.get("default", [])},
            context.data,
        )
        values = self._values(source)
        if not values:
            return []
        bucket_count = max(int(self.spec.get("bucket_count", 8)), 1)
        minimum = float(self.spec.get("min", min(values)))
        maximum = float(self.spec.get("max", max(values)))
        if maximum <= minimum:
            maximum = minimum + 1.0
        width = (maximum - minimum) / bucket_count
        counts = [0 for _ in range(bucket_count)]
        for value in values:
            if value <= minimum:
                index = 0
            elif value >= maximum:
                index = bucket_count - 1
            else:
                index = min(bucket_count - 1, int((value - minimum) / width))
            counts[index] += 1
        result = []
        precision = int(self.spec.get("precision", 2))
        for index, count in enumerate(counts):
            start = minimum + index * width
            end = start + width
            result.append(
                {
                    "label": f"{start:.{precision}f}-{end:.{precision}f}",
                    "count": count,
                    "value": count,
                    "start": round(start, precision),
                    "end": round(end, precision),
                    "display": str(count),
                }
            )
        return result

    def _values(self, source) -> list[float]:
        if isinstance(source, list):
            result = []
            value_path = self.spec.get("value_key")
            for item in source:
                if isinstance(item, dict) and value_path:
                    try:
                        result.append(float(item.get(value_path, 0.0)))
                    except (TypeError, ValueError):
                        continue
                else:
                    try:
                        result.append(float(item))
                    except (TypeError, ValueError):
                        continue
            return result
        try:
            return [float(source)]
        except (TypeError, ValueError):
            return []

class EventStreamProvider(Provider):
    spec_schema = {"item": dict, "source": str, "default": object, "max_items": int}

    def setup(self, context):
        self.events: list[dict] = []

    def provide(self, delta_time: float, context):
        payload = self.spec.get("item")
        if payload is not None:
            value = resolve_mapping(payload, context.data, string_mode="literal_fallback")
            items = [value]
        else:
            source = resolve_value_spec(
                {"source": self.spec.get("source"), "default": self.spec.get("default")},
                context.data,
            )
            if isinstance(source, list):
                items = [item for item in source if isinstance(item, dict)]
            elif isinstance(source, dict):
                items = [source]
            else:
                items = []

        for item in items:
            event = dict(item)
            event.setdefault("timestamp", time.strftime("%H:%M:%S", time.localtime()))
            self.events.append(event)
        self.events = self.events[-int(self.spec.get("max_items", 80)) :]
        return list(self.events)


class GridHistoryProvider(Provider):
    spec_schema = {"source": str, "default": object, "size": int}
    required_spec_keys = {"source"}

    def setup(self, context):
        self.rows: list[list[float]] = []

    def provide(self, delta_time: float, context):
        row = resolve_value_spec(
            {"source": self.spec.get("source"), "default": self.spec.get("default", [])},
            context.data,
        )
        if isinstance(row, dict):
            values = list(row.values())
        elif isinstance(row, list):
            values = row
        else:
            values = [row]
        self.rows.append(list(values))
        self.rows = self.rows[-int(self.spec.get("size", 16)) :]
        return list(self.rows)
