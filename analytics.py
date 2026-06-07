"""
gui/analytics.py - Analytics dashboard page with embedded Plotly chart launches.
"""

import os
import threading
import webbrowser
import customtkinter as ctk
from modules.database import DatabaseManager
from modules.analytics_engine import AnalyticsEngine
from modules.logger import logger


class AnalyticsPage(ctk.CTkFrame):
    """Analytics page with chart buttons and stat cards."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.db     = DatabaseManager()
        self.engine = AnalyticsEngine()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Analytics",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(side="left")
        ctk.CTkButton(hdr, text="⟳ Refresh", width=100, height=36,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#00D4FF", command=self.refresh).pack(side="right")

        # Chart launcher buttons
        chart_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                                   border_width=1, border_color="#30363D")
        chart_card.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(chart_card, text="Interactive Charts (open in browser)",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8B949E").pack(anchor="w", padx=16, pady=(12, 6))

        btn_row = ctk.CTkFrame(chart_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        charts = [
            ("📈 Activity Trend",  self._open_trend,   "#00D4FF"),
            ("📊 Top Channels",    self._open_channels, "#4ECDC4"),
            ("🎯 By Quality",      self._open_quality,  "#FFE66D"),
            ("🎵 Video vs Audio",  self._open_types,    "#FF6B6B"),
            ("🖥 Full Dashboard",  self._open_combined, "#A8E6CF"),
        ]
        for label, cmd, color in charts:
            ctk.CTkButton(btn_row, text=label, width=140, height=36,
                           fg_color="#21262D", hover_color="#30363D",
                           text_color=color, command=cmd).pack(side="left", padx=4)

        # Stats grid
        self.stats_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=(8, 20))

        # Row 1 – summary cards
        self.row1 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.row1.pack(fill="x", pady=4)

        # By Quality table
        ctk.CTkLabel(self.stats_frame, text="Quality Breakdown",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", pady=(12, 4))
        self.quality_frame = ctk.CTkFrame(self.stats_frame, fg_color="#161B22", corner_radius=8)
        self.quality_frame.pack(fill="x", pady=4)

        # By Channel table
        ctk.CTkLabel(self.stats_frame, text="Channel Breakdown (Top 10)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", pady=(12, 4))
        self.channel_tbl_frame = ctk.CTkFrame(self.stats_frame, fg_color="#161B22", corner_radius=8)
        self.channel_tbl_frame.pack(fill="x", pady=4)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        stats = self.db.get_stats()
        self.after(0, self._render, stats)

    def _render(self, stats: dict):
        for w in self.row1.winfo_children():
            w.destroy()

        cards = [
            ("📥 Total", str(stats["total"]),       "#00D4FF"),
            ("🎬 Videos",str(stats["videos"]),       "#4ECDC4"),
            ("🎵 Audio", str(stats["audios"]),       "#FFE66D"),
            ("💾 GB",    f"{stats['storage_gb']:.1f}","#FF6B6B"),
        ]
        for label, val, color in cards:
            f = ctk.CTkFrame(self.row1, fg_color="#161B22", corner_radius=10,
                              border_width=1, border_color=color)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="#8B949E").pack(pady=(10,2), padx=12, anchor="w")
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(padx=12, pady=(0,10), anchor="w")
            f.pack(side="left", expand=True, fill="both", padx=5)

        # Quality table
        for w in self.quality_frame.winfo_children():
            w.destroy()
        self._render_table(self.quality_frame,
                            ["Quality", "Count"],
                            [(r["quality"], str(r["cnt"])) for r in stats.get("by_quality",[])])

        # Channel table
        for w in self.channel_tbl_frame.winfo_children():
            w.destroy()
        self._render_table(self.channel_tbl_frame,
                            ["Channel", "Count"],
                            [(r["channel"], str(r["cnt"])) for r in stats.get("by_channel",[])])

    def _render_table(self, parent, headers: list, rows: list):
        hdr_row = ctk.CTkFrame(parent, fg_color="#21262D")
        hdr_row.pack(fill="x")
        for h in headers:
            ctk.CTkLabel(hdr_row, text=h, font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="#8B949E", width=200, anchor="w").pack(side="left", padx=12, pady=6)

        for i, r in enumerate(rows):
            bg = "#0D1117" if i % 2 == 0 else "#161B22"
            row_f = ctk.CTkFrame(parent, fg_color=bg)
            row_f.pack(fill="x")
            for val in r:
                ctk.CTkLabel(row_f, text=val, font=ctk.CTkFont(size=11),
                              text_color="#E6EDF3", width=200, anchor="w").pack(side="left", padx=12, pady=4)

        if not rows:
            ctk.CTkLabel(parent, text="No data.", text_color="#8B949E").pack(pady=12)

    # ── Chart openers ─────────────────────────────────────────────────────────

    def _open_chart(self, chart_fn, filename: str):
        def _worker():
            fig  = chart_fn()
            path = os.path.abspath(os.path.join("reports", filename))
            os.makedirs("reports", exist_ok=True)
            fig.write_html(path)
            webbrowser.open(f"file://{path}")
            logger.log_user_action("Open chart", filename)
        threading.Thread(target=_worker, daemon=True).start()

    def _open_trend(self):    self._open_chart(self.engine.downloads_trend_chart, "trend.html")
    def _open_channels(self): self._open_chart(self.engine.channel_bar_chart,     "channels.html")
    def _open_quality(self):  self._open_chart(self.engine.quality_pie_chart,     "quality.html")
    def _open_types(self):    self._open_chart(self.engine.type_donut_chart,      "types.html")
    def _open_combined(self): self._open_chart(self.engine.combined_dashboard,    "dashboard.html")
