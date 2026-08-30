from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from music_sync.conflict_ui import review_conflicts
from music_sync.dry_run import summarize
from music_sync.fuzzy_ui import apply_fuzzy_decisions, review_fuzzy_matches
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
        self.geometry("1080x740")
        self.minsize(900, 620)
        self.laptop_var = tk.StringVar(value=DEFAULT_LAPTOP)
        self.phone_var = tk.StringVar(value=DEFAULT_PHONE_COPY)
        self.status_var = tk.StringVar(value="Select your copied phone Music folder, then scan.")
        self.plan: SyncPlan | None = None
        self.laptop_root: Path | None = None
        self.phone_root: Path | None = None
        self.scan_button: ttk.Button | None = None
        self.review_conflicts_button: ttk.Button | None = None
        self.review_fuzzy_button: ttk.Button | None = None
        self.dry_run_button: ttk.Button | None = None
        self.merge_button: ttk.Button | None = None
        self.review_choices: dict[str, ConflictChoice] = {}
        self.fuzzy_decisions: dict[str, bool] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="🎵 Ava Music Sync", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Compare two libraries, review conflicts and uncertain matches, then merge safely.").pack(anchor="w", pady=(2, 18))
        self._path_row(frame, "💻 Library A", self.laptop_var)
        self._path_row(frame, "📁 Library B", self.phone_var)

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=16)
        self.scan_button = ttk.Button(actions, text="🔍 Scan & Preview", command=self.scan)
        self.scan_button.pack(side="left")
        self.review_conflicts_button = ttk.Button(actions, text="🖼️ Review Conflicts", command=self.review, state="disabled")
        self.review_conflicts_button.pack(side="left", padx=8)
        self.review_fuzzy_button = ttk.Button(actions, text="🧠 Review Fuzzy Matches", command=self.review_fuzzy, state="disabled")
        self.review_fuzzy_button.pack(side="left")
        self.dry_run_button = ttk.Button(actions, text="👁️ Dry Run", command=self.dry_run, state="disabled")
        self.dry_run_button.pack(side="left", padx=8)
        self.merge_button = ttk.Button(actions, text="🔄 Merge Safely", command=self.merge, state="disabled")
        self.merge_button.pack(side="left")

        self.tree = ttk.Treeview(frame, columns=("category", "count", "details"), show="headings", height=20)
        self.tree.heading("category", text="Category")
        self.tree.heading("count", text="Count")
        self.tree.heading("details", text="Details")
        self.tree.column("category", width=270, anchor="w")
        self.tree.column("count", width=90, anchor="center")
        self.tree.column("details", width=620, anchor="w")
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
        if self.review_conflicts_button:
            self.review_conflicts_button.configure(state="normal" if has_plan and not busy else "disabled")
        if self.review_fuzzy_button:
            fuzzy_exists = has_plan and any(not m.confirmed for m in self.plan.matches)
            self.review_fuzzy_button.configure(state="normal" if fuzzy_exists and not busy else "disabled")
        if self.dry_run_button:
            self.dry_run_button.configure(state="normal" if has_plan and not busy else "disabled")
        if self.merge_button:
            can_merge = has_plan and not busy and self.plan and (self.plan.phone_only or self.plan.matches)
            self.merge_button.configure(state="normal" if can_merge else "disabled")

    def scan(self) -> None:
        laptop_path = Path(self.laptop_var.get().strip()).expanduser()
        phone_path = Path(self.phone_var.get().strip()).expanduser()
        if not laptop_path.is_dir():
            messagebox.showerror("Library A not found", f"Could not find:\n{laptop_path}")
            return
        if not phone_path.is_dir():
            messagebox.showerror("Library B not found", f"Select the second music library.\n\nExpected example:\n{DEFAULT_PHONE_COPY}")
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
        self.fuzzy_decisions = {}
        for item in self.tree.get_children():
            self.tree.delete(item)
        metadata_conflicts = sum(match.metadata_conflict for match in plan.matches)
        artwork_conflicts = sum(match.artwork_conflict for match in plan.matches)
        exact_matches = sum(1 for match in plan.matches if match.confirmed)
        fuzzy_matches = len(plan.matches) - exact_matches
        rows = [
            ("💻 Library A-only", len(plan.laptop_only), "Already present in Library A"),
            ("📁 Library B-only", len(plan.phone_only), "Would be added to Library A"),
            ("🟡 Matched", len(plan.matches), f"{exact_matches} exact/trusted, {fuzzy_matches} fuzzy/unconfirmed"),
            ("⚠️ Metadata conflicts", metadata_conflicts, "Review before choosing a source"),
            ("🖼️ Artwork conflicts", artwork_conflicts, "Compare embedded artwork before choosing a source"),
            ("❗ Scan errors", len(laptop.errors) + len(phone.errors), "Unreadable files are never modified"),
        ]
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._set_busy(False)
        self.status_var.set(f"Scan complete — {len(laptop.tracks)} + {len(phone.tracks)} tracks. Nothing was changed.")

    def dry_run(self) -> None:
        if not self.plan:
            return
        summary = summarize(self.plan)
        unresolved = summary.fuzzy
        messagebox.showinfo(
            "Dry run — no files changed",
            f"READ-ONLY PREVIEW\n\n"
            f"Would add: {summary.add}\n"
            f"Matched: {summary.matched}\n"
            f"Fuzzy matches needing review: {unresolved}\n"
            f"Metadata conflicts: {summary.metadata_conflicts}\n"
            f"Artwork conflicts: {summary.artwork_conflicts}\n"
            f"Scan errors: {summary.scan_errors}\n\n"
            f"No files were created, replaced, deleted, or modified.",
        )
        self.status_var.set("Dry run complete — no files were changed.")

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

    def review_fuzzy(self) -> None:
        if not self.plan:
            return
        fuzzy = [m for m in self.plan.matches if not m.confirmed]
        if not fuzzy:
            messagebox.showinfo("No fuzzy matches", "There are no unconfirmed fuzzy matches.")
            return
        decisions = review_fuzzy_matches(self, fuzzy)
        if decisions is None:
            self.status_var.set("Fuzzy review cancelled. Unconfirmed matches remain blocked from merge.")
            return
        self.fuzzy_decisions.update(decisions)
        self.plan = apply_fuzzy_decisions(self.plan, decisions)
        confirmed = sum(1 for m in self.plan.matches if m.confirmed)
        self.status_var.set(f"Fuzzy review saved — {len(decisions)} decision(s), {confirmed} confirmed matches.")
        self._set_busy(False)

    def merge(self) -> None:
        if not self.plan or not self.phone_root or not self.laptop_root:
            return
        unresolved = [m for m in self.plan.matches if not m.confirmed]
        if unresolved:
            answer = messagebox.askyesno("Review fuzzy matches first?", f"There are {len(unresolved)} unconfirmed fuzzy match(es).\n\nReview them before merging?\n\nUnconfirmed fuzzy matches cannot be merged as matches.")
            if answer:
                self.review_fuzzy()
                return
            messagebox.showwarning("Fuzzy matches still unresolved", "Please review every fuzzy match before merging. This protects against merging different songs.")
            return

        count = len(self.plan.phone_only)
        conflict_count = sum(m.metadata_conflict or m.artwork_conflict for m in self.plan.matches)
        if conflict_count and not self.review_choices:
            answer = messagebox.askyesno("Review conflicts first?", f"There are {conflict_count} metadata/artwork conflict(s).\n\nReview them before merging?\n\nChoosing No keeps the Library A version for every conflict.")
            if answer:
                self.review()
                return

        answer = messagebox.askyesno(
            "Create backup and merge?",
            f"This will:\n\n• Back up Library A first\n• Copy {count} Library B-only song(s)\n• Apply your reviewed conflict choices\n• Keep Library A versions by default\n\nContinue?",
        )
        if not answer:
            return
        self._set_busy(True)
        self.status_var.set("Creating backup and applying the merge plan…")
        backup_root = self.laptop_root.parent / "music-sync-backups"

        def worker() -> None:
            try:
                backup, copied, replaced, skipped = merge_with_conflicts(self.plan, self.laptop_root, self.phone_root, backup_root, self.review_choices)
                self.after(0, lambda: self._merge_done(backup, copied, replaced, skipped))
            except Exception as exc:
                self.after(0, lambda: self._merge_failed(exc))
        threading.Thread(target=worker, daemon=True).start()

    def _merge_done(self, backup: Path, copied, replaced, skipped) -> None:
        self._set_busy(False)
        self.status_var.set(f"Merge complete — added {len(copied)}, replaced {len(replaced)}, skipped {len(skipped)}.")
        messagebox.showinfo("Merge complete 🎵", f"Added {len(copied)} song(s).\nApplied {len(replaced)} Library B choice(s).\nSkipped {len(skipped)} conflict(s).\n\nBackup created at:\n{backup}\n\nThe merged Library A folder is ready to use.")
        self.scan()

    def _merge_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("Merge failed — no further changes were attempted.")
        messagebox.showerror("Merge failed", str(exc))


if __name__ == "__main__":
    MusicSyncApp().mainloop()
