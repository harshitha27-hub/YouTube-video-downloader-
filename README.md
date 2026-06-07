# 📥 YouTube Downloader Pro

A full-featured YouTube downloader with analytics, ML predictions, report generation, and a modern dark GUI — built for portfolio and internship showcasing.

---

## 🗂 Project Structure

```
youtube_downloader/
│
├── main.py                     # Entry point
│
├── gui/
│   ├── dashboard.py            # KPI cards + activity bars
│   ├── downloader.py           # URL input, metadata preview, download manager
│   ├── history.py              # Searchable / filterable download history table
│   ├── analytics.py            # Interactive Plotly charts (opens in browser)
│   ├── prediction.py           # ML forecast cards + portfolio tracking
│   ├── reports.py              # CSV / Excel / PDF report generator
│   └── settings.py             # App settings + DB management
│
├── modules/
│   ├── yt_downloader.py        # yt-dlp engine with pause/resume/cancel
│   ├── database.py             # SQLite CRUD + analytics queries
│   ├── analytics_engine.py     # Plotly chart builders
│   ├── predictor.py            # Scikit-Learn polynomial regression
│   ├── report_generator.py     # CSV, Excel (openpyxl), PDF (ReportLab)
│   └── logger.py               # Rotating file + console logger
│
├── database/
│   └── downloads.db            # Auto-created SQLite database
│
├── downloads/                  # Default output folder for videos/audio
├── reports/                    # Generated CSV, Excel, PDF, HTML charts
├── logs/
│   └── download.log            # Rotating application log
│
└── requirements.txt
```

---

## ⚙️ Installation

### 1. Prerequisites

- **Python 3.10+**
- **FFmpeg** (required by yt-dlp for merging video+audio)
  - Windows: https://ffmpeg.org/download.html  (add to PATH)
  - macOS:   `brew install ffmpeg`
  - Linux:   `sudo apt install ffmpeg`

### 2. Clone / unzip the project

```bash
cd youtube_downloader
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the App

```bash
python main.py
```

The app will:
1. Auto-create `database/`, `downloads/`, `reports/`, `logs/` directories.
2. Seed **180 demo records** into the DB on first run (so the dashboard isn't empty).
3. Open the main GUI window.

---

## 🖥 Pages

| Page        | Description |
|-------------|-------------|
| Dashboard   | KPI summary cards + daily activity bars + top-channels leaderboard |
| Downloader  | Paste URL → fetch metadata preview → choose quality/type → download (with pause/resume/cancel) |
| History     | Full download log with live search, channel/type/quality filters, sortable columns, delete |
| Analytics   | Stat cards + 5 interactive Plotly charts (open in browser) |
| Prediction  | ML download & storage forecasts + portfolio tracking |
| Reports     | One-click CSV / Excel / PDF report generation |
| Settings    | Output folder, default quality/type, theme, DB seed/clear |

---

## 📊 Features at a Glance

- **yt-dlp** – battle-tested YouTube download engine
- **Multithreaded** downloads — UI never freezes
- **Pause / Resume / Cancel** per download
- **Playlist support** — downloads every video sequentially
- **SQLite** database — zero-config, portable
- **ML predictions** via Scikit-Learn polynomial regression
- **5 interactive Plotly charts** — activity trend, top channels, quality split, type split, combined dashboard
- **3 report formats** — CSV, multi-sheet Excel, styled PDF
- **Rotating log** — up to 5 MB × 3 files in `logs/`
- **Dark mode GUI** with CustomTkinter

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `FFmpegNotFound` | Install FFmpeg and add it to PATH |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the venv |
| Download fails with 403 | Update yt-dlp: `pip install -U yt-dlp` |
| Charts don't open | Ensure a browser is set as the system default |
| `sqlite3` errors | Delete `database/downloads.db` and restart |

---

## 📦 Key Libraries

| Library | Purpose |
|---------|---------|
| yt-dlp | YouTube downloading |
| customtkinter | Modern dark-mode GUI |
| pandas | Data manipulation |
| plotly | Interactive charts |
| scikit-learn | ML prediction |
| openpyxl | Excel report |
| reportlab | PDF report |
| sqlite3 | Embedded database (stdlib) |

---

## 📄 License

MIT — free to use, modify, and showcase in your portfolio.
