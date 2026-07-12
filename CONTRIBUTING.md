# Contributing to Hatui

Hatui is a Python TUI toolkit driven by declarative YAML screens, reusable widgets, and providers.

## Development setup

1. Create a virtual environment.
2. Install the project in editable mode:

```bash
python -m pip install -e .
```

3. Run the bundled demo:

```bash
python -m hatui
```

## Local validation

Use lightweight smoke checks before opening a PR:

```bash
python -m compileall src
PYTHONPATH=src python -m hatui validate
PYTHONPATH=src python -m hatui preview --width 100 --height 28 --frames 1
```

## Release process

- Version is sourced from `pyproject.toml`.
- Create a release tag in the form `vX.Y.Z`.
- The release workflow builds:
  - Python wheel
  - source distribution
  - Windows executable zip
- PyPI publishing uses GitHub trusted publishing and must be configured on the PyPI project.

## Pull requests

- Keep features generic and declarative where possible.
- Avoid sample-only shortcuts in the runtime.
- Update user-facing docs when changing CLI behavior or packaging expectations.
