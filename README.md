# Hatui

Hatui is a configurable hacker-style terminal UI toolkit for Python. It lets you compose full-screen TUIs from YAML screens, reusable widgets, themes, routing, and data providers.

## Install

Recommended for end users:

```bash
pipx install hatui-kit
```

Python package install:

```bash
pip install hatui-kit
```

Installed CLI command:

```bash
hatui
```

Windows convenience build:

- Download `hatui-windows-amd64.zip` from GitHub Releases
- Unzip it
- Run `hatui.exe`

## Quick start

Run the bundled demo:

```bash
hatui
```

Validate the bundled demo spec:

```bash
hatui validate
```

Render a non-interactive preview:

```bash
hatui preview --width 100 --height 28 --frames 1
```

Run a custom spec:

```bash
hatui run path/to/screen.yaml
```

## What Hatui provides

- declarative YAML screen loading with includes
- widget and provider registries
- routing, modals, focus traversal, and debug overlays
- theme slots, color tokens, and font tokens
- reusable hacker-style widgets for dashboards and console simulations

## Example custom spec

```yaml
theme:
  preset: clean_ops

providers:
  - type: constant
    name: hello_text
    target: ui.hello
    value: Hello from Hatui

screen:
  type: box
  name: root_box
  title: demo
  padding: 1
  child:
    type: text
    name: hello_text
    text_key: ui.hello
```

Run it with:

```bash
hatui run ./demo.yaml
```

## Development

Editable install:

```bash
python -m pip install -e .
```

Smoke checks:

```bash
python -m compileall src
PYTHONPATH=src python -m hatui validate
PYTHONPATH=src python -m hatui preview --width 100 --height 28 --frames 1
```
