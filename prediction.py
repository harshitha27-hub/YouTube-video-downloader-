"""
gui/prediction.py - Machine Learning prediction page.
"""

import threading
import customtkinter as ctk
from modules.predictor import DownloadPredictor
from modules.database import DatabaseManager
from modules.logger import logger


class PredictionPage(ctk.CTkFrame):
    """ML prediction page with portfolio stats and forecast cards."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.predictor = DownloadPredictor()
        self.db        = DatabaseManager()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Predictions & Portfolio",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(side="left")
        ctk.CTkButton(hdr, text="⟳ Refresh", width=100, height=36,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#00D4FF", command=self.refresh).pack(side="right")

        # ── Portfolio tracking card ──
        p_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                               border_width=1, border_color="#00D4FF")
        p_card.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(p_card, text="📁 Portfolio Tracking",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#00D4FF").pack(anchor="w", padx=16, pady=(12, 4))

        self.portfolio_frame = ctk.CTkFrame(p_card, fg_color="transparent")
        self.portfolio_frame.pack(fill="x", padx=16, pady=(0, 14))

        # ── ML Prediction cards ──
        ctk.CTkLabel(self, text="🤖 ML Download Forecast (Polynomial Regression)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=26, pady=(12, 4))

        self.pred_dl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pred_dl_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(self, text="💾 Storage Forecast",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=26, pady=(12, 4))

        self.pred_st_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pred_st_frame.pack(fill="x", padx=20, pady=4)

        # ── Text report ──
        ctk.CTkLabel(self, text="📊 Full Prediction Report",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=26, pady=(12, 4))

        self.text_box = ctk.CTkTextbox(self, height=200, fg_color="#161B22",
                                        border_color="#30363D",
                                        text_color="#00D4FF",
                                        font=ctk.CTkFont(family="Consolas", size=12))
        self.text_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.text_box.configure(state="disabled")

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            stats  = self.db.get_stats()
            pred   = self.predictor.predict_trends()
            report = self.predictor.get_formatted_predictions()
            self.after(0, self._render, stats, pred, report)
        except Exception as exc:
            logger.error(f"Prediction error: {exc}")
            self.after(0, self._show_error, str(exc))

    def _render(self, stats: dict, pred: dict, report: str):
        # Portfolio
        for w in self.portfolio_frame.winfo_children():
            w.destroy()

        portfolio_items = [
            ("🎬 Videos Downloaded", str(stats["videos"]),      "#4ECDC4"),
            ("🎵 Audio Files",       str(stats["audios"]),      "#FFE66D"),
            ("💾 Total Storage",     f"{stats['storage_gb']:.1f} GB", "#FF6B6B"),
            ("🏆 Top Channel",       stats["top_channel"],      "#00D4FF"),
        ]
        for label, val, color in portfolio_items:
            f = ctk.CTkFrame(self.portfolio_frame, fg_color="#0D1117", corner_radius=8,
                              border_width=1, border_color=color)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                          text_color="#8B949E").pack(pady=(8,0), padx=12, anchor="w")
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=18, weight="bold"),
                          text_color=color).pack(padx=12, pady=(0,8), anchor="w")
            f.pack(side="left", expand=True, fill="both", padx=4)

        # Download prediction cards
        for w in self.pred_dl_frame.winfo_children():
            w.destroy()

        dl = pred["downloads"]
        dl_items = [
            ("Next Week",     str(dl["next_week"]),    "#A8E6CF"),
            ("Next Month",    str(dl["next_month"]),   "#00D4FF"),
            ("Next 3 Months", str(dl["next_3months"]), "#4ECDC4"),
        ]
        for label, val, color in dl_items:
            f = ctk.CTkFrame(self.pred_dl_frame, fg_color="#161B22", corner_radius=10,
                              border_width=1, border_color=color)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11),
                          text_color="#8B949E").pack(pady=(10,2), padx=16, anchor="w")
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=26, weight="bold"),
                          text_color=color).pack(padx=16, pady=(0,2), anchor="w")
            ctk.CTkLabel(f, text="downloads", font=ctk.CTkFont(size=10),
                          text_color="#8B949E").pack(padx=16, pady=(0,10), anchor="w")
            f.pack(side="left", expand=True, fill="both", padx=5)

        # Storage prediction cards
        for w in self.pred_st_frame.winfo_children():
            w.destroy()

        st = pred["storage"]
        st_items = [
            ("Current",       f"{st['current_gb']:.1f} GB",    "#FFE66D"),
            ("Next Month",    f"{st['next_month_gb']:.1f} GB",  "#FF8B94"),
            ("Next 3 Months", f"{st['next_3month_gb']:.1f} GB", "#FF6B6B"),
        ]
        for label, val, color in st_items:
            f = ctk.CTkFrame(self.pred_st_frame, fg_color="#161B22", corner_radius=10,
                              border_width=1, border_color=color)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11),
                          text_color="#8B949E").pack(pady=(10,2), padx=16, anchor="w")
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=26, weight="bold"),
                          text_color=color).pack(padx=16, pady=(0,2), anchor="w")
            ctk.CTkLabel(f, text="storage", font=ctk.CTkFont(size=10),
                          text_color="#8B949E").pack(padx=16, pady=(0,10), anchor="w")
            f.pack(side="left", expand=True, fill="both", padx=5)

        # Text report
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("end", report)
        self.text_box.configure(state="disabled")

    def _show_error(self, msg: str):
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("end", f"❌ Prediction error: {msg}")
        self.text_box.configure(state="disabled")
