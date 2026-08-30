from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from music_sync.conflict_ui import review_conflicts
from music_sync.matcher import build_plan
from music_sync.models import SyncPlan
from music_sync.scanner import scan_library
from music_sync.review import ConflictChoice
from music_sync.sync import merge_with_conflicts

DEFAULT_LAPTOP = r"E:\Ava files\ava music"
DEFAULT_PHONE_COPY = r"E:\Ava files\phone music"


class MusicSyncApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("🎵 Ava Music Sync")
        self.geometry("980x700")
        self.minsize(860, 600)
        self.laptop_var = tk.StringVar(value=DEFAULT_LAPTOP)
        self.phone_var = tk.StringVar(value=DEFAULT_PHONE_COPY)
        self.status_var = tk.StringVar(value="Select your copied phone Music folder, then scan.")
        self.plan: SyncPlan | None = None
        self.laptop_root: Path | None = None
        self.phone_root: Path | None = None
        self.scan_button: ttk.Button | None = None
        self.review_button: ttk.Button | None = None
        self.merge_button: ttk.Button | None = None
        self.review_choices: dict[str, ConflictChoice] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="🎵 Ava Music Sync", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Compare two libraries, review conflicts, then merge safely.").pack(anchor="w", pady=(2, 18))
        self._path_row(frame, "💻 Laptop", self.laptop_var)
        self._path_row(frame, "📱 Phone copy", self.phone_var)

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=16)
        self.scan_button = ttk.Button(actions, text="🔍 Scan & Preview", command=self.scan)
        self.scan_button.pack(side="left")
        self.review_button = ttk.Button(actions, text="👀 Review Conflicts", command=self.review, state="disabled")
        self.review_button.pack(side="left", padx=8)
        self.merge_button = ttk.Button(actions, text="🔄 Merge Safely", command=self.merge, state="disabled")
        self.merge_button.pack(side="left")

        self.tree = ttk.Treeview(frame, columns=("category", "count", "details"), show="headings", height=18)
        self.tree.heading("category", text="Category")
        self.tree.heading("count", text="Count")
        self.tree.heading("details", text="Details")
        self.tree.column("category", width=250, anchor="w")
        self.tree.column("count", width=90, anchor="center")
        self.tree.column("details", width=560, anchor="w")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(12, 0))

    def _path_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, width=14).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text="Browse", command=lambda: self.browse(variable)).pack(side="left")

    def browse(self, variable: tk.StringVar) -> None:
        path = filedialog.askdirectory(title="Select music folder")
        if path:
            variable.set(path)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        if self.scan_button:
            self.scan_button.configure(state=state)
        has_plan = self.plan is not None
        if self.review_button:
            self.review_button.configure(state="normal" if (has_plan and not busy) else "disabled")
        if self.merge_button:
            self.merge_button.configure(state="normal" if (has_plan and not busy and self.plan and self.plan.phone_only) else "disabled")

    def scan(self) -> None:
        laptop_path = Path(self.laptop_var.get().strip()).expanduser()
        phone_path = Path(self.phone_var.get().strip()).expanduser()
        if not laptop_path.is_dir():
            messagebox.showerror("Laptop folder not found", f"Could not find:\n{laptop_path}")
            return
        if not phone_path.is_dir():
            messagebox.showerror("Phone copy not found", f"Select the copied phone Music folder.\n\nExpected example:\n{DEFAULT_PHONE_COPY}")
            return

        self._set_busy(True)
        self.status_var.set("Scanning both libraries…")

        def worker() -> None:
            laptop = scan_library(laptop_path, "laptop")
            phone = scan_library(phone_path, "phone")
            plan = build_plan(laptop, phone)
            self.after(0, lambda: self._show_scan(laptop_path, phone_path, laptop, phone, plan))

        threading.Thread(target=worker, daemon=True).start()

    def _show_scan(self, laptop_path, phone_path, laptop, phone, plan: SyncPlan) -> None:
        self.plan = plan
        self.laptop_root = laptop_path
        self.phone_root = phone_path
        self.review_choices = {}
        for item in self.tree.get_children():
            self.tree.delete(item)

        metadata_conflicts = sum(match.metadata_conflict for match in plan.matches)
        artwork_conflicts = sum(match.artwork_conflict for match in plan.matches)
        exact_matches = sum(1 for match in plan.matches if match.confidence >= 0.99)
        fuzzy_matches = len(plan.matches) - exact_matches
        rows = [
            ("💻 Laptop-only", len(plan.laptop_only), "Songs already on the laptop"),
            ("📱 Phone-only", len(plan.phone_only), "These will be copied into the laptop"),
            ("🟡 Matched", len(plan.matches), f"{exact_matches} exact, {fuzzy_matches} fuzzy matches"),
            ("⚠️ Metadata conflicts", metadata_conflicts, "Review before choosing a source"),
            ("🖼️ Artwork conflicts", artwork_conflicts, "Embedded artwork can be compared"),
            ("❗ Scan errors", len(laptop.errors) + len(phone.errors), "Unreadable files are never modified"),
        ]
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._set_busy(False)
        self.status_var.set(f"Scan complete — {len(laptop.tracks)} laptop tracks, {len(phone.tracks)} phone tracks. Nothing was changed.")

    def review(self) -> None:
        if not self.plan:
            return
        conflicts = [m for m in self.plan.matches if m.metadata_conflict or m.artwork_conflict]
        if not conflicts:
            messagebox.showinfo("No conflicts", "No metadata or artwork conflicts were found.")
            return
        choices = review_conflicts(self, conflicts)
        if choices is None:
            self.status_var.set("Conflict review cancelled. No files were changed.")
            return
        self.review_choices = choices
        self.status_var.set(f"Conflict review saved — {len(choices)} decision(s).")
        self.merge_button.configure(state="normal" if self.plan.phone_only or choices else "disabled")

    def merge(self) -> None:
        if not self.plan or not self.phone_root or not self.laptop_root:
            return
        count = len(self.plan.phone_only)
        conflict_count = sum(m.metadata_conflict or m.artwork_conflict for m in self.plan.matches)
        if conflict_count and not self.review_choices:
            answer = messagebox.askyesno("Review conflicts first?", f"There are {conflict_count} metadata/artwork conflict(s).\n\nReview them before merging?\n\nChoosing No keeps the laptop version for every conflict.")
            if answer:
                self.review()
                return

        answer = messagebox.askyesno(
            "Create backup and merge?",
            f"This will:\n\n• Back up the laptop library first\n• Copy {count} phone-only song(s)\n• Apply your reviewed conflict choices\n• Keep laptop versions by default\n\nContinue?",
        )
        if not answer:
            return

        self._set_busy(True)
        self.status_var.set("Creating backup and applying the merge plan…")
        backup_root = self.laptop_root.parent / "music-sync-backups"

        def worker() -> None:
            try:
                backup, copied, replaced, skipped = merge_with_conflicts(
                    self.plan, self.laptop_root, self.phone_root, backup_root, self.review_choices
                )
                self.after(0, lambda: self._merge_done(backup, copied, replaced, skipped))
            except Exception as exc:
                self.after(0, lambda: self._merge_failed(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _merge_done(self, backup: Path, copied, replaced, skipped) -> None:
        self._set_busy(False)
        self.status_var.set(f"Merge complete — added {len(copied)}, replaced {len(replaced)}, skipped {len(skipped)}.")
        messagebox.showinfo(
            "Merge complete 🎵",
            f"Added {len(copied)} song(s) to the laptop library.\n"
            f"Applied {len(replaced)} phone choice(s).\n"
            f"Skipped {len(skipped)} conflict(s).\n\n"
            f"Backup created at:\n{backup}\n\n"
            "You can now copy the finished laptop Music folder back to your A02s Music folder.",
        )
        self.scan()

    def _merge_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("Merge failed — no further changes were attempted.")
        messagebox.showerror("Merge failed", str(exc))


if __name__ == "__main__":
    MusicSyncApp().mainloop()
