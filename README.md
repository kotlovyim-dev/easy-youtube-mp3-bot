# 🎬 Telegram YouTube & Media Downloader Bot

A feature-rich, high-performance Telegram bot built with **aiogram 3.x** and **yt-dlp** for downloading videos (MP4) and audio (MP3) from YouTube, TikTok, Instagram, Twitter/X, SoundCloud, and thousands of other platforms.

Includes **per-user persistent settings** (powered by asynchronous SQLite) that users can customize at any time!

---

## ✨ Features

- 🎵 **High-Quality MP3 Extraction**: Automatically extracts audio, adds ID3 metadata (artist, title, thumbnail), and supports selectable bitrates (**320 kbps**, 256 kbps, 192 kbps, 128 kbps).
- 🎬 **Video Downloads (MP4)**: Fast video downloads with audio merged in selectable resolutions (**Best**, 1080p, 720p, 480p, 360p).
- ⚙️ **Interactive Per-User Settings**:
  - **Download Mode**: Choose between *Audio Only (MP3)*, *Video (MP4)*, or *Always Ask*.
  - **Audio Bitrate**: 320 kbps, 256 kbps, 192 kbps, 128 kbps.
  - **Video Resolution**: Best Available, 1080p, 720p, 480p, 360p.
  - **Delivery Format**: Send as native *Media Player* (streamable audio/video) or as a *Document File*.
  - Settings are changeable at **any moment** via `/settings` or `/mode`.
- 🌍 **Supports 1000+ Platforms**: YouTube, YouTube Shorts, TikTok, Instagram Reels, Twitter/X, SoundCloud, Bandcamp, Reddit, Vimeo, Facebook, and more.
- ⚡ **Asynchronous & Non-Blocking**: Heavy downloads run in background thread pools, keeping the bot fast and responsive for all users concurrently.
- 🧹 **Automatic Cleanup**: Temporary downloaded media and thumbnails are cleaned up immediately after upload to prevent disk bloat.
- 📦 **Built-in Static FFmpeg**: Automatically bundles ffmpeg/ffprobe with fallback support.
- 🐳 **Docker Ready**: Includes `Dockerfile` and `docker-compose.yml` for 1-command deployment.

---

## 📁 Project Structure

```
easy-youtube-mp3-bot/
├── bot/
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py            # Asynchronous SQLite database layer
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py         # /start and /help commands
│   │   ├── settings.py      # /settings, /mode, and callback handlers
│   │   └── download.py      # URL handling, downloader triggers, and media upload
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── settings_kb.py   # Interactive settings inline keyboards
│   │   └── download_kb.py   # Format choice buttons per link
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── user_middleware.py # Auto user registration & context injection
│   ├── services/
│   │   ├── __init__.py
│   │   ├── downloader.py    # yt-dlp async wrapper & metadata extraction
│   │   └── url_utils.py     # Regex URL detection and validation
│   ├── __init__.py
│   └── config.py            # Environment configuration loader
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── main.py                  # Bot entry point & dispatcher runner
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Installation

1. **Clone the repository and enter the directory**:
   ```bash
   cd easy-youtube-mp3-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and insert your Telegram bot token:
   ```env
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   MAX_FILE_SIZE_MB=50
   DATABASE_PATH=bot_database.sqlite3
   DOWNLOADS_DIR=downloads
   ```

### 3. Run the Bot

```bash
python3 main.py
```

---

## 🐳 Running with Docker

You can run the bot in Docker using `docker-compose`:

```bash
# 1. Create .env with your BOT_TOKEN
cp .env.example .env
nano .env

# 2. Build and launch
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f
```

---

## 💬 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message, introduction, and quick configuration buttons. |
| `/settings` | Open interactive settings menu (change mode, bitrate, resolution, format). |
| `/mode` | Quick toggle for default format (MP3, MP4, or Ask Each Time). |
| `/help` | Detailed guide and list of supported platforms. |

---

## ⚙️ How User Settings Work

1. **Change Mode**:
   - Send `/settings` or `/mode` in chat.
   - Select **🎵 Audio (MP3)** to auto-download MP3 audio for every link.
   - Select **🎬 Video (MP4)** to auto-download video for every link.
   - Select **❓ Ask Each Time** to receive buttons on every link.
2. **Change Quality**:
   - Click **🎧 MP3 Bitrate** to choose from 128 kbps to 320 kbps.
   - Click **🎬 Video Resolution** to choose from 360p up to 1080p / Best.
3. **Change Send Format**:
   - Toggle between **🎵 Media Player** (playable directly in Telegram audio/video player) and **📄 Document File** (uncompressed file attachment).
