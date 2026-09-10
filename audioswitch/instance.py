"""Single instance."""

from __future__ import annotations

import ctypes
import sys

from . import __version__

_MUTEX = None
MUTEX_NAME = "Global\\AudioSwitch_Mutex_vlx0"
WINDOW_TITLE = "AudioSwitch — darkshade"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def claim_or_exit() -> None:
    global _MUTEX
    kernel32.SetLastError(0)
    _MUTEX = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if kernel32.GetLastError() == 183:
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if hwnd:
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
        else:
            user32.MessageBoxW(0, "AudioSwitch уже запущен.", f"AudioSwitch {__version__}", 0x40)
        sys.exit(0)
