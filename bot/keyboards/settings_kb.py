from typing import Any, Dict
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_settings_keyboard(user_settings: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Generate the main settings interactive inline keyboard."""
    builder = InlineKeyboardBuilder()

    mode = user_settings.get("download_mode", "ask")
    audio_q = user_settings.get("audio_quality", "320")
    video_q = user_settings.get("video_quality", "best")
    send_as_file = bool(user_settings.get("send_as_file", 0))

    mode_label = {
        "audio": "🎵 Audio (MP3)",
        "video": "🎬 Video (MP4)",
        "ask": "❓ Ask Each Time",
    }.get(mode, "❓ Ask Each Time")

    audio_label = f"{audio_q} kbps" if audio_q != "best" else "Best"
    video_label = video_q.upper() if video_q != "best" else "Best Available"
    file_type_label = "📄 Document File" if send_as_file else "🎵 Audio / Video Player"

    builder.row(
        InlineKeyboardButton(
            text=f"📥 Default Mode: {mode_label}",
            callback_data="set_menu:mode",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🎧 MP3 Bitrate: {audio_label}",
            callback_data="set_menu:audio_q",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🎬 Video Resolution: {video_label}",
            callback_data="set_menu:video_q",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📦 Send Format: {file_type_label}",
            callback_data="toggle:send_as_file",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Close Menu",
            callback_data="settings:close",
        )
    )

    return builder.as_markup()


def get_mode_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    """Generate the download mode selection keyboard."""
    builder = InlineKeyboardBuilder()

    modes = [
        ("audio", "🎵 Audio Only (MP3)"),
        ("video", "🎬 Video (MP4)"),
        ("ask", "❓ Always Ask Every Time"),
    ]

    for mode_val, mode_title in modes:
        mark = " ✅" if current_mode == mode_val else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{mode_title}{mark}",
                callback_data=f"set_val:download_mode:{mode_val}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Back to Settings",
            callback_data="set_menu:main",
        )
    )
    return builder.as_markup()


def get_audio_quality_keyboard(current_quality: str) -> InlineKeyboardMarkup:
    """Generate the audio bitrate selection keyboard."""
    builder = InlineKeyboardBuilder()

    qualities = [
        ("320", "💎 320 kbps (High Quality)"),
        ("256", "🎵 256 kbps (Very Good)"),
        ("192", "📻 192 kbps (Standard)"),
        ("128", "💾 128 kbps (Compact/Data Saver)"),
    ]

    for q_val, q_title in qualities:
        mark = " ✅" if current_quality == q_val else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{q_title}{mark}",
                callback_data=f"set_val:audio_quality:{q_val}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Back to Settings",
            callback_data="set_menu:main",
        )
    )
    return builder.as_markup()


def get_video_quality_keyboard(current_quality: str) -> InlineKeyboardMarkup:
    """Generate the video quality selection keyboard."""
    builder = InlineKeyboardBuilder()

    qualities = [
        ("best", "🌟 Best Available Quality"),
        ("1080p", "📺 1080p (Full HD)"),
        ("720p", "💻 720p (HD Standard)"),
        ("480p", "📱 480p (SD Medium)"),
        ("360p", "💾 360p (Data Saver)"),
    ]

    for q_val, q_title in qualities:
        mark = " ✅" if current_quality == q_val else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{q_title}{mark}",
                callback_data=f"set_val:video_quality:{q_val}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔙 Back to Settings",
            callback_data="set_menu:main",
        )
    )
    return builder.as_markup()
