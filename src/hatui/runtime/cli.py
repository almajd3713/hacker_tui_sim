from __future__ import annotations

import argparse
import sys
from contextlib import nullcontext
from pathlib import Path

from hatui.demo_assets import bundled_demo_spec_path
from hatui.runtime.render_policy import RenderPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hatui")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("spec", nargs="?", help="path to YAML spec")
    run_parser.add_argument("--watch", action="store_true", help="reload spec when watched files change")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("spec", nargs="?", help="path to YAML spec")

    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("spec", nargs="?", help="path to YAML spec")
    preview_parser.add_argument("--route")
    preview_parser.add_argument("--width", type=int, default=100)
    preview_parser.add_argument("--height", type=int, default=32)
    preview_parser.add_argument("--frames", type=int, default=1)
    return parser


def normalize_argv(argv: list[str] | None = None) -> list[str]:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in {"run", "validate", "preview"}:
        return ["run", *argv]
    return argv


def resolve_spec_context(spec_arg: str | None):
    if spec_arg:
        return nullcontext(Path(spec_arg)), False
    return bundled_demo_spec_path(), True


def preferred_glyph_mode(stream=None) -> str:
    stream = sys.stdout if stream is None else stream
    encoding = getattr(stream, "encoding", None) or "utf-8"
    sample = "┌█▁░▸●╱"
    try:
        sample.encode(encoding)
    except UnicodeEncodeError:
        return "ascii"
    return "unicode"


def write_cli_text(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        fallback = RenderPolicy("ascii").translate(text)
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(fallback.encode(encoding, errors="replace"))
        else:
            sys.stdout.write(fallback)
    sys.stdout.flush()
