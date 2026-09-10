"""Tray."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .ui import AudioSwitchApp


def make_tray_image():
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((6, 6, size - 6, size - 6), radius=12, fill=(251, 191, 36, 255))
    draw.ellipse((20, 22, 36, 38), outline=(17, 17, 17, 255), width=3)
    draw.polygon([(36, 24), (48, 16), (48, 44), (36, 36)], fill=(17, 17, 17, 255))
    return img


class TrayIcon:
    def __init__(self, app: AudioSwitchApp, on_show, on_toggle, on_quit) -> None:
        self._app = app
        self._on_show = on_show
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._icon = None
        self._thread = None
        self._ready = threading.Event()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self) -> None:
        import pystray
        from pystray import MenuItem as item

        menu = pystray.Menu(
            item("Открыть", lambda *_: self._app.after(0, self._on_show)),
            item("Переключить", lambda *_: self._app.after(0, self._on_toggle)),
            pystray.Menu.SEPARATOR,
            item("Выход", lambda *_: self._app.after(0, self._on_quit)),
        )
        self._icon = pystray.Icon("AudioSwitch", make_tray_image(), "AudioSwitch", menu)
        self._ready.set()
        self._icon.run()

    def notify(self, text: str) -> None:
        if self._icon:
            try:
                self._icon.notify(text, "AudioSwitch")
            except Exception:
                pass

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
