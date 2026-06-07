"""
gui/dashboard.py - Main dashboard page with stat cards and charts.
"""

import customtkinter as ctk
import threading
from modules.database import DatabaseManager
from modules.analytics_engine import AnalyticsEngine


class DashboardPage(ctk.CTkFrame):
    """Dashboard with KPI cards and embedded Plotly charts (via webview or export)."""

    CARD_DEFS = [
        ("📥 Total Downloads",      "total",       "#00D4FF"),
        ("🎬 Videos",               "videos",      "#4ECDC4"),
        ("🎵 Audio Files",          "audios",      "#FFE66D"),
        ("💾 Storage Used",         "storage_str", "#FF6B6B"),
        ("🏆 Top Channel",          "top_channel", "#A8E6CF"),
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.db = DatabaseManager()
        self._build_ui()
        self.refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header, text="Dashboard",
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color="#E6EDF3",
        ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            header, text="⟳ Refresh", width=100, height=36,
            fg_color="#21262D", hover_color="#30363D", text_color="#00D4FF",
            command=self.refresh,
        )
        self.refresh_btn.pack(side="right")

        # KPI card row
        self.card_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.card_frame.pack(fill="x", padx=20, pady=8)
        self.card_labels: dict = {}

        for label_text, key, accent in self.CARD_DEFS:
            card  = self._make_card(self.card_frame, label_text, accent)
            val_l = card.nametowidget(card.winfo_children()[-1].winfo_name())
            self.card_labels[key] = card.winfo_children()[-1]
            card.pack(side="left", expand=True, fill="both", padx=6, pady=4)

        # Trend section
        trend_lbl = ctk.CTkLabel(
            self, text="📈 Recent Activity",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#E6EDF3",
        )
        trend_lbl.pack(anchor="w", padx=26, pady=(12, 4))

        self.trend_frame = ctk.CTkScrollableFrame(self, fg_color="#161B22", height=200)
        self.trend_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # Top channels section
        ch_lbl = ctk.CTkLabel(
            self, text="🏆 Top Channels",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#E6EDF3",
        )
        ch_lbl.pack(anchor="w", padx=26, pady=(4, 4))

        self.channel_frame = ctk.CTkScrollableFrame(self, fg_color="#161B22", height=180)
        self.channel_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _make_card(self, parent, title: str, accent: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color="#161B22", corner_radius=12,
                             border_width=1, border_color=accent)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11),
                     text_color="#8B949E").pack(pady=(14, 2), padx=14, anchor="w")
        val_l = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=24, weight="bold"),
                              text_color=accent)
        val_l.pack(padx=14, pady=(0, 14), anchor="w")
        return card

    # ── Data refresh ──────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        stats = self.db.get_stats()
        self.after(0, self._update_ui, stats)

    def _update_ui(self, stats: dict):
        # Update KPI cards
        vals = {
            "total":       str(stats["total"]),
            "videos":      str(stats["videos"]),
            "audios":      str(stats["audios"]),
            "storage_str": f"{stats['storage_gb']:.2f} GB",
            "top_channel": stats["top_channel"],
        }
        for key, label in self.card_labels.items():
            label.configure(text=vals.get(key, "—"))

        # Trend bars
        for w in self.trend_frame.winfo_children():
            w.destroy()
        trend = stats.get("trend", [])
        if trend:
            max_cnt = max(t["cnt"] for t in trend) or 1
            for row in trend[-14:]:   # last 14 days
                r = ctk.CTkFrame(self.trend_frame, fg_color="transparent")
                r.pack(fill="x", padx=8, pady=2)
                ctk.CTkLabel(r, text=row["day"], width=90, anchor="w",
                              font=ctk.CTkFont(size=11), text_color="#8B949E").pack(side="left")
                bar_pct = row["cnt"] / max_cnt
                bar = ctk.CTkProgressBar(r, width=260, height=14,
                                          fg_color="#21262D", progress_color="#00D4FF")
                bar.set(bar_pct)
                bar.pack(side="left", padx=8)
                ctk.CTkLabel(r, text=str(row["cnt"]), font=ctk.CTkFont(size=11),
                              text_color="#E6EDF3").pack(side="left")
        else:
            ctk.CTkLabel(self.trend_frame, text="No data yet.",
                          text_color="#8B949E").pack(pady=20)

        # Top channels
        for w in self.channel_frame.winfo_children():
            w.destroy()
        channels = stats.get("by_channel", [])
        if channels:
            max_ch = max(c["cnt"] for c in channels) or 1
            for i, ch in enumerate(channels[:8]):
                r = ctk.CTkFrame(self.channel_frame, fg_color="transparent")
                r.pack(fill="x", padx=8, pady=2)
                medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
                ctk.CTkLabel(r, text=medal, width=30,
                              font=ctk.CTkFont(size=11)).pack(side="left")
                ctk.CTkLabel(r, text=ch["channel"], width=160, anchor="w",
                              font=ctk.CTkFont(size=11), text_color="#E6EDF3").pack(side="left", padx=4)
                bar = ctk.CTkProgressBar(r, width=200, height=14,
                                          fg_color="#21262D", progress_color="#4ECDC4")
                bar.set(ch["cnt"] / max_ch)
                bar.pack(side="left", padx=8)
                ctk.CTkLabel(r, text=str(ch["cnt"]),
                              font=ctk.CTkFont(size=11), text_color="#4ECDC4").pack(side="left")
        else:
            ctk.CTkLabel(self.channel_frame, text="No data yet.",
                          text_color="#8B949E").pack(pady=20)
