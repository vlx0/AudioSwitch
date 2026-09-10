"""AudioSwitch GUI."""

from __future__ import annotations

import ctypes
import tkinter as tk

from . import __version__
from .audio import list_playback, set_default, toggle_next
from .instance import WINDOW_TITLE
from .tray import TrayIcon

BG = "#111111"
FG = "#ffffff"
MUTED = "#999999"
CARD = "#1a1a1a"
OK = "#86efac"
WARN = "#f87171"
ACCENT = "#fbbf24"


class AudioSwitchApp(tk.Tk):
    def __init__(self, start_hidden: bool = False) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry("480x380")
        self.minsize(400, 320)
        self.configure(bg=BG)
        self._exiting = False
        self._tray: TrayIcon | None = None
        self._devices = []

        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(pad, text="AudioSwitch", bg=BG, fg=FG, font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(
            pad,
            text="Наушники ↔ колонки одной кнопкой",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 14))

        self._current = tk.Label(pad, text="…", bg=BG, fg=OK, font=("Segoe UI Semibold", 12), anchor="w")
        self._current.pack(fill="x", pady=(0, 10))

        btn = tk.Label(
            pad,
            text="Переключить",
            bg=ACCENT,
            fg=BG,
            font=("Segoe UI", 10),
            padx=16,
            pady=9,
            cursor="hand2",
        )
        btn.pack(anchor="w")
        btn.bind("<Button-1>", lambda _e: self.toggle())

        frame = tk.Frame(pad, bg="#2a2a2a", padx=1, pady=1)
        frame.pack(fill="both", expand=True, pady=(14, 0))
        inner = tk.Frame(frame, bg=CARD)
        inner.pack(fill="both", expand=True)
        self._list = tk.Listbox(
            inner,
            bg=CARD,
            fg=FG,
            selectbackground="#333333",
            selectforeground=FG,
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 10),
            activestyle="none",
        )
        self._list.pack(fill="both", expand=True, padx=4, pady=4)
        self._list.bind("<Double-Button-1>", self._on_dbl)

        self._status = tk.Label(pad, text=f"v{__version__}", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self._status.pack(fill="x", pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.reload()
        self.after(20, self._place)
        self.after(200, self._start_tray)
        if start_hidden:
            self.after(300, self.hide_to_tray)

    def _place(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width() or 480, self.winfo_height() or 380
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 3}")

    def _start_tray(self) -> None:
        try:
            self._tray = TrayIcon(self, self.show_window, self.toggle, self.quit_app)
            self._tray.start()
        except Exception as e:
            self._status.configure(text=f"трей: {e}", fg=WARN)

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.reload()

    def hide_to_tray(self) -> None:
        self.withdraw()

    def quit_app(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()

    def reload(self) -> None:
        self._devices = list_playback()
        self._list.delete(0, tk.END)
        cur = "нет устройств"
        for d in self._devices:
            mark = " ★" if d.is_default else ""
            self._list.insert(tk.END, f"  {d.name}{mark}")
            if d.is_default:
                cur = d.name
        self._current.configure(text=f"Сейчас: {cur}")

    def toggle(self) -> None:
        name, _ = toggle_next()
        self.reload()
        if name:
            self._status.configure(text=f"→ {name}", fg=OK)
            if self._tray:
                self._tray.notify(name)
        else:
            self._status.configure(text="нужно ≥2 устройства вывода", fg=WARN)

    def _on_dbl(self, _e=None) -> None:
        sel = self._list.curselection()
        if not sel or not self._devices:
            return
        d = self._devices[sel[0]]
        if set_default(d.id):
            self.reload()
            self._status.configure(text=f"→ {d.name}", fg=OK)
            if self._tray:
                self._tray.notify(d.name)
        else:
            self._status.configure(text="не удалось переключить", fg=WARN)


def run(start_hidden: bool = False) -> None:
    AudioSwitchApp(start_hidden=start_hidden).mainloop()
