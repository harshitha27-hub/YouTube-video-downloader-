"""
report_generator.py - Generates CSV, Excel, and PDF reports.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from modules.database import DatabaseManager
from modules.predictor import DownloadPredictor
from modules.logger import logger


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class ReportGenerator:
    """Creates CSV, XLSX, and PDF reports from download history + analytics."""

    def __init__(self):
        self.db        = DatabaseManager()
        self.predictor = DownloadPredictor()
        os.makedirs("reports", exist_ok=True)

    # ── CSV ───────────────────────────────────────────────────────────────────

    def generate_csv(self) -> str:
        """Write all downloads to a CSV file and return its path."""
        downloads = self.db.get_all_downloads()
        path      = os.path.join("reports", f"download_history_{_timestamp()}.csv")

        fieldnames = ["id","video_title","channel","url","file_size","download_date","quality","status","file_type","duration"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(downloads)

        logger.log_report_generated("CSV", path)
        return path

    # ── Excel ─────────────────────────────────────────────────────────────────

    def generate_excel(self) -> str:
        """Write a multi-sheet Excel report and return its path."""
        path      = os.path.join("reports", f"download_report_{_timestamp()}.xlsx")
        downloads = self.db.get_all_downloads()
        stats     = self.db.get_stats()
        pred      = self.predictor.predict_trends()

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Sheet 1 – Full history
            df_hist = pd.DataFrame(downloads)[
                ["id","video_title","channel","file_type","quality","file_size","download_date","status"]
            ]
            df_hist.columns = ["ID","Title","Channel","Type","Quality","Size (MB)","Date","Status"]
            df_hist.to_excel(writer, sheet_name="Download History", index=False)

            # Sheet 2 – Analytics summary
            summary = {
                "Metric":  ["Total Downloads","Total Videos","Total Audio","Storage (GB)","Top Channel"],
                "Value":   [stats["total"], stats["videos"], stats["audios"],
                            round(stats["storage_gb"],2), stats["top_channel"]],
            }
            pd.DataFrame(summary).to_excel(writer, sheet_name="Analytics", index=False)

            # Sheet 3 – Predictions
            p_dl = pred["downloads"]
            p_st = pred["storage"]
            pred_data = {
                "Metric": [
                    "Next Week Downloads","Next Month Downloads","Next 3 Months Downloads",
                    "Current Storage (GB)","Next Month Storage (GB)","Next 3 Months Storage (GB)",
                ],
                "Value": [
                    p_dl["next_week"], p_dl["next_month"], p_dl["next_3months"],
                    p_st["current_gb"], p_st["next_month_gb"], p_st["next_3month_gb"],
                ],
            }
            pd.DataFrame(pred_data).to_excel(writer, sheet_name="Predictions", index=False)

            # Sheet 4 – Top channels
            pd.DataFrame(stats["by_channel"]).rename(
                columns={"channel":"Channel","cnt":"Downloads"}
            ).to_excel(writer, sheet_name="Top Channels", index=False)

        logger.log_report_generated("Excel", path)
        return path

    # ── PDF ───────────────────────────────────────────────────────────────────

    def generate_pdf(self) -> str:
        """Write a styled PDF report and return its path."""
        path     = os.path.join("reports", f"download_report_{_timestamp()}.pdf")
        stats    = self.db.get_stats()
        pred     = self.predictor.predict_trends()
        history  = self.db.get_all_downloads()[:50]   # cap at 50 rows for PDF

        doc      = SimpleDocTemplate(path, pagesize=A4,
                                     rightMargin=0.7*inch, leftMargin=0.7*inch,
                                     topMargin=0.7*inch, bottomMargin=0.7*inch)
        styles   = getSampleStyleSheet()
        story    = []

        # ── Title ──
        title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                     fontSize=22, textColor=colors.HexColor("#0056D6"),
                                     spaceAfter=6, alignment=TA_CENTER)
        story.append(Paragraph("📥 YouTube Downloader – Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                ParagraphStyle("sub", parent=styles["Normal"],
                                               alignment=TA_CENTER, textColor=colors.grey)))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0056D6"), spaceAfter=12))

        # ── Analytics summary table ──
        h_style = ParagraphStyle("H2", parent=styles["Heading2"],
                                  textColor=colors.HexColor("#0056D6"), spaceBefore=12, spaceAfter=6)
        story.append(Paragraph("Analytics Summary", h_style))

        summary_data = [
            ["Metric", "Value"],
            ["Total Downloads",  str(stats["total"])],
            ["Total Videos",     str(stats["videos"])],
            ["Total Audio",      str(stats["audios"])],
            ["Total Storage",    f"{stats['storage_gb']:.2f} GB"],
            ["Top Channel",      stats["top_channel"]],
        ]
        t = Table(summary_data, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#0056D6")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#EEF2FF")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))

        # ── Predictions ──
        story.append(Paragraph("ML Predictions", h_style))
        p_dl = pred["downloads"]
        p_st = pred["storage"]
        pred_data = [
            ["Prediction",                "Value"],
            ["Next Week Downloads",        str(p_dl["next_week"])],
            ["Next Month Downloads",       str(p_dl["next_month"])],
            ["Next 3 Months Downloads",    str(p_dl["next_3months"])],
            ["Next Month Storage",         f"{p_st['next_month_gb']:.2f} GB"],
            ["Next 3 Months Storage",      f"{p_st['next_3month_gb']:.2f} GB"],
            ["Trend",                      pred["trend_dir"]],
        ]
        t2 = Table(pred_data, colWidths=[3*inch, 3*inch])
        t2.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#00897B")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#E0F2F1")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.2*inch))

        # ── Download history ──
        story.append(Paragraph("Recent Download History (last 50)", h_style))
        hist_header = ["#", "Title", "Channel", "Type", "Quality", "Size (MB)", "Date"]
        hist_rows   = [hist_header] + [
            [str(d["id"]),
             d["video_title"][:30] + ("…" if len(d["video_title"])>30 else ""),
             d["channel"][:20],
             d["file_type"],
             d["quality"],
             f"{d['file_size']:.1f}",
             d["download_date"][:10]]
            for d in history
        ]
        col_widths = [0.35*inch, 2.2*inch, 1.3*inch, 0.6*inch, 0.7*inch, 0.8*inch, 1.1*inch]
        t3 = Table(hist_rows, colWidths=col_widths, repeatRows=1)
        t3.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#333333")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F5F5F5")]),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#DDDDDD")),
            ("WORDWRAP",    (1,1), (1,-1), True),
        ]))
        story.append(t3)

        doc.build(story)
        logger.log_report_generated("PDF", path)
        return path
