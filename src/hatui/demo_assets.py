from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Iterator


_BUNDLED_DEMO_SPEC = files("hatui.demo").joinpath("screens/dashboard.yaml")


@contextmanager
def bundled_demo_spec_path() -> Iterator[Path]:
    """Yield a filesystem path to the bundled demo spec."""
    with as_file(_BUNDLED_DEMO_SPEC) as spec_path:
        yield spec_path
