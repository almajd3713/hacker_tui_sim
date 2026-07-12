"""Hatui package."""

__all__ = ["HatuiApp"]


def __getattr__(name: str):
    if name == "HatuiApp":
        from hatui.app import HatuiApp

        return HatuiApp
    raise AttributeError(name)
