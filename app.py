from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from music_sync.direction import MasterLibrary, SyncDirection
from music_sync.dry_run import dry_run_mirror, dry_run_reconcile, dry_run_safe
from music_sync.execution_report import ExecutionReport, report_from_mirror, report_from_reconcile, report_from_safe
from music_sync.fuzzy_ui import apply_fuzzy_decisions, review_fuzzy_matches
from music_sync.matcher import build_plan
from music_sync.models import SyncMode, SyncPlan
from music_sync.mirror import MirrorConfirmationError, build_mirror_preview, execute_mirror
from music_sync.path_safety import validate_library_pair
from music_sync.reconcile import ReconcileDecision, execute_reconcile
from music_sync.review import ConflictChoice
from music_sync.scanner import scan_library
from music_sync.settings import Settings, SettingsStore
from music_sync.sync import execute_safe


class MusicSyncApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("music-sync")
        self.geometry("1180x780")
        self.minsize(940, 640)
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.plan: SyncPlan | None = None
        self.library_a_root: Path | None = None
        self.library_b_root: Path | None = None
        self.last_report: ExecutionReport | None = None
        self.review_choices: dict[str, ConflictChoice] = {}
        self.scan_errors = 0
        self.library_a_var = tk.StringVar(value=self.settings.library_a)
        self.library_b_var = tk.StringVar(value=self.settings.library_b)
        self.master_var = tk.StringVar(value=self.settings.master or "library_a")
        self.mode_var = tk.StringVar(value=self.settings.sync_mode)
        self.backup_var = tk.StringVar(value=self.settings.backup_location)
        self.status_var = tk.StringVar(value="Choose Library A and Library B to begin.")
        self._build_ui()
        self._update_controls()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="music-sync", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Compare, review, preview, and synchronize two arbitrary music libraries.").pack(anchor="w", pady=(2, 18))
        self._path_row(frame, "Library A", self.library_a_var)
        self._path_row(frame, "Library B", self.library_b_var)
        options = ttk.Frame(frame)
        options.pack(fill="x", pady=8)
        self._combo_row(options, "Master", self.master_var, ["library_a", "library_b"])
        self._combo_row(options, "Mode", self.mode_var, [SyncMode.SAFE, SyncMode.RECONCILE, SyncMode.MIRROR])
        self._path_row(options, "Backup location", self.backup_var, "Select backup folder")
        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=16)
        self.scan_button = ttk.Button(actions, text="Scan", command=self.scan)
        self.scan_button.pack(side="left")
        self.review_conflicts_button = ttk.Button(actions, text="Review conflicts", command=self.review_conflicts, state="disabled")
        self.review_conflicts_button.pack(side="left", padx=8)
        self.review_fuzzy_button = ttk.Button(actions, text="Review fuzzy", command=self.review_fuzzy, state="disabled")
        self.review_fuzzy_button.pack(side="left")
        self.dry_run_button = ttk.Button(actions, text="Dry run", command=self.dry_run, state="disabled")
        self.dry_run_button.pack(side="left", padx=8)
        self.execute_button = ttk.Button(actions, text="Apply", command=self.execute, state="disabled")
        self.execute_button.pack(side="left")
        self.export_button = ttk.Button(actions, text="Export report", command=self.export_report, state="disabled")
        self.export_button.pack(side="left", padx=8)
        self.tree = ttk.Treeview(frame, columns=("category", "count", "details"), show="headings", height=21)
        for column, title, width in (("category", "Category", 260), ("count", "Count", 90), ("details", "Details", 700)):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(12, 0))

    def _path_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, browse_title: str = "Select music library") -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, width=16).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text="Browse", command=lambda: self.browse(variable, browse_title)).pack(side="left")

    def _combo_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[str]) -> None:
        row = ttk.Frame(parent)
        row.pack(side="left", padx=(0, 18))
        ttk.Label(row, text=label).pack(side="left", padx=(0, 6))
        combo = ttk.Combobox(row, textvariable=variable, values=values, state="readonly", width=14)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _event: self._save_settings())

    def browse(self, variable: tk.StringVar, title: str) -> None:
        path = filedialog.askdirectory(title=title)
        if path:
            variable.set(path)
            self._save_settings()

    def _save_settings(self) -> None:
        try:
            settings = Settings(
                library_a=self.library_a_var.get().strip(), library_b=self.library_b_var.get().strip(),
                master=self.master_var.get().strip(), sync_mode=self.mode_var.get().strip(),
                backup_location=self.backup_var.get().strip(), fuzzy_threshold=self.settings.fuzzy_threshold,
                conflict_defaults=self.settings.conflict_defaults, appearance=self.settings.appearance,
            )
            self.settings_store.save(settings)
            self.settings = settings
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)

    def _direction(self) -> SyncDirection:
        if not self.library_a_root or not self.library_b_root:
            raise ValueError("Scan both libraries before applying a plan.")
        master = MasterLibrary.LIBRARY_A if self.master_var.get() == "library_a" else MasterLibrary.LIBRARY_B
        return SyncDirection(self.library_a_root, self.library_b_root, master)

    def _backup_root(self) -> Path:
        value = self.backup_var.get().strip()
        if not value:
            raise ValueError("Choose a backup location before applying a modifying mode.")
        return Path(value).expanduser()

    def _set_busy(self, busy: bool) -> None:
        if self.scan_button:
            self.scan_button.configure(state="disabled" if busy else "normal")
        self._update_controls(busy)

    def _update_controls(self, busy: bool = False) -> None:
        has_plan = self.plan is not None
        fuzzy = has_plan and any(not match.confirmed for match in self.plan.matches)
        conflicts = has_plan and any(match.metadata_conflict or match.artwork_conflict for match in self.plan.matches)
        for button, enabled in ((self.review_conflicts_button, conflicts), (self.review_fuzzy_button, fuzzy), (self.dry_run_button, has_plan), (self.execute_button, has_plan), (self.export_button, self.last_report is not None)):
            if button:
                button.configure(state="normal" if enabled and not busy else "disabled")

    def scan(self) -> None:
        self._save_settings()
        try:
            library_a, library_b = validate_library_pair(self.library_a_var.get().strip(), self.library_b_var.get().strip())
        except (OSError, ValueError) as exc:
            messagebox.showerror("Invalid libraries", str(exc), parent=self)
            return
        self._set_busy(True)
        self.status_var.set("Scanning both libraries…")

        def worker() -> None:
            result_a = scan_library(library_a, "a")
            result_b = scan_library(library_b, "b")
            plan = build_plan(result_a, result_b, threshold=self.settings.fuzzy_threshold)
            self.after(0, lambda: self._show_scan(library_a, library_b, result_a, result_b, plan))

        threading.Thread(target=worker, daemon=True).start()

    def _show_scan(self, library_a: Path, library_b: Path, result_a, result_b, plan: SyncPlan) -> None:
        self.plan, self.library_a_root, self.library_b_root = plan, library_a, library_b
        self.scan_errors = len(result_a.errors) + len(result_b.errors)
        self.last_report = None
        self.review_choices = {}
        for item in self.tree.get_children():
            self.tree.delete(item)
        exact = sum(match.confirmed for match in plan.matches)
        rows = [
            ("Library A-only", len(plan.library_a_only), "Missing from Library B"),
            ("Library B-only", len(plan.library_b_only), "Missing from Library A"),
            ("Matches", len(plan.matches), f"{exact} confirmed, {len(plan.matches) - exact} fuzzy/unconfirmed"),
            ("Metadata conflicts", sum(m.metadata_conflict for m in plan.matches), "Require explicit review"),
            ("Artwork conflicts", sum(m.artwork_conflict for m in plan.matches), "Require explicit review"),
            ("Scan errors", self.scan_errors, "Unreadable files are not modified"),
        ]
        for row in rows:
            self.tree.insert("", "end", values=row)
        self._set_busy(False)
        self.status_var.set(f"Scan complete — {len(result_a.tracks)} + {len(result_b.tracks)} tracks. Nothing was changed.")

    def review_conflicts(self) -> None:
        if not self.plan:
            return
        from music_sync.conflict_ui import review_conflicts
        conflicts = [m for m in self.plan.matches if m.metadata_conflict or m.artwork_conflict]
        choices = review_conflicts(self, conflicts)
        if choices is not None:
            self.review_choices = choices
            self.status_var.set(f"Saved {len(choices)} conflict decision(s).")

    def review_fuzzy(self) -> None:
        if not self.plan:
            return
        fuzzy = [m for m in self.plan.matches if not m.confirmed]
        decisions = review_fuzzy_matches(self, fuzzy)
        if decisions is not None:
            self.plan = apply_fuzzy_decisions(self.plan, decisions)
            self.status_var.set("Fuzzy review saved. Rescan if the filesystem changes.")
            self._update_controls()

    def _reconcile_decisions(self) -> dict[str, ReconcileDecision] | None:
        if not self.plan:
            return None
        decisions: dict[str, ReconcileDecision] = {}
        for track in self.plan.library_a_only:
            answer = messagebox.askyesnocancel("Reconcile A-only track", f"Copy to Library B?\n\n{track.path}\n\nYes = Copy A → B\nNo = Skip", parent=self)
            if answer is None:
                return None
            decisions[f"a-only:{track.path}"] = ReconcileDecision.COPY_A_TO_B if answer else ReconcileDecision.SKIP
        for track in self.plan.library_b_only:
            answer = messagebox.askyesnocancel("Reconcile B-only track", f"Copy to Library A?\n\n{track.path}\n\nYes = Copy B → A\nNo = Skip", parent=self)
            if answer is None:
                return None
            decisions[f"b-only:{track.path}"] = ReconcileDecision.COPY_B_TO_A if answer else ReconcileDecision.SKIP
        for path, choice in self.review_choices.items():
            decisions[f"match:{path}"] = {ConflictChoice.LAPTOP: ReconcileDecision.KEEP_A, ConflictChoice.PHONE: ReconcileDecision.KEEP_B, ConflictChoice.SKIP: ReconcileDecision.SKIP}[choice]
        if any(not m.confirmed and f"match:{m.library_a.path}" not in decisions for m in self.plan.matches):
            return None
        return decisions

    def dry_run(self) -> None:
        if not self.plan:
            return
        try:
            direction = self._direction()
            mode = self.mode_var.get()
            if mode == SyncMode.SAFE:
                result = dry_run_safe(self.plan, direction)
            elif mode == SyncMode.RECONCILE:
                decisions = self._reconcile_decisions()
                if decisions is None:
                    raise ValueError("Every Reconcile item needs an explicit decision.")
                result = dry_run_reconcile(self.plan, decisions, self._backup_root())
            else:
                result = dry_run_mirror(self.plan, direction)
            messagebox.showinfo("Dry run — no files changed", f"Mode: {mode}\nStatus: {result.status}\nOperations: {len(result.operations)}\nSkipped: {len(result.skipped)}\nBlocked: {len(result.blocked)}\n\nNo library or backup files were modified.", parent=self)
        except Exception as exc:
            messagebox.showerror("Dry run blocked", str(exc), parent=self)

    def execute(self) -> None:
        if not self.plan:
            return
        mode = self.mode_var.get()
        if mode == SyncMode.SAFE:
            self._execute_safe()
        elif mode == SyncMode.RECONCILE:
            self._execute_reconcile()
        else:
            self._execute_mirror()

    def _execute_safe(self) -> None:
        try:
            direction, backup = self._direction(), self._backup_root()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Safe mode blocked", str(exc), parent=self)
            return
        if not messagebox.askyesno("Apply Safe mode?", "Safe mode only adds missing files. It never deletes or overwrites existing destination files.\n\nCreate a verified backup and continue?", parent=self):
            return
        self._run_worker(lambda: report_from_safe(execute_safe(self.plan, direction, backup)))

    def _execute_reconcile(self) -> None:
        decisions = self._reconcile_decisions()
        if decisions is None:
            messagebox.showwarning("Reconcile blocked", "Every missing, conflicting, or fuzzy item needs an explicit decision.", parent=self)
            return
        try:
            backup = self._backup_root()
        except ValueError as exc:
            messagebox.showerror("Reconcile blocked", str(exc), parent=self)
            return
        self._run_worker(lambda: report_from_reconcile(execute_reconcile(self.plan, decisions, backup)))

    def _execute_mirror(self) -> None:
        try:
            direction, backup = self._direction(), self._backup_root()
            preview = build_mirror_preview(self.plan, direction)
        except Exception as exc:
            messagebox.showerror("Mirror blocked", str(exc), parent=self)
            return
        if preview.blocked:
            messagebox.showwarning("Mirror blocked", "Resolve all fuzzy matches before Mirror execution.", parent=self)
            return
        messagebox.showinfo("Mirror preview", f"Copies: {len(preview.copies)}\nReplacements: {len(preview.replacements)}\nDeletions: {len(preview.deletions)}", parent=self)
        confirmation = simpledialog.askstring("Confirm Mirror", "Type MIRROR exactly to apply these changes:", parent=self)
        if confirmation is None:
            return
        self._run_worker(lambda: report_from_mirror(execute_mirror(self.plan, direction, backup, confirmation)))

    def _run_worker(self, work) -> None:
        self._set_busy(True)
        def worker() -> None:
            try:
                report = work()
                self.after(0, lambda: self._execution_done(report))
            except Exception as exc:
                self.after(0, lambda: self._execution_failed(exc))
        threading.Thread(target=worker, daemon=True).start()

    def _execution_done(self, report: ExecutionReport) -> None:
        self.last_report = report
        self._set_busy(False)
        self.status_var.set(f"{report.mode.title()} finished with status {report.final_status.value}.")
        messagebox.showinfo("Execution result", f"Mode: {report.mode}\nStatus: {report.final_status.value}\nAttempted: {report.attempted}\nSucceeded: {report.succeeded}\nFailed: {report.failed}\nSkipped: {report.skipped}\nRolled back: {report.rolled_back}", parent=self)

    def _execution_failed(self, exc: Exception) -> None:
        self._set_busy(False)
        self.status_var.set("Execution blocked or failed.")
        messagebox.showerror("Execution failed", str(exc), parent=self)

    def export_report(self) -> None:
        if not self.last_report:
            return
        destination = filedialog.asksaveasfilename(title="Export execution report", defaultextension=".json", filetypes=[("JSON report", "*.json")], initialfile="music-sync-execution-report.json")
        if destination:
            path = self.last_report.save_json(Path(destination))
            self.status_var.set(f"Report exported to {path}")


if __name__ == "__main__":
    MusicSyncApp().mainloop()
