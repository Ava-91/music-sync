from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .models import Match


class FuzzyReviewDialog(tk.Toplevel):
    """Ask the user to confirm or reject every uncertain track match."""

    def __init__(self, parent: tk.Misc, matches: list[Match]) -> None:
        super().__init__(parent)
        self.title("Review fuzzy matches")
        self.geometry("820x560")
        self.transient(parent)
        self.grab_set()
        self.matches = matches
        self.index = 0
        self.decisions: dict[str, bool] = {}
        self.result: dict[str, bool] | None = None
        self._build()
        self._show_current()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        self.counter = ttk.Label(root, font=("Segoe UI", 12, "bold"))
        self.counter.pack(anchor="w")
        ttk.Label(root, text="These matches are suggestions, not automatic decisions.").pack(anchor="w", pady=(4, 18))

        columns = ttk.Frame(root)
        columns.pack(fill="both", expand=True)
        self.laptop = self._panel(columns, "💻 Laptop candidate")
        self.laptop.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.phone = self._panel(columns, "📱 Phone candidate")
        self.phone.pack(side="left", fill="both", expand=True, padx=(8, 0))

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=18)
        ttk.Button(actions, text="← Previous", command=self.previous).pack(side="left")
        ttk.Button(actions, text="✓ Same Song", command=lambda: self.choose(True)).pack(side="left", padx=8)
        ttk.Button(actions, text="✕ Different Songs", command=lambda: self.choose(False)).pack(side="left")
        ttk.Button(actions, text="Finish Review", command=self.finish).pack(side="right")
        ttk.Button(actions, text="Cancel", command=self.cancel).pack(side="right", padx=8)

    def _panel(self, parent: ttk.Frame, title: str) -> ttk.Frame:
        return ttk.LabelFrame(parent, text=title, padding=14)

    def _populate(self, panel: ttk.Frame, track) -> None:
        for child in panel.winfo_children():
            child.destroy()
        ttk.Label(panel, text=track.display_title, font=("Segoe UI", 14, "bold"), wraplength=330).pack(anchor="w")
        ttk.Label(panel, text=f"Artist: {track.display_artist}").pack(anchor="w", pady=(12, 0))
        ttk.Label(panel, text=f"Album: {track.display_album}").pack(anchor="w")
        duration = f"{track.duration:.1f}s" if track.duration is not None else "Unknown"
        ttk.Label(panel, text=f"Duration: {duration}").pack(anchor="w")
        ttk.Label(panel, text=f"Filename: {track.path.name}", wraplength=330).pack(anchor="w", pady=(0, 12))

    def _show_current(self) -> None:
        if not self.matches:
            self.finish()
            return
        match = self.matches[self.index]
        self.counter.configure(text=f"Fuzzy match {self.index + 1} of {len(self.matches)} — confidence {match.confidence:.0%}")
        self._populate(self.laptop, match.laptop)
        self._populate(self.phone, match.phone)

    def choose(self, same: bool) -> None:
        match = self.matches[self.index]
        self.decisions[str(match.laptop.path)] = same
        if self.index < len(self.matches) - 1:
            self.index += 1
            self._show_current()
        else:
            self.finish()

    def previous(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._show_current()

    def finish(self) -> None:
        self.result = dict(self.decisions)
        self.destroy()

    def cancel(self) -> None:
        self.result = None
        self.destroy()


def review_fuzzy_matches(parent: tk.Misc, matches: list[Match]) -> dict[str, bool] | None:
    dialog = FuzzyReviewDialog(parent, matches)
    parent.wait_window(dialog)
    return dialog.result
