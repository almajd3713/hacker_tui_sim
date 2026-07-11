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
from hatui.runtime.bindings import resolve_path
from hatui.runtime.formatters import apply_formatter, apply_template


class ConstantProvider(Provider):
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
    def provide(self, delta_time: float, context):
        key = self.spec.get("key")
        keys = self.spec.get("keys")
        if key is not None:
            return os.environ.get(key, self.spec.get("default"))
        if keys is not None:
            return {item: os.environ.get(item) for item in keys}
        return dict(os.environ)


class FileProvider(Provider):
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
    def provide(self, delta_time: float, context):
        with urllib.request.urlopen(self.spec["url"], timeout=float(self.spec.get("timeout", 5.0))) as response:
            return json.loads(response.read().decode("utf-8"))


class TransformProvider(Provider):
    def provide(self, delta_time: float, context):
        source = resolve_path(context.data, self.spec.get("source"))
        if source is None:
            source = self.spec.get("default")
        value = apply_formatter(source, self.spec.get("formatter"))
        return apply_template(value, self.spec.get("template"))


class TemplateProvider(Provider):
    def provide(self, delta_time: float, context):
        values = {}
        for key, source in self.spec.get("mapping", {}).items():
            if isinstance(source, dict):
                value = resolve_path(context.data, source.get("path"), source.get("default"))
                value = apply_formatter(value, source.get("formatter"))
                value = apply_template(value, source.get("template"))
            else:
                value = resolve_path(context.data, source)
            values[key] = value
        return self.spec.get("template", "").format(**values)


class ComposeProvider(Provider):
    def provide(self, delta_time: float, context):
        mapping = self.spec.get("mapping", {})
        composed = {}
        for key, source in mapping.items():
            if isinstance(source, dict):
                value = resolve_path(context.data, source.get("path"), source.get("default"))
                value = apply_formatter(value, source.get("formatter"))
                value = apply_template(value, source.get("template"))
            else:
                value = resolve_path(context.data, source)
            composed[key] = value
        return composed


class RecordsProvider(Provider):
    def provide(self, delta_time: float, context):
        records = []
        for item in self.spec.get("items", []):
            record = {}
            for key, source in item.items():
                if isinstance(source, dict):
                    value = resolve_path(context.data, source.get("path"), source.get("default"))
                    value = apply_formatter(value, source.get("formatter"))
                    value = apply_template(value, source.get("template"))
                else:
                    value = source
                record[key] = value
            records.append(record)
        return records


class RollingWindowProvider(Provider):
    def setup(self, context):
        self.values: list = []

    def provide(self, delta_time: float, context):
        source = resolve_path(context.data, self.spec.get("source"))
        self.values.append(source)
        self.values = self.values[-int(self.spec.get("size", 32)) :]
        return list(self.values)


class ThresholdProvider(Provider):
    def provide(self, delta_time: float, context):
        value = resolve_path(context.data, self.spec.get("source"), self.spec.get("default"))
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
        return self.spec.get("true") if matched else self.spec.get("false")
