from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from music_sync.matcher import build_plan
from music_sync.scanner import scan_library

DEFAULT_LAPTOP = r"E:\Ava files\ava music"


class MusicSyncApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("🎵 Ava Music Sync")
        self.geometry("760x560")
        self.minsize(680, 480)

        self.laptop_var = tk.StringVar(value=DEFAULT_LAPTOP)
        self.phone_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Choose the phone Music folder, then scan.")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="🎵 Ava Music Sync", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Scan first. Nothing is modified by the scan.",
        ).pack(anchor="w", pady=(2, 18))

        self._path_row(frame, "💻 Laptop", self.laptop_var, allow_browse=True)
        self._path_row(frame, "📱 Phone", self.phone_var, allow_browse=True)

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=18)
        ttk.Button(actions, text="🔍 Scan & Preview", command=self.scan).pack(side="left")

        self.tree = ttk.Treeview(frame, columns=("count", "details"), show="headings", height=14)
        self.tree.heading("count", text="Category")
        self.tree.heading("details", text="Count / details")
        self.tree.column("count", width=230, anchor="w")
        self.tree.column("details", width=450, anchor="w")
        self.tree.pack(fill="both", expand=True)

        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(12, 0))

    def _path_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, allow_browse: bool) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, width=12).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=8)
        if allow_browse:
            ttk.Button(row, text="Browse", command=lambda: self.browse(variable)).pack(side="left")

    def browse(self, variable: tk.StringVar) -> None:
        path = filedialog.askdirectory(title="Select music folder")
        if path:
            variable.set(path)

    def scan(self) -> None:
        laptop_path = Path(self.laptop_var.get().strip())
        phone_path = Path(self.phone_var.get().strip())
        if not laptop_path:
            messagebox.showerror("Missing path", "Choose the laptop music folder.")
            return
        if not phone_path:
            messagebox.showwarning(
                "Phone folder needed",
                "Windows MTP phone storage may not appear as a normal filesystem path. "
                "For now, select a locally accessible folder or mapped phone storage.",
            )
            return

        self.status_var.set("Scanning…")
        self.update_idletasks()
        laptop = scan_library(laptop_path, "laptop")
        phone = scan_library(phone_path, "phone")
        plan = build_plan(laptop, phone)

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert("", "end", values=("💻 Laptop-only", len(plan.laptop_only)))
        self.tree.insert("", "end", values=("📱 Phone-only", len(plan.phone_only)))
        self.tree.insert("", "end", values=("🟡 Matched tracks", len(plan.matches)))
        self.tree.insert(
            "", "end", values=(
                "⚠️ Metadata conflicts",
                sum(match.metadata_conflict for match in plan.matches),
            )
        )
        self.tree.insert(
            "", "end", values=("❗ Scan errors", len(laptop.errors) + len(phone.errors))
        )

        self.status_var.set(
            f"Scan complete — {len(laptop.tracks)} laptop tracks, "
            f"{len(phone.tracks)} phone tracks. No files were changed."
        )


if __name__ == "__main__":
    MusicSyncApp().mainloop()
