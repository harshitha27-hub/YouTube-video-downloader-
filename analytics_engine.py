"""
analytics_engine.py - Generates Plotly charts from database stats.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List

from modules.database import DatabaseManager
from modules.logger import logger


class AnalyticsEngine:
    """Builds interactive Plotly figures from download data."""

    def __init__(self):
        self.db = DatabaseManager()

    # ── Colour palette ────────────────────────────────────────────────────────
    PALETTE = ["#00D4FF", "#FF6B6B", "#4ECDC4", "#FFE66D", "#A8E6CF",
               "#FF8B94", "#B8B5FF", "#FFA07A", "#98FB98", "#DDA0DD"]

    DARK_BG = "#0D1117"
    CARD_BG = "#161B22"
    TEXT    = "#E6EDF3"

    def _dark_layout(self, title: str = "") -> Dict:
        return dict(
            title=dict(text=title, font=dict(color=self.TEXT, size=16)),
            paper_bgcolor=self.DARK_BG,
            plot_bgcolor =self.CARD_BG,
            font=dict(color=self.TEXT),
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=self.TEXT)),
        )

    # ── Individual charts ─────────────────────────────────────────────────────

    def downloads_trend_chart(self) -> go.Figure:
        """Line chart – daily downloads over the last 30 days."""
        stats = self.db.get_stats()
        trend = stats.get("trend", [])

        if not trend:
            fig = go.Figure()
            fig.update_layout(**self._dark_layout("No data yet"))
            return fig

        df = pd.DataFrame(trend)
        fig = go.Figure(
            go.Scatter(
                x=df["day"], y=df["cnt"],
                mode="lines+markers",
                line=dict(color="#00D4FF", width=2),
                marker=dict(size=6, color="#00D4FF"),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.15)",
            )
        )
        fig.update_layout(**self._dark_layout("📈 Download Activity (Last 30 Days)"))
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="#21262D")
        return fig

    def channel_bar_chart(self) -> go.Figure:
        """Horizontal bar chart – top 10 channels by download count."""
        stats    = self.db.get_stats()
        by_ch    = stats.get("by_channel", [])

        if not by_ch:
            fig = go.Figure()
            fig.update_layout(**self._dark_layout("No data yet"))
            return fig

        df  = pd.DataFrame(by_ch)
        fig = go.Figure(
            go.Bar(
                x=df["cnt"], y=df["channel"],
                orientation="h",
                marker=dict(color=self.PALETTE[:len(df)]),
                text=df["cnt"], textposition="outside",
            )
        )
        fig.update_layout(**self._dark_layout("🏆 Top Channels"))
        fig.update_xaxes(gridcolor="#21262D")
        fig.update_yaxes(showgrid=False)
        return fig

    def quality_pie_chart(self) -> go.Figure:
        """Pie chart – downloads by quality."""
        stats    = self.db.get_stats()
        by_qual  = stats.get("by_quality", [])

        if not by_qual:
            fig = go.Figure()
            fig.update_layout(**self._dark_layout("No data yet"))
            return fig

        df  = pd.DataFrame(by_qual)
        fig = go.Figure(
            go.Pie(
                labels=df["quality"], values=df["cnt"],
                marker=dict(colors=self.PALETTE),
                hole=0.4,
            )
        )
        fig.update_layout(**self._dark_layout("🎯 Downloads by Quality"))
        return fig

    def type_donut_chart(self) -> go.Figure:
        """Donut chart – video vs audio split."""
        stats   = self.db.get_stats()
        by_type = stats.get("by_type", [])

        if not by_type:
            fig = go.Figure()
            fig.update_layout(**self._dark_layout("No data yet"))
            return fig

        df  = pd.DataFrame(by_type)
        fig = go.Figure(
            go.Pie(
                labels=df["file_type"], values=df["cnt"],
                marker=dict(colors=["#00D4FF", "#FF6B6B"]),
                hole=0.55,
            )
        )
        fig.update_layout(**self._dark_layout("🎵 Video vs Audio"))
        return fig

    def combined_dashboard(self) -> go.Figure:
        """2×2 subplot combining all four charts."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Activity Trend", "Top Channels", "Quality Split", "Type Split"),
            specs=[
                [{"type": "xy"},  {"type": "xy"}],
                [{"type": "pie"}, {"type": "pie"}],
            ],
        )

        stats    = self.db.get_stats()

        # -- Trend
        trend = stats.get("trend", [])
        if trend:
            df_t = pd.DataFrame(trend)
            fig.add_trace(go.Scatter(x=df_t["day"], y=df_t["cnt"],
                                     mode="lines+markers", line=dict(color="#00D4FF"),
                                     fill="tozeroy", fillcolor="rgba(0,212,255,0.15)"),
                          row=1, col=1)

        # -- Channels
        by_ch = stats.get("by_channel", [])[:8]
        if by_ch:
            df_c = pd.DataFrame(by_ch)
            fig.add_trace(go.Bar(x=df_c["cnt"], y=df_c["channel"],
                                  orientation="h", marker=dict(color=self.PALETTE[:len(df_c)])),
                          row=1, col=2)

        # -- Quality
        by_q = stats.get("by_quality", [])
        if by_q:
            df_q = pd.DataFrame(by_q)
            fig.add_trace(go.Pie(labels=df_q["quality"], values=df_q["cnt"],
                                  marker=dict(colors=self.PALETTE), hole=0.4, showlegend=False),
                          row=2, col=1)

        # -- Type
        by_tp = stats.get("by_type", [])
        if by_tp:
            df_tp = pd.DataFrame(by_tp)
            fig.add_trace(go.Pie(labels=df_tp["file_type"], values=df_tp["cnt"],
                                  marker=dict(colors=["#00D4FF","#FF6B6B"]), hole=0.4, showlegend=False),
                          row=2, col=2)

        fig.update_layout(
            paper_bgcolor=self.DARK_BG,
            plot_bgcolor =self.CARD_BG,
            font=dict(color=self.TEXT),
            height=700,
            showlegend=False,
            margin=dict(l=40, r=40, t=80, b=40),
        )
        return fig

    def save_chart_html(self, fig: go.Figure, filename: str) -> str:
        """Save a chart as a standalone HTML file and return the path."""
        os.makedirs("reports", exist_ok=True)
        path = os.path.join("reports", filename)
        fig.write_html(path)
        return path


import os  # placed here to avoid circular at top level
