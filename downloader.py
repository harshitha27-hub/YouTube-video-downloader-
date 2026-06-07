"""
gui/downloader.py - YouTube download page with URL input, metadata preview, and progress tracking.
"""

import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from modules.yt_downloader import DownloadTask, PlaylistDownloader
from modules.logger import logger


QUALITY_OPTIONS = ["best", "1080p", "720p", "360p"]
TYPE_OPTIONS    = ["video", "audio"]


class DownloaderPage(ctk.CTkFrame):
    """Page for entering URLs and managing active downloads."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self._active_tasks: list[DownloadTask] = []
        self._output_dir = "downloads"
        self._build_ui()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Downloader",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(side="left")

        # ── URL Input card ──
        url_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                                 border_width=1, border_color="#30363D")
        url_card.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(url_card, text="YouTube URL",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8B949E").pack(anchor="w", padx=16, pady=(14, 4))

        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=(0, 14))

        self.url_entry = ctk.CTkEntry(
            url_row, placeholder_text="https://www.youtube.com/watch?v=...",
            height=40, font=ctk.CTkFont(size=13),
            fg_color="#0D1117", border_color="#30363D", text_color="#E6EDF3",
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.fetch_btn = ctk.CTkButton(
            url_row, text="🔍 Fetch Info", width=120, height=40,
            fg_color="#238636", hover_color="#2EA043", command=self._fetch_info,
        )
        self.fetch_btn.pack(side="left")

        # ── Options row ──
        opt_row = ctk.CTkFrame(url_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(opt_row, text="Quality:", text_color="#8B949E").pack(side="left", padx=(0,6))
        self.quality_var = ctk.StringVar(value="best")
        ctk.CTkOptionMenu(opt_row, values=QUALITY_OPTIONS,
                           variable=self.quality_var,
                           fg_color="#21262D", button_color="#30363D",
                           dropdown_fg_color="#161B22",
                           text_color="#E6EDF3", width=100).pack(side="left", padx=(0, 20))

        ctk.CTkLabel(opt_row, text="Type:", text_color="#8B949E").pack(side="left", padx=(0,6))
        self.type_var = ctk.StringVar(value="video")
        ctk.CTkOptionMenu(opt_row, values=TYPE_OPTIONS,
                           variable=self.type_var,
                           fg_color="#21262D", button_color="#30363D",
                           dropdown_fg_color="#161B22",
                           text_color="#E6EDF3", width=100).pack(side="left", padx=(0, 20))

        self.folder_btn = ctk.CTkButton(
            opt_row, text="📁 Output Folder", width=140, height=32,
            fg_color="#21262D", hover_color="#30363D", text_color="#8B949E",
            command=self._choose_folder,
        )
        self.folder_btn.pack(side="left")
        self.folder_lbl = ctk.CTkLabel(opt_row, text="downloads/",
                                        text_color="#8B949E", font=ctk.CTkFont(size=11))
        self.folder_lbl.pack(side="left", padx=8)

        # ── Metadata preview card ──
        self.meta_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                                       border_width=1, border_color="#30363D")
        self.meta_card.pack(fill="x", padx=20, pady=8)

        self.meta_lbl = ctk.CTkLabel(
            self.meta_card,
            text="Enter a URL and click Fetch Info to preview video details.",
            text_color="#8B949E", font=ctk.CTkFont(size=12),
            wraplength=700, justify="left",
        )
        self.meta_lbl.pack(padx=16, pady=16)

        self.dl_btn = ctk.CTkButton(
            self.meta_card, text="⬇ Download", width=150, height=40,
            fg_color="#0056D6", hover_color="#0969DA",
            state="disabled", command=self._start_download,
        )
        self.dl_btn.pack(padx=16, pady=(0, 16), anchor="e")

        # ── Active downloads area ──
        ctk.CTkLabel(self, text="Active Downloads",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#E6EDF3").pack(anchor="w", padx=26, pady=(12, 4))

        self.dl_scroll = ctk.CTkScrollableFrame(self, fg_color="#161B22", height=280)
        self.dl_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._no_dl_lbl = ctk.CTkLabel(self.dl_scroll,
                                        text="No active downloads.",
                                        text_color="#8B949E")
        self._no_dl_lbl.pack(pady=20)

        # Store current fetched info
        self._current_info: dict | None = None

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _choose_folder(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self._output_dir = path
            self.folder_lbl.configure(text=path[-40:] if len(path) > 40 else path)

    def _fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a YouTube URL.")
            return

        self.fetch_btn.configure(state="disabled", text="Fetching…")
        self.meta_lbl.configure(text="⏳ Fetching video information…", text_color="#FFE66D")
        self.dl_btn.configure(state="disabled")
        threading.Thread(target=self._do_fetch, args=(url,), daemon=True).start()

    def _do_fetch(self, url: str):
        task = DownloadTask(url=url, output_dir=self._output_dir)
        info = task.fetch_info()
        self.after(0, self._show_info, info, task)

    def _show_info(self, info: dict | None, task: DownloadTask):
        self.fetch_btn.configure(state="normal", text="🔍 Fetch Info")
        if not info:
            self.meta_lbl.configure(text="❌ Could not fetch video info. Check the URL.", text_color="#FF6B6B")
            return

        self._current_info = info
        is_playlist = info.get("playlist", False)
        entries     = info.get("entries", [])

        if is_playlist:
            text = (f"📋 PLAYLIST: {info['title']}\n"
                    f"Channel: {info['channel']}   |   Videos: {len(entries)}\n"
                    f"(All {len(entries)} videos will be downloaded)")
        else:
            text = (f"🎬 {info['title']}\n"
                    f"📺 Channel: {info['channel']}   |   ⏱ Duration: {info['duration']}")

        self.meta_lbl.configure(text=text, text_color="#E6EDF3")
        self.dl_btn.configure(state="normal")

    def _start_download(self):
        if not self._current_info:
            return

        url      = self.url_entry.get().strip()
        quality  = self.quality_var.get()
        ftype    = self.type_var.get()
        is_pl    = self._current_info.get("playlist", False)

        # Build a progress widget row
        row = DownloadRow(self.dl_scroll, url, self._current_info.get("title", url))
        row.pack(fill="x", padx=8, pady=4)
        self._no_dl_lbl.pack_forget()
        self._active_tasks.append(row)

        if is_pl:
            dl = PlaylistDownloader(
                url=url, quality=quality, file_type=ftype,
                output_dir=self._output_dir,
                item_cb=lambda done, total, t: self.after(
                    0, row.set_playlist_progress, done, total, t),
                complete_cb=lambda: self.after(0, row.set_complete),
                error_cb=lambda e: self.after(0, row.set_error, e),
            )
            row.set_canceller(dl.cancel)
            dl.start_async()
        else:
            task = DownloadTask(
                url=url, quality=quality, file_type=ftype,
                output_dir=self._output_dir,
                progress_cb=lambda d: self.after(0, row.update_progress, d),
                complete_cb=lambda _: self.after(0, row.set_complete),
                error_cb=lambda e: self.after(0, row.set_error, e),
            )
            task.info = self._current_info
            row.set_canceller(task.cancel)
            row.set_pauser(task.pause)
            row.set_resumer(task.resume)
            task.start_async()

        # Reset UI
        self.dl_btn.configure(state="disabled")
        self.meta_lbl.configure(
            text="Enter a URL and click Fetch Info to preview video details.",
            text_color="#8B949E",
        )
        self._current_info = None
        logger.log_user_action("Start Download", url)


# ── Individual download row widget ────────────────────────────────────────────

class DownloadRow(ctk.CTkFrame):
    """Shows progress, speed, ETA, and controls for one download."""

    def __init__(self, parent, url: str, title: str, **kwargs):
        super().__init__(parent, fg_color="#0D1117", corner_radius=8,
                          border_width=1, border_color="#21262D", **kwargs)
        self._url      = url
        self._paused   = False
        self._cancel_fn = None
        self._pause_fn  = None
        self._resume_fn = None

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 2))

        self.title_lbl = ctk.CTkLabel(top, text=title[:70] + ("…" if len(title) > 70 else ""),
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color="#E6EDF3", anchor="w")
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Controls
        ctrl = ctk.CTkFrame(top, fg_color="transparent")
        ctrl.pack(side="right")

        self.pause_btn = ctk.CTkButton(ctrl, text="⏸", width=32, height=28,
                                        fg_color="#21262D", hover_color="#30363D",
                                        command=self._toggle_pause)
        self.pause_btn.pack(side="left", padx=2)

        self.cancel_btn = ctk.CTkButton(ctrl, text="✕", width=32, height=28,
                                         fg_color="#3D1F1F", hover_color="#5A2020",
                                         text_color="#FF6B6B",
                                         command=self._cancel)
        self.cancel_btn.pack(side="left", padx=2)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, height=8,
                                            fg_color="#21262D", progress_color="#00D4FF")
        self.progress.set(0)
        self.progress.pack(fill="x", padx=12, pady=4)

        # Status row
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=12, pady=(0, 10))

        self.pct_lbl   = ctk.CTkLabel(bot, text="0%",   font=ctk.CTkFont(size=11),
                                       text_color="#8B949E")
        self.speed_lbl = ctk.CTkLabel(bot, text="",     font=ctk.CTkFont(size=11),
                                       text_color="#8B949E")
        self.eta_lbl   = ctk.CTkLabel(bot, text="",     font=ctk.CTkFont(size=11),
                                       text_color="#8B949E")
        self.status_lbl= ctk.CTkLabel(bot, text="Starting…", font=ctk.CTkFont(size=11),
                                       text_color="#FFE66D")

        self.pct_lbl.pack(side="left")
        self.speed_lbl.pack(side="left", padx=12)
        self.eta_lbl.pack(side="left")
        self.status_lbl.pack(side="right")

    # ── Wiring controls ───────────────────────────────────────────────────────

    def set_canceller(self, fn): self._cancel_fn = fn
    def set_pauser(self, fn):   self._pause_fn  = fn
    def set_resumer(self, fn):  self._resume_fn = fn

    def _toggle_pause(self):
        if not self._paused:
            if self._pause_fn: self._pause_fn()
            self._paused = True
            self.pause_btn.configure(text="▶")
            self.status_lbl.configure(text="Paused", text_color="#FFE66D")
        else:
            if self._resume_fn: self._resume_fn()
            self._paused = False
            self.pause_btn.configure(text="⏸")
            self.status_lbl.configure(text="Downloading…", text_color="#00D4FF")

    def _cancel(self):
        if self._cancel_fn: self._cancel_fn()
        self.set_cancelled()

    # ── State updates ─────────────────────────────────────────────────────────

    def update_progress(self, d: dict):
        status = d.get("status", "")
        if status == "downloading":
            pct  = d.get("downloaded_bytes", 0) / (d.get("total_bytes") or d.get("total_bytes_estimate") or 1)
            pct  = min(pct, 1.0)
            speed = d.get("speed") or 0
            eta   = d.get("eta") or 0

            self.progress.set(pct)
            self.pct_lbl.configure(text=f"{pct*100:.1f}%")
            self.speed_lbl.configure(text=f"{speed/1024/1024:.2f} MB/s" if speed else "")
            self.eta_lbl.configure(text=f"ETA: {eta}s" if eta else "")
            self.status_lbl.configure(text="Downloading…", text_color="#00D4FF")

    def set_playlist_progress(self, done: int, total: int, title: str):
        pct = done / total if total else 0
        self.progress.set(pct)
        self.pct_lbl.configure(text=f"{done}/{total}")
        self.status_lbl.configure(text=f"Downloading: {title[:40]}", text_color="#00D4FF")

    def set_complete(self):
        self.progress.set(1.0)
        self.progress.configure(progress_color="#4ECDC4")
        self.status_lbl.configure(text="✅ Complete", text_color="#4ECDC4")
        self.pct_lbl.configure(text="100%")
        self.pause_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")

    def set_error(self, msg: str):
        self.progress.configure(progress_color="#FF6B6B")
        self.status_lbl.configure(text=f"❌ Error: {msg[:60]}", text_color="#FF6B6B")
        self.pause_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")

    def set_cancelled(self):
        self.progress.configure(progress_color="#8B949E")
        self.status_lbl.configure(text="Cancelled", text_color="#8B949E")
        self.pause_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
