"""
gui/settings.py - Settings page for app configuration.
"""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from modules.database import DatabaseManager
from modules.logger import logger


class SettingsPage(ctk.CTkFrame):
    """Application settings page."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.db = DatabaseManager()
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Settings",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=20, pady=(20, 12))

        # ── Download settings ──
        self._section("Download Settings")

        dl_card = self._card()
        self._setting_row(dl_card, "Default Output Folder", "output_dir", is_folder=True)
        self._setting_row(dl_card, "Default Quality",        "default_quality",
                          options=["best","1080p","720p","360p"])
        self._setting_row(dl_card, "Default Type",           "default_type",
                          options=["video","audio"])

        # ── App settings ──
        self._section("Application")
        app_card = self._card()

        # Theme
        self._theme_row(app_card)

        # Seed demo data
        seed_row = ctk.CTkFrame(app_card, fg_color="transparent")
        seed_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(seed_row, text="Demo Data", width=200, anchor="w",
                      text_color="#E6EDF3").pack(side="left")
        ctk.CTkButton(seed_row, text="Seed Demo Records", width=160, height=32,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#FFE66D", command=self._seed).pack(side="left", padx=8)

        # Clear DB
        clr_row = ctk.CTkFrame(app_card, fg_color="transparent")
        clr_row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(clr_row, text="Clear Database", width=200, anchor="w",
                      text_color="#E6EDF3").pack(side="left")
        ctk.CTkButton(clr_row, text="⚠ Clear All Data", width=160, height=32,
                       fg_color="#3D1F1F", hover_color="#5A2020",
                       text_color="#FF6B6B", command=self._clear_db).pack(side="left", padx=8)

        # Save button
        ctk.CTkButton(self, text="💾 Save Settings", width=160, height=40,
                       fg_color="#238636", hover_color="#2EA043",
                       command=self._save).pack(pady=20)

        self._widgets: dict[str, ctk.CTkBaseClass] = {}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section(self, title: str):
        ctk.CTkLabel(self, text=title,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#8B949E").pack(anchor="w", padx=26, pady=(8, 4))

    def _card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                             border_width=1, border_color="#30363D")
        card.pack(fill="x", padx=20, pady=4)
        return card

    def _setting_row(self, parent, label: str, key: str,
                     options: list[str] | None = None,
                     is_folder: bool = False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label, width=200, anchor="w",
                      text_color="#E6EDF3").pack(side="left")

        if is_folder:
            var = ctk.StringVar(value="downloads")
            entry = ctk.CTkEntry(row, textvariable=var, width=220,
                                  fg_color="#0D1117", border_color="#30363D",
                                  text_color="#E6EDF3")
            entry.pack(side="left", padx=8)
            ctk.CTkButton(row, text="Browse", width=80, height=28,
                           fg_color="#21262D", hover_color="#30363D",
                           text_color="#8B949E",
                           command=lambda v=var: self._browse(v)).pack(side="left")
            self._widgets[key] = var
        elif options:
            var = ctk.StringVar(value=options[0])
            ctk.CTkOptionMenu(row, values=options, variable=var,
                               fg_color="#21262D", button_color="#30363D",
                               dropdown_fg_color="#161B22", text_color="#E6EDF3",
                               width=140).pack(side="left", padx=8)
            self._widgets[key] = var
        else:
            var = ctk.StringVar()
            ctk.CTkEntry(row, textvariable=var, width=220,
                          fg_color="#0D1117", border_color="#30363D",
                          text_color="#E6EDF3").pack(side="left", padx=8)
            self._widgets[key] = var

    def _theme_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text="Theme", width=200, anchor="w",
                      text_color="#E6EDF3").pack(side="left")
        self._theme_var = ctk.StringVar(value="Dark")
        ctk.CTkOptionMenu(row, values=["Dark","Light","System"],
                           variable=self._theme_var,
                           fg_color="#21262D", button_color="#30363D",
                           dropdown_fg_color="#161B22", text_color="#E6EDF3",
                           width=140,
                           command=lambda v: ctk.set_appearance_mode(v)).pack(side="left", padx=8)

    def _browse(self, var: ctk.StringVar):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _load_settings(self):
        for key, widget in self._widgets.items():
            val = self.db.get_setting(key)
            if val:
                widget.set(val)

    def _save(self):
        for key, widget in self._widgets.items():
            self.db.set_setting(key, widget.get())
        messagebox.showinfo("Saved", "Settings saved successfully.")
        logger.log_user_action("Save settings")

    def _seed(self):
        self.db.seed_demo_data()
        messagebox.showinfo("Done", "Demo data seeded successfully.\nGo to Dashboard to refresh.")
        logger.log_user_action("Seed demo data")

    def _clear_db(self):
        if messagebox.askyesno("⚠ Confirm", "This will permanently delete ALL download records. Continue?"):
            import sqlite3
            with sqlite3.connect(self.db.DB_PATH) as conn:
                conn.execute("DELETE FROM downloads")
            messagebox.showinfo("Cleared", "All download records deleted.")
            logger.log_user_action("Clear database")
