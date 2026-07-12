from __future__ import annotations

import contextlib
import os
import sys


class TerminalEnvironment:
    def __init__(self):
        self.original_stdin_attrs = None
        self.is_windows = os.name == "nt"
        self._active = False

    @contextlib.contextmanager
    def manage(self):
        self._setup()
        try:
            yield
        finally:
            self._teardown()

    def _setup(self):
        if self._active:
            return
        if not sys.stdout.isatty():
            raise RuntimeError("Standard output is not a TTY.")
        if not sys.stdin.isatty():
            raise RuntimeError("Standard input is not a TTY.")

        if self.is_windows:
            self._enable_windows_ansi()
        else:
            self._enable_posix_raw_mode()

        sys.stdout.write("\033[?1049h\033[2J\033[H\033[?25l")
        sys.stdout.flush()
        self._active = True

    def _teardown(self):
        if not self._active:
            return
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()

        if not self.is_windows and self.original_stdin_attrs is not None:
            import termios

            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_stdin_attrs)
            self.original_stdin_attrs = None
        self._active = False

    def _enable_posix_raw_mode(self):
        import termios
        import tty

        fd = sys.stdin.fileno()
        self.original_stdin_attrs = termios.tcgetattr(fd)
        tty.setraw(fd)

    def _enable_windows_ansi(self):
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
