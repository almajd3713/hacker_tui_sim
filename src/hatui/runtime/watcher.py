from __future__ import annotations

import glob
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WatchSnapshot:
    enabled: bool
    interval_s: float
    debounce_s: float
    watched_files: list[str]
    pending_reload: bool
    pending_changed_files: list[str]
    reload_count: int
    last_reload_at: float | None
    last_reload_error: str | None


class SpecWatcher:
    def __init__(self, *, cli_watch: bool = False, allow_watch: bool = True):
        self.cli_watch = cli_watch
        self.allow_watch = allow_watch
        self.enabled = False
        self.interval = 0.35
        self.debounce = 0.2
        self.loaded_files: list[Path] = []
        self.extra_watch_files: list[Path] = []
        self._watched_mtimes: dict[Path, float] = {}
        self._last_watch_check = 0.0
        self._pending_reload_since: float | None = None
        self._pending_changed_files: list[str] = []
        self._reload_count = 0
        self._last_reload_at: float | None = None
        self._last_reload_error: str | None = None

    def configure(self, *, spec_path: Path, loaded_files: list[Path], dev_spec: dict) -> None:
        watch_spec = dict(dev_spec.get("watch", {}) or {})
        enabled = bool(watch_spec.get("enabled", False)) or self.cli_watch
        self.enabled = bool(enabled and self.allow_watch)
        self.interval = max(float(watch_spec.get("interval", 0.35)), 0.05)
        self.debounce = max(float(watch_spec.get("debounce", 0.2)), 0.0)
        self.loaded_files = list(loaded_files)
        self.extra_watch_files = self._resolve_watch_paths(spec_path, watch_spec.get("paths", []))
        self._refresh_watched_files()

    def should_reload(self, now: float | None = None) -> bool:
        if not self.enabled:
            return False
        now = time.monotonic() if now is None else now
        if now - self._last_watch_check < self.interval:
            return False
        self._last_watch_check = now
        changed_files = self._changed_watched_files()
        if not changed_files:
            self._pending_reload_since = None
            self._pending_changed_files = []
            return False
        self._pending_changed_files = [str(path) for path in changed_files]
        if self._pending_reload_since is None:
            self._pending_reload_since = now
            return False
        return now - self._pending_reload_since >= self.debounce

    def mark_reload_success(self, at_elapsed: float | None) -> None:
        self._reload_count += 1
        self._last_reload_at = at_elapsed
        self._last_reload_error = None
        self._pending_reload_since = None
        self._pending_changed_files = []

    def mark_reload_error(self, message: str) -> None:
        self._last_reload_error = message
        self._pending_reload_since = None
        self._pending_changed_files = []

    def capture_state(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "interval": self.interval,
            "debounce": self.debounce,
            "loaded_files": list(self.loaded_files),
            "extra_watch_files": list(self.extra_watch_files),
            "watched_mtimes": dict(self._watched_mtimes),
            "last_watch_check": self._last_watch_check,
            "pending_reload_since": self._pending_reload_since,
            "pending_changed_files": list(self._pending_changed_files),
            "reload_count": self._reload_count,
            "last_reload_at": self._last_reload_at,
            "last_reload_error": self._last_reload_error,
        }

    def restore_state(self, state: dict[str, object]) -> None:
        self.enabled = bool(state["enabled"])
        self.interval = float(state["interval"])
        self.debounce = float(state["debounce"])
        self.loaded_files = list(state["loaded_files"])
        self.extra_watch_files = list(state["extra_watch_files"])
        self._watched_mtimes = dict(state["watched_mtimes"])
        self._last_watch_check = float(state["last_watch_check"])
        self._pending_reload_since = state["pending_reload_since"]
        self._pending_changed_files = list(state["pending_changed_files"])
        self._reload_count = int(state["reload_count"])
        self._last_reload_at = state["last_reload_at"]
        self._last_reload_error = state["last_reload_error"]

    def snapshot(self) -> WatchSnapshot:
        return WatchSnapshot(
            enabled=self.enabled,
            interval_s=self.interval,
            debounce_s=self.debounce,
            watched_files=[str(path) for path in self._collect_watched_files()],
            pending_reload=self._pending_reload_since is not None,
            pending_changed_files=list(self._pending_changed_files),
            reload_count=self._reload_count,
            last_reload_at=self._last_reload_at,
            last_reload_error=self._last_reload_error,
        )

    def _resolve_watch_paths(self, spec_path: Path, patterns: list[str]) -> list[Path]:
        resolved: list[Path] = []
        base_dir = spec_path.resolve().parent
        for pattern in patterns:
            absolute_pattern = str((base_dir / pattern).resolve()) if not Path(pattern).is_absolute() else pattern
            matches = [Path(item).resolve() for item in glob.glob(absolute_pattern, recursive=True)]
            if matches:
                resolved.extend(matches)
            else:
                resolved.append(Path(absolute_pattern).resolve())
        unique: list[Path] = []
        seen: set[Path] = set()
        for path in resolved:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    def _collect_watched_files(self) -> list[Path]:
        combined = list(self.loaded_files) + list(self.extra_watch_files)
        unique: list[Path] = []
        seen: set[Path] = set()
        for path in combined:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    def _refresh_watched_files(self) -> None:
        self._watched_mtimes = {}
        for path in self._collect_watched_files():
            try:
                self._watched_mtimes[path] = path.stat().st_mtime
            except FileNotFoundError:
                self._watched_mtimes[path] = 0.0

    def _changed_watched_files(self) -> list[Path]:
        changed: list[Path] = []
        for path, recorded_mtime in self._watched_mtimes.items():
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                current_mtime = 0.0
            if current_mtime != recorded_mtime:
                changed.append(path)
        return changed
