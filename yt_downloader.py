"""
yt_downloader.py - Core YouTube download engine using yt-dlp.
Supports video, audio-only, and playlist downloads with progress callbacks.
"""

import os
import threading
from typing import Callable, Optional, Dict
import yt_dlp

from modules.logger import logger
from modules.database import DatabaseManager


# Quality → yt-dlp format string
QUALITY_MAP = {
    "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "best":  "bestvideo+bestaudio/best",
}


class DownloadTask:
    """Represents a single download job with pause/resume/cancel support."""

    def __init__(
        self,
        url: str,
        quality: str = "best",
        file_type: str = "video",          # "video" | "audio"
        output_dir: str = "downloads",
        progress_cb: Optional[Callable[[Dict], None]] = None,
        complete_cb: Optional[Callable[[Dict], None]] = None,
        error_cb: Optional[Callable[[str], None]] = None,
    ):
        self.url         = url
        self.quality     = quality
        self.file_type   = file_type
        self.output_dir  = output_dir
        self.progress_cb = progress_cb
        self.complete_cb = complete_cb
        self.error_cb    = error_cb

        self._paused    = False
        self._cancelled = False
        self._thread: Optional[threading.Thread] = None

        self.info: Dict = {}    # video metadata filled after fetch
        self.db = DatabaseManager()

        os.makedirs(output_dir, exist_ok=True)

    # ── Controls ──────────────────────────────────────────────────────────────

    def pause(self):
        self._paused = True
        logger.info(f"Download PAUSED: {self.url}")

    def resume(self):
        self._paused = False
        logger.info(f"Download RESUMED: {self.url}")

    def cancel(self):
        self._cancelled = True
        logger.info(f"Download CANCELLED: {self.url}")

    # ── Internal progress hook ────────────────────────────────────────────────

    def _progress_hook(self, d: Dict):
        """Called by yt-dlp on every progress update."""
        if self._cancelled:
            raise yt_dlp.utils.DownloadError("Cancelled by user")

        # Busy-wait while paused (checked ~every 0.5 s by yt-dlp)
        while self._paused and not self._cancelled:
            import time; time.sleep(0.5)

        if self.progress_cb:
            self.progress_cb(d)

    # ── Fetch metadata only ───────────────────────────────────────────────────

    def fetch_info(self) -> Optional[Dict]:
        """Return video metadata without downloading."""
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info = {
                    "title":     info.get("title", "Unknown"),
                    "channel":   info.get("uploader", "Unknown"),
                    "duration":  self._fmt_duration(info.get("duration", 0)),
                    "thumbnail": info.get("thumbnail", ""),
                    "url":       self.url,
                    "playlist":  info.get("_type") == "playlist",
                    "entries":   info.get("entries", []),
                }
                return self.info
        except Exception as exc:
            logger.error(f"fetch_info failed for {self.url}: {exc}")
            return None

    @staticmethod
    def _fmt_duration(seconds: int) -> str:
        h, rem = divmod(int(seconds), 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # ── Build yt-dlp options ──────────────────────────────────────────────────

    def _build_opts(self) -> Dict:
        tmpl = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        if self.file_type == "audio":
            opts = {
                "format": "bestaudio/best",
                "outtmpl": tmpl,
                "postprocessors": [{
                    "key":            "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            opts = {
                "format":  QUALITY_MAP.get(self.quality, QUALITY_MAP["best"]),
                "outtmpl": tmpl,
                "merge_output_format": "mp4",
            }

        opts.update({
            "progress_hooks": [self._progress_hook],
            "quiet":          True,
            "no_warnings":    True,
        })
        return opts

    # ── Download ──────────────────────────────────────────────────────────────

    def start(self):
        """Start the download in the current thread (call from a worker thread)."""
        try:
            logger.log_download_start(
                self.info.get("title", self.url), self.url, self.quality
            )
            opts = self._build_opts()

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

            if self._cancelled:
                return

            # Estimate file size from info dict
            file_size_mb = 0.0
            try:
                file_size_mb = (info.get("filesize") or info.get("filesize_approx") or 0) / (1024 * 1024)
            except Exception:
                pass

            title   = info.get("title", "Unknown")
            channel = info.get("uploader", "Unknown")
            dur     = self._fmt_duration(info.get("duration", 0))
            thumb   = info.get("thumbnail", "")

            # Persist to DB
            self.db.add_download(
                video_title=title,
                channel=channel,
                url=self.url,
                file_size=file_size_mb,
                quality=self.quality,
                status="completed",
                file_type=self.file_type,
                duration=dur,
                thumbnail=thumb,
            )

            logger.log_download_complete(title, file_size_mb)

            if self.complete_cb:
                self.complete_cb({
                    "title":    title,
                    "channel":  channel,
                    "size_mb":  file_size_mb,
                    "duration": dur,
                    "quality":  self.quality,
                    "type":     self.file_type,
                })

        except yt_dlp.utils.DownloadError as exc:
            if not self._cancelled:
                logger.log_download_error(self.url, str(exc))
                if self.error_cb:
                    self.error_cb(str(exc))
        except Exception as exc:
            logger.log_download_error(self.url, str(exc))
            if self.error_cb:
                self.error_cb(str(exc))

    def start_async(self):
        """Launch download in a background thread."""
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        return self._thread


class PlaylistDownloader:
    """Downloads every video in a playlist sequentially."""

    def __init__(
        self,
        url: str,
        quality: str = "best",
        file_type: str = "video",
        output_dir: str = "downloads",
        item_cb: Optional[Callable[[int, int, str], None]] = None,   # (done, total, title)
        complete_cb: Optional[Callable[[], None]] = None,
        error_cb: Optional[Callable[[str], None]] = None,
    ):
        self.url        = url
        self.quality    = quality
        self.file_type  = file_type
        self.output_dir = output_dir
        self.item_cb    = item_cb
        self.complete_cb= complete_cb
        self.error_cb   = error_cb
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def start(self):
        """Fetch playlist entries then download each one."""
        probe_opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
        try:
            with yt_dlp.YoutubeDL(probe_opts) as ydl:
                info    = ydl.extract_info(self.url, download=False)
                entries = info.get("entries", [])
        except Exception as exc:
            if self.error_cb:
                self.error_cb(str(exc))
            return

        total = len(entries)
        for idx, entry in enumerate(entries, 1):
            if self._cancelled:
                break
            entry_url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id','')}"
            title     = entry.get("title", f"Video {idx}")
            if self.item_cb:
                self.item_cb(idx, total, title)

            task = DownloadTask(
                url=entry_url,
                quality=self.quality,
                file_type=self.file_type,
                output_dir=self.output_dir,
            )
            task.info = {"title": title, "channel": info.get("uploader", "Unknown")}
            task.start()

        if self.complete_cb and not self._cancelled:
            self.complete_cb()

    def start_async(self) -> threading.Thread:
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        return t
