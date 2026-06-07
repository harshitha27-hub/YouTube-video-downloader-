"""
gui/reports.py - Report generation page (CSV, Excel, PDF).
"""

import os
import threading
import subprocess
import platform
import customtkinter as ctk
from tkinter import messagebox
from modules.report_generator import ReportGenerator
from modules.logger import logger


class ReportsPage(ctk.CTkFrame):
    """Page to generate and download reports."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.gen = ReportGenerator()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Reports",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=20, pady=(20, 12))

        cards_data = [
            ("📄 CSV Report",   "Comma-separated file of all download history",
             "#4ECDC4", self._gen_csv),
            ("📊 Excel Report", "Multi-sheet workbook with history, analytics & predictions",
             "#00D4FF", self._gen_excel),
            ("📋 PDF Report",   "Styled PDF with analytics summary, predictions & history",
             "#FFE66D", self._gen_pdf),
        ]

        for title, desc, color, cmd in cards_data:
            card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                                 border_width=1, border_color="#30363D")
            card.pack(fill="x", padx=20, pady=8)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=16, pady=14)
            ctk.CTkLabel(left, text=title,
                          font=ctk.CTkFont(size=15, weight="bold"),
                          text_color=color).pack(anchor="w")
            ctk.CTkLabel(left, text=desc, font=ctk.CTkFont(size=11),
                          text_color="#8B949E").pack(anchor="w", pady=(2, 0))

            ctk.CTkButton(card, text="Generate", width=110, height=36,
                           fg_color="#21262D", hover_color="#30363D",
                           text_color=color, command=cmd).pack(side="right", padx=16)

        # Output log
        ctk.CTkLabel(self, text="Generated Reports",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=20, pady=(16, 4))

        self.log_box = ctk.CTkTextbox(self, height=200, fg_color="#161B22",
                                       border_color="#30363D", text_color="#4ECDC4",
                                       font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.log_box.configure(state="disabled")

        # Open reports folder
        ctk.CTkButton(self, text="📁 Open Reports Folder", width=180, height=36,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#8B949E", command=self._open_folder).pack(pady=(0, 20))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _append_log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _run_in_thread(self, fn, label: str):
        self._append_log(f"⏳ Generating {label}…")

        def worker():
            try:
                path = fn()
                self.after(0, self._append_log, f"✅ {label} saved: {path}")
                self.after(0, messagebox.showinfo, "Report Ready", f"{label} saved:\n{path}")
            except Exception as exc:
                self.after(0, self._append_log, f"❌ Error: {exc}")
                logger.error(f"Report generation error: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def _gen_csv(self):   self._run_in_thread(self.gen.generate_csv,   "CSV Report")
    def _gen_excel(self): self._run_in_thread(self.gen.generate_excel, "Excel Report")
    def _gen_pdf(self):   self._run_in_thread(self.gen.generate_pdf,   "PDF Report")

    def _open_folder(self):
        path = os.path.abspath("reports")
        os.makedirs(path, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
