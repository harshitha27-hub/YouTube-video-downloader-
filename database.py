"""
database.py - SQLite database manager for YouTube Downloader.
Handles all CRUD operations for download history.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from modules.logger import logger


class DatabaseManager:
    """Manages the SQLite database for storing download records."""

    DB_PATH = os.path.join("database", "downloads.db")

    def __init__(self):
        os.makedirs("database", exist_ok=True)
        self._init_db()
        logger.log_db_operation("DatabaseManager initialized", self.DB_PATH)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new connection with row factory enabled."""
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        ddl = """
        CREATE TABLE IF NOT EXISTS downloads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            video_title TEXT    NOT NULL,
            channel     TEXT    NOT NULL DEFAULT 'Unknown',
            url         TEXT    NOT NULL,
            file_size   REAL    NOT NULL DEFAULT 0.0,
            download_date TEXT  NOT NULL,
            quality     TEXT    NOT NULL DEFAULT 'best',
            status      TEXT    NOT NULL DEFAULT 'completed',
            file_type   TEXT    NOT NULL DEFAULT 'video',
            duration    TEXT             DEFAULT '00:00',
            thumbnail   TEXT             DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
        with self._get_connection() as conn:
            conn.executescript(ddl)
        logger.log_db_operation("Schema initialized")

    # ── Write operations ──────────────────────────────────────────────────────

    def add_download(
        self,
        video_title: str,
        channel: str,
        url: str,
        file_size: float,
        quality: str,
        status: str = "completed",
        file_type: str = "video",
        duration: str = "00:00",
        thumbnail: str = "",
    ) -> int:
        """Insert a new download record and return its row id."""
        sql = """
        INSERT INTO downloads
            (video_title, channel, url, file_size, download_date, quality, status, file_type, duration, thumbnail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cur = conn.execute(sql, (video_title, channel, url, file_size, now, quality, status, file_type, duration, thumbnail))
            row_id = cur.lastrowid
        logger.log_db_operation("INSERT download", f"id={row_id}, title='{video_title}'")
        return row_id

    def update_status(self, download_id: int, status: str):
        """Update the status of an existing download record."""
        with self._get_connection() as conn:
            conn.execute("UPDATE downloads SET status=? WHERE id=?", (status, download_id))
        logger.log_db_operation("UPDATE status", f"id={download_id}, status={status}")

    def delete_download(self, download_id: int):
        """Delete a download record by id."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM downloads WHERE id=?", (download_id,))
        logger.log_db_operation("DELETE download", f"id={download_id}")

    # ── Read operations ───────────────────────────────────────────────────────

    def get_all_downloads(self) -> List[Dict]:
        """Return all downloads ordered by most recent first."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM downloads ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def search_downloads(
        self,
        query: str = "",
        channel: str = "",
        file_type: str = "",
        quality: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict]:
        """Flexible search / filter over downloads table."""
        conditions, params = [], []

        if query:
            conditions.append("(video_title LIKE ? OR channel LIKE ?)")
            params += [f"%{query}%", f"%{query}%"]
        if channel:
            conditions.append("channel = ?")
            params.append(channel)
        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)
        if quality:
            conditions.append("quality = ?")
            params.append(quality)
        if date_from:
            conditions.append("download_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("download_date <= ?")
            params.append(date_to + " 23:59:59")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"SELECT * FROM downloads {where} ORDER BY id DESC"

        with self._get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ── Analytics queries ─────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Return aggregate statistics used by the dashboard."""
        with self._get_connection() as conn:
            total      = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
            videos     = conn.execute("SELECT COUNT(*) FROM downloads WHERE file_type='video'").fetchone()[0]
            audios     = conn.execute("SELECT COUNT(*) FROM downloads WHERE file_type='audio'").fetchone()[0]
            storage_mb = conn.execute("SELECT COALESCE(SUM(file_size),0) FROM downloads").fetchone()[0]

            top_ch_row = conn.execute(
                "SELECT channel, COUNT(*) AS cnt FROM downloads GROUP BY channel ORDER BY cnt DESC LIMIT 1"
            ).fetchone()
            top_channel = top_ch_row["channel"] if top_ch_row else "N/A"

            # Downloads per day (last 30 days)
            trend_rows = conn.execute(
                """SELECT DATE(download_date) AS day, COUNT(*) AS cnt
                   FROM downloads
                   WHERE download_date >= DATE('now','-30 days')
                   GROUP BY day ORDER BY day"""
            ).fetchall()

            # Downloads by channel
            channel_rows = conn.execute(
                """SELECT channel, COUNT(*) AS cnt
                   FROM downloads
                   GROUP BY channel ORDER BY cnt DESC LIMIT 10"""
            ).fetchall()

            # Downloads by quality
            quality_rows = conn.execute(
                """SELECT quality, COUNT(*) AS cnt
                   FROM downloads GROUP BY quality"""
            ).fetchall()

            # Downloads by type
            type_rows = conn.execute(
                """SELECT file_type, COUNT(*) AS cnt
                   FROM downloads GROUP BY file_type"""
            ).fetchall()

        return {
            "total":        total,
            "videos":       videos,
            "audios":       audios,
            "storage_mb":   storage_mb,
            "storage_gb":   storage_mb / 1024,
            "top_channel":  top_channel,
            "trend":        [dict(r) for r in trend_rows],
            "by_channel":   [dict(r) for r in channel_rows],
            "by_quality":   [dict(r) for r in quality_rows],
            "by_type":      [dict(r) for r in type_rows],
        }

    def get_distinct_channels(self) -> List[str]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT DISTINCT channel FROM downloads ORDER BY channel").fetchall()
        return [r[0] for r in rows]

    def get_monthly_counts(self) -> List[Dict]:
        """Return monthly download counts for ML prediction."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT STRFTIME('%Y-%m', download_date) AS month, COUNT(*) AS cnt
                   FROM downloads GROUP BY month ORDER BY month"""
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    # ── Seed / demo data ──────────────────────────────────────────────────────

    def seed_demo_data(self):
        """Insert sample records so the dashboard isn't empty on first run."""
        import random, calendar
        channels   = ["Tech Channel", "Python Academy", "Music World", "Science Hub", "Gaming Zone", "Edu Talks"]
        qualities  = ["360p", "720p", "1080p", "best"]
        file_types = ["video", "video", "video", "audio"]  # weighted toward video
        titles_v   = ["Python Tutorial", "AI Revolution", "Web Dev Crash Course", "Linux Tips", "Cloud Computing",
                      "Machine Learning Basics", "Docker & Kubernetes", "Data Science 101", "React Deep Dive", "DevOps Essentials"]
        titles_a   = ["Chill Beats", "Lo-Fi Mix", "Study Music", "Focus Playlist", "Ambient Sounds"]

        with self._get_connection() as conn:
            existing = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]

        if existing > 0:
            return  # Don't seed if data exists

        records = []
        for i in range(180):
            ft      = random.choice(file_types)
            title   = random.choice(titles_v if ft == "video" else titles_a)
            channel = random.choice(channels)
            quality = random.choice(qualities)
            size_mb = round(random.uniform(50 if ft=="video" else 5, 800 if ft=="video" else 15), 2)
            # Spread over past 6 months
            days_ago = random.randint(0, 180)
            from datetime import timedelta
            dt = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            records.append((title, channel, f"https://youtube.com/watch?v=demo{i}", size_mb, dt, quality, "completed", ft, "03:45", ""))

        with self._get_connection() as conn:
            conn.executemany(
                "INSERT INTO downloads(video_title,channel,url,file_size,download_date,quality,status,file_type,duration,thumbnail) VALUES(?,?,?,?,?,?,?,?,?,?)",
                records,
            )
        logger.log_db_operation("Seeded demo data", f"{len(records)} records")
