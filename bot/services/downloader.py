import asyncio
import logging
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yt_dlp
import static_ffmpeg

from bot.config import config

logger = logging.getLogger(__name__)

# Ensure ffmpeg/ffprobe are discovered
try:
    static_ffmpeg.add_paths()
except Exception as e:
    logger.warning("Could not add static ffmpeg paths: %s", e)


@dataclass
class MediaInfo:
    url: str
    title: str
    uploader: Optional[str]
    duration: Optional[int]
    thumbnail_url: Optional[str]
    description: Optional[str]
    is_live: bool = False


@dataclass
class DownloadResult:
    file_path: Path
    media_type: str  # 'audio' or 'video'
    title: str
    uploader: Optional[str] = None
    duration: Optional[int] = None
    thumbnail_path: Optional[Path] = None
    file_size_mb: float = 0.0
    width: Optional[int] = None
    height: Optional[int] = None

    def cleanup(self) -> None:
        """Remove downloaded file and thumbnail from disk."""
        try:
            if self.file_path and self.file_path.exists():
                self.file_path.unlink(missing_ok=True)
            if self.thumbnail_path and self.thumbnail_path.exists():
                self.thumbnail_path.unlink(missing_ok=True)
        except Exception as err:
            logger.error("Error cleaning up media files: %s", err)


class Downloader:
    def __init__(self, downloads_dir: Path = config.DOWNLOADS_DIR):
        self.downloads_dir = downloads_dir
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    async def get_info(self, url: str) -> Optional[MediaInfo]:
        """Fetch media information asynchronously without downloading the payload."""
        return await asyncio.to_thread(self._extract_info_sync, url)

    def _extract_info_sync(self, url: str) -> Optional[MediaInfo]:
        ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None

                # If it's a playlist or multiple entries, take the first entry
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                return MediaInfo(
                    url=url,
                    title=info.get("title", "Unknown Title"),
                    uploader=info.get("uploader") or info.get("artist") or info.get("channel"),
                    duration=info.get("duration"),
                    thumbnail_url=info.get("thumbnail"),
                    description=info.get("description"),
                    is_live=bool(info.get("is_live")),
                )
        except Exception as e:
            logger.error("Failed to extract info from %s: %s", url, e)
            raise e

    async def download_audio(
        self,
        url: str,
        quality: str = "320",
    ) -> DownloadResult:
        """Download and convert media to MP3."""
        return await asyncio.to_thread(self._download_audio_sync, url, quality)

    def _download_audio_sync(
        self,
        url: str,
        quality: str = "320",
    ) -> DownloadResult:
        task_id = uuid.uuid4().hex
        out_template = str(self.downloads_dir / f"{task_id}_%(title).100B.%(ext)s")

        # Map quality
        preferred_quality = "320" if quality == "best" else quality

        ydl_opts: Dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": preferred_quality,
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": config.MAX_FILE_SIZE_MB * 1024 * 1024,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Could not extract media info or download audio.")

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            title = info.get("title", "Audio")
            uploader = info.get("uploader") or info.get("artist") or info.get("channel")
            duration = info.get("duration")

            # Locate downloaded mp3 file
            found_audio_file = None
            found_thumb_file = None

            for f in self.downloads_dir.glob(f"{task_id}_*"):
                if f.suffix.lower() == ".mp3":
                    found_audio_file = f
                elif f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    found_thumb_file = f

            if not found_audio_file or not found_audio_file.exists():
                raise FileNotFoundError("Extracted MP3 file not found on disk.")

            file_size_mb = found_audio_file.stat().st_size / (1024 * 1024)
            if file_size_mb > config.MAX_FILE_SIZE_MB:
                # Cleanup and raise
                if found_audio_file.exists():
                    found_audio_file.unlink()
                if found_thumb_file and found_thumb_file.exists():
                    found_thumb_file.unlink()
                raise ValueError(
                    f"Downloaded audio size ({file_size_mb:.1f} MB) exceeds Telegram bot limit of {config.MAX_FILE_SIZE_MB} MB."
                )

            return DownloadResult(
                file_path=found_audio_file,
                thumbnail_path=found_thumb_file,
                media_type="audio",
                title=title,
                uploader=uploader,
                duration=duration,
                file_size_mb=file_size_mb,
            )

    async def download_video(
        self,
        url: str,
        quality: str = "best",
    ) -> DownloadResult:
        """Download video in MP4 format with audio merged."""
        return await asyncio.to_thread(self._download_video_sync, url, quality)

    def _download_video_sync(
        self,
        url: str,
        quality: str = "best",
    ) -> DownloadResult:
        task_id = uuid.uuid4().hex
        out_template = str(self.downloads_dir / f"{task_id}_%(title).100B.%(ext)s")

        # Format selector based on resolution
        if quality == "1080p":
            format_spec = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif quality == "720p":
            format_spec = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif quality == "480p":
            format_spec = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        elif quality == "360p":
            format_spec = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best"
        else:
            # best quality
            format_spec = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

        ydl_opts: Dict[str, Any] = {
            "format": format_spec,
            "outtmpl": out_template,
            "writethumbnail": True,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": config.MAX_FILE_SIZE_MB * 1024 * 1024,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Could not extract media info or download video.")

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            title = info.get("title", "Video")
            uploader = info.get("uploader") or info.get("channel")
            duration = info.get("duration")
            width = info.get("width")
            height = info.get("height")

            found_video_file = None
            found_thumb_file = None

            for f in self.downloads_dir.glob(f"{task_id}_*"):
                if f.suffix.lower() == ".mp4":
                    found_video_file = f
                elif f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    found_thumb_file = f

            if not found_video_file or not found_video_file.exists():
                # Check if it was saved with another video extension
                for f in self.downloads_dir.glob(f"{task_id}_*"):
                    if f.suffix.lower() in [".mkv", ".webm", ".avi", ".mov"]:
                        found_video_file = f
                        break

            if not found_video_file or not found_video_file.exists():
                raise FileNotFoundError("Extracted video file not found on disk.")

            file_size_mb = found_video_file.stat().st_size / (1024 * 1024)
            if file_size_mb > config.MAX_FILE_SIZE_MB:
                if found_video_file.exists():
                    found_video_file.unlink()
                if found_thumb_file and found_thumb_file.exists():
                    found_thumb_file.unlink()
                raise ValueError(
                    f"Downloaded video size ({file_size_mb:.1f} MB) exceeds Telegram bot limit of {config.MAX_FILE_SIZE_MB} MB."
                )

            return DownloadResult(
                file_path=found_video_file,
                thumbnail_path=found_thumb_file,
                media_type="video",
                title=title,
                uploader=uploader,
                duration=duration,
                file_size_mb=file_size_mb,
                width=width,
                height=height,
            )


downloader = Downloader()
