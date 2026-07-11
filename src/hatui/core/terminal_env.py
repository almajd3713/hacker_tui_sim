import sys
import os
import contextlib

class TerminalEnvironment:
    def __init__(self):
        self.original_stdin_attrs = None
        self.is_windows = os.name == 'nt'

    @contextlib.contextmanager
    def manage(self):
        """Context manager to setup and teardown the terminal environment."""
        self._setup()
        try:
            yield
        finally:
            self._teardown()

    def _setup(self):
        if not sys.stdout.isatty():
            raise RuntimeError("Standard output is not a TTY.")

        # 1. Enable ANSI on Windows
        if self.is_windows:
            self._enable_windows_ansi()

        # 2. Put terminal in raw mode (disable echo and line buffering)
        if not self.is_windows:
            import tty
            import termios
            fd = sys.stdin.fileno()
            self.original_stdin_attrs = termios.tcgetattr(fd)
            tty.setcbreak(fd=fd)
        else:
            import msvcrt
            # On Windows, msvcrt handles raw input implicitly for the most part, 
            # but we disable echo if necessary.
            pass 

        # 3. Switch to the alternate screen, clear it, and hide the cursor.
        sys.stdout.write("\033[?1049h\033[2J\033[H\033[?25l")
        sys.stdout.flush()

    def _teardown(self):
        # 1. Show the cursor and restore the main screen buffer.
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()

        # 2. Restore terminal to canonical mode
        if not self.is_windows and self.original_stdin_attrs is not None:
            import termios
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_stdin_attrs)

    def _enable_windows_ansi(self):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
