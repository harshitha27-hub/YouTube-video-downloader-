"""
logger.py - Centralized logging system for YouTube Downloader
Handles download logs, error logs, and user action logs.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class AppLogger:
    """Centralized logger with rotating file handler and console output."""

    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # --- Main application logger ---
        self.logger = logging.getLogger("YTDownloader")
        self.logger.setLevel(logging.DEBUG)

        # Formatter
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Rotating file handler (5 MB per file, keep 3 backups)
        fh = RotatingFileHandler(
            "logs/download.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)

        # Console handler (INFO and above)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

    # ── Domain helpers ────────────────────────────────────────────────────────

    def log_download_start(self, title: str, url: str, quality: str):
        self.info(f"DOWNLOAD START | Title: '{title}' | Quality: {quality} | URL: {url}")

    def log_download_complete(self, title: str, file_size: float):
        self.info(f"DOWNLOAD COMPLETE | Title: '{title}' | Size: {file_size:.2f} MB")

    def log_download_error(self, url: str, error: str):
        self.error(f"DOWNLOAD ERROR | URL: {url} | Error: {error}")

    def log_user_action(self, action: str, details: str = ""):
        self.info(f"USER ACTION | {action}" + (f" | {details}" if details else ""))

    def log_db_operation(self, operation: str, details: str = ""):
        self.debug(f"DB | {operation}" + (f" | {details}" if details else ""))

    def log_report_generated(self, report_type: str, path: str):
        self.info(f"REPORT GENERATED | Type: {report_type} | Path: {path}")


# Module-level singleton for easy import
logger = AppLogger()
