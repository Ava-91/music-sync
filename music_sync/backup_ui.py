from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .backups import BackupInfo, list_backups, restore_backup


def _format_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


class BackupManagerDialog(tk.Toplevel):
    """Browse and safely restore music-sync backups."""

    def __init__(self, parent: tk.Misc, target: Path, backup_root: Path) -> None:
        super().__init__(parent)
        self.title("Backup Manager")
        self.geometry("760x480")
        self.transient(parent)
        self.grab_set()
        self.target = target
        self.backup_root = backup_root
        self.backups: list[BackupInfo] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="💾 Backup Manager", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(root, text=f"Backups: {self.backup_root}", wraplength=700).pack(anchor="w", pady=(4, 12))
        columns = ("created", "files", "size", "path")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        for column, title, width in (("created", "Created", 150), ("files", "Files", 70), ("size", "Size", 90), ("path", "Location", 380)):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text="↻ Refresh", command=self.refresh).pack(side="left")
        ttk.Button(actions, text="↩ Restore Selected", command=self.restore).pack(side="right")
        ttk.Button(actions, text="Close", command=self.destroy).pack(side="right", padx=8)

    def refresh(self) -> None:
        self.backups = list_backups(self.backup_root)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for backup in self.backups:
            self.tree.insert("", "end", values=(backup.created_at.strftime("%Y-%m-%d %H:%M:%S"), backup.file_count, _format_size(backup.size_bytes), str(backup.path)))

    def restore(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a backup", "Choose a backup to restore first.", parent=self)
            return
        index = self.tree.index(selection[0])
        backup = self.backups[index]
        if not messagebox.askyesno(
            "Restore backup?",
            f"Restore this backup?\n\n{backup.path}\n\nThe current library will be backed up before restoration.",
            parent=self,
        ):
            return
        try:
            protection = restore_backup(backup.path, self.target, self.backup_root)
        except Exception as exc:
            messagebox.showerror("Restore failed", str(exc), parent=self)
            return
        messagebox.showinfo("Restore complete", f"Backup restored.\n\nYour previous library was protected at:\n{protection}", parent=self)
        self.refresh()


def open_backup_manager(parent: tk.Misc, target: Path) -> None:
    BackupManagerDialog(parent, target, target.parent / "music-sync-backups")
