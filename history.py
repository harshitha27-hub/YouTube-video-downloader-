"""
gui/history.py - Download history page with search and filter capabilities.
"""

import customtkinter as ctk
import threading
from tkinter import ttk, messagebox
from modules.database import DatabaseManager
from modules.logger import logger


class HistoryPage(ctk.CTkFrame):
    """Displays all downloaded items with search and filter controls."""

    COLS = ("ID", "Title", "Channel", "Type", "Quality", "Size (MB)", "Date", "Status")

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color="transparent")
        self.db = DatabaseManager()
        self._all_records: list[dict] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(hdr, text="History",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#E6EDF3").pack(side="left")
        ctk.CTkButton(hdr, text="⟳ Refresh", width=100, height=36,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#00D4FF", command=self.refresh).pack(side="right")

        # Search / Filter card
        filter_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12,
                                    border_width=1, border_color="#30363D")
        filter_card.pack(fill="x", padx=20, pady=8)

        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 4))

        self.search_entry = ctk.CTkEntry(
            row1, placeholder_text="🔍 Search title or channel…",
            height=36, font=ctk.CTkFont(size=12),
            fg_color="#0D1117", border_color="#30363D", text_color="#E6EDF3", width=300,
        )
        self.search_entry.pack(side="left", padx=(0, 12))
        self.search_entry.bind("<Return>", lambda _: self._apply_filter())
        self.search_entry.bind("<KeyRelease>", lambda _: self._apply_filter())

        # Filter dropdowns
        self.channel_var = ctk.StringVar(value="All Channels")
        self.type_var    = ctk.StringVar(value="All Types")
        self.quality_var = ctk.StringVar(value="All Qualities")

        self._ch_menu = ctk.CTkOptionMenu(row1, variable=self.channel_var,
                                           values=["All Channels"],
                                           fg_color="#21262D", button_color="#30363D",
                                           dropdown_fg_color="#161B22", text_color="#E6EDF3",
                                           width=160, command=lambda _: self._apply_filter())
        self._ch_menu.pack(side="left", padx=4)

        ctk.CTkOptionMenu(row1, variable=self.type_var,
                           values=["All Types","video","audio"],
                           fg_color="#21262D", button_color="#30363D",
                           dropdown_fg_color="#161B22", text_color="#E6EDF3",
                           width=120, command=lambda _: self._apply_filter()).pack(side="left", padx=4)

        ctk.CTkOptionMenu(row1, variable=self.quality_var,
                           values=["All Qualities","best","1080p","720p","360p"],
                           fg_color="#21262D", button_color="#30363D",
                           dropdown_fg_color="#161B22", text_color="#E6EDF3",
                           width=130, command=lambda _: self._apply_filter()).pack(side="left", padx=4)

        ctk.CTkButton(row1, text="Clear", width=70, height=32,
                       fg_color="#21262D", hover_color="#30363D",
                       text_color="#8B949E", command=self._clear_filters).pack(side="left", padx=4)

        # Result count label
        self.count_lbl = ctk.CTkLabel(filter_card, text="",
                                       text_color="#8B949E", font=ctk.CTkFont(size=11))
        self.count_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # Table frame
        table_frame = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Treeview (native Tk widget styled dark)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
                         background="#0D1117", foreground="#E6EDF3",
                         fieldbackground="#0D1117", rowheight=28,
                         borderwidth=0, font=("Consolas", 10))
        style.configure("Dark.Treeview.Heading",
                         background="#161B22", foreground="#8B949E",
                         borderwidth=0, relief="flat", font=("Arial", 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", "#1F6FEB")])

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            table_frame, columns=self.COLS, show="headings",
            style="Dark.Treeview", yscrollcommand=vsb.set, xscrollcommand=hsb.set,
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Column widths
        widths = [40, 260, 130, 60, 70, 80, 140, 80]
        for col, w in zip(self.COLS, widths):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=w, anchor="center" if w < 150 else "w", minwidth=30)

        # Right-click context menu
        self.ctx_menu = ctk.CTkFrame(self)   # placeholder; we use tk Menu
        from tkinter import Menu
        self.menu = Menu(self, tearoff=0, bg="#161B22", fg="#E6EDF3",
                          activebackground="#1F6FEB", activeforeground="white", bd=0)
        self.menu.add_command(label="🗑 Delete Record", command=self._delete_selected)
        self.tree.bind("<Button-3>", self._show_ctx_menu)

        self._sort_col  = "ID"
        self._sort_asc  = False

    # ── Data ─────────────────────────────────────────────────────────────────

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        records  = self.db.get_all_downloads()
        channels = ["All Channels"] + self.db.get_distinct_channels()
        self.after(0, self._populate, records, channels)

    def _populate(self, records: list[dict], channels: list[str]):
        self._all_records = records
        self._ch_menu.configure(values=channels)
        self._apply_filter()

    def _apply_filter(self):
        q   = self.search_entry.get().lower()
        ch  = self.channel_var.get()
        ft  = self.type_var.get()
        ql  = self.quality_var.get()

        rows = [
            r for r in self._all_records
            if (not q or q in r["video_title"].lower() or q in r["channel"].lower())
            and (ch == "All Channels" or r["channel"] == ch)
            and (ft == "All Types"    or r["file_type"] == ft)
            and (ql == "All Qualities" or r["quality"] == ql)
        ]
        self._render_rows(rows)
        self.count_lbl.configure(text=f"{len(rows)} record(s) found")

    def _render_rows(self, rows: list[dict]):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            tag = "audio" if r["file_type"] == "audio" else "video"
            self.tree.insert("", "end", iid=str(r["id"]), tags=(tag,), values=(
                r["id"], r["video_title"][:55], r["channel"][:30],
                r["file_type"], r["quality"],
                f"{r['file_size']:.1f}",
                r["download_date"][:16],
                r["status"],
            ))
        self.tree.tag_configure("audio", foreground="#FFE66D")
        self.tree.tag_configure("video", foreground="#E6EDF3")

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.channel_var.set("All Channels")
        self.type_var.set("All Types")
        self.quality_var.set("All Qualities")
        self._apply_filter()

    def _sort_by(self, col: str):
        rows = list(self.tree.get_children())
        col_idx = list(self.COLS).index(col)
        reverse = (self._sort_col == col and self._sort_asc)
        rows.sort(key=lambda x: self.tree.set(x, col), reverse=reverse)
        for i, item in enumerate(rows):
            self.tree.move(item, "", i)
        self._sort_col = col
        self._sort_asc = not reverse

    def _show_ctx_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.menu.post(event.x_root, event.y_root)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Delete", f"Delete {len(sel)} record(s)?"):
            for iid in sel:
                self.db.delete_download(int(iid))
                self.tree.delete(iid)
            self._all_records = [r for r in self._all_records if str(r["id"]) not in sel]
            self.count_lbl.configure(text=f"{len(self.tree.get_children())} record(s) found")
            logger.log_user_action("Delete records", str(sel))
