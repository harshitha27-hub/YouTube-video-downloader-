"""
main.py - Entry point for YouTube Downloader Pro.
Builds the main window with sidebar navigation and page routing.
"""

import os
import sys
import customtkinter as ctk

# ── Ensure project root is on sys.path ───────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Bootstrap required directories ───────────────────────────────────────────
for d in ("database", "downloads", "reports", "logs"):
    os.makedirs(d, exist_ok=True)

# ── Import pages ─────────────────────────────────────────────────────────────
from gui.dashboard  import DashboardPage
from gui.downloader import DownloaderPage
from gui.history    import HistoryPage
from gui.analytics  import AnalyticsPage
from gui.prediction import PredictionPage
from gui.reports    import ReportsPage
from gui.settings   import SettingsPage
from modules.database import DatabaseManager
from modules.logger   import logger


# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Palette constants ─────────────────────────────────────────────────────────
BG_MAIN    = "#0D1117"
BG_SIDEBAR = "#010409"
ACCENT     = "#00D4FF"
TEXT_DIM   = "#8B949E"
TEXT_BRIGHT= "#E6EDF3"


class MainApp(ctk.CTk):
    """Main application window."""

    NAV_ITEMS = [
        ("🏠  Dashboard",   "dashboard",  DashboardPage),
        ("⬇  Downloader",  "downloader", DownloaderPage),
        ("📜  History",     "history",    HistoryPage),
        ("📊  Analytics",   "analytics",  AnalyticsPage),
        ("🤖  Prediction",  "prediction", PredictionPage),
        ("📋  Reports",     "reports",    ReportsPage),
        ("⚙  Settings",    "settings",   SettingsPage),
    ]

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=BG_MAIN)

        # Seed demo data on first run
        db = DatabaseManager()
        db.seed_demo_data()

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        self._active_page = ""

        self._build_ui()
        self._navigate("dashboard")

        logger.info("Application started")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Root panes ──
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=BG_SIDEBAR,
                                     corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # ── Logo / Brand ──
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(20, 8))

        ctk.CTkLabel(brand, text="▶",
                     font=ctk.CTkFont(size=32), text_color=ACCENT).pack(side="left")
        title_col = ctk.CTkFrame(brand, fg_color="transparent")
        title_col.pack(side="left", padx=8)
        ctk.CTkLabel(title_col, text="YT Downloader",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT_BRIGHT).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Pro Edition",
                     font=ctk.CTkFont(size=10),
                     text_color=TEXT_DIM).pack(anchor="w")

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#21262D").pack(
            fill="x", padx=16, pady=12)

        # ── Navigation buttons ──
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)

        for label, key, PageClass in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame, text=label,
                anchor="w", height=42,
                fg_color="transparent",
                hover_color="#161B22",
                text_color=TEXT_DIM,
                font=ctk.CTkFont(size=13),
                corner_radius=8,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", pady=2)
            self._nav_btns[key] = btn

        # ── Footer version ──
        ctk.CTkLabel(self.sidebar, text="v1.0  •  Built with yt-dlp",
                     font=ctk.CTkFont(size=9),
                     text_color="#3D444D").pack(side="bottom", pady=12)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key: str):
        if self._active_page == key:
            return

        # Deactivate previous
        if self._active_page and self._active_page in self._nav_btns:
            self._nav_btns[self._active_page].configure(
                fg_color="transparent", text_color=TEXT_DIM)

        # Activate new
        self._nav_btns[key].configure(fg_color="#161B22", text_color=ACCENT)
        self._active_page = key

        # Hide all pages
        for frame in self._pages.values():
            frame.pack_forget()

        # Lazy-create page if needed
        if key not in self._pages:
            PageClass = next(pc for _, k, pc in self.NAV_ITEMS if k == key)
            page = PageClass(self.content)
            self._pages[key] = page

        self._pages[key].pack(fill="both", expand=True)
        logger.log_user_action("Navigate", key)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
