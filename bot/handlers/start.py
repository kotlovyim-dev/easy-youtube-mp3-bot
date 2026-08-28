from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.settings_kb import get_settings_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, user_settings: dict) -> None:
    """Handle /start command."""
    mode = user_settings.get("download_mode", "ask")
    mode_text = {
        "audio": "🎵 Audio (MP3)",
        "video": "🎬 Video (MP4)",
        "ask": "❓ Ask Each Time",
    }.get(mode, "❓ Ask Each Time")

    welcome_text = (
        f"👋 <b>Hello, {message.from_user.first_name}!</b>\n\n"
        "Welcome to the <b>YouTube & Media Downloader Bot</b>!\n\n"
        "⚡ <b>How to use:</b>\n"
        "1. Simply <b>send any video link</b> (YouTube, Shorts, TikTok, Instagram, Twitter/X, SoundCloud, etc.)\n"
        f"2. The bot will automatically process it according to your preference (Current mode: <b>{mode_text}</b>)\n\n"
        "⚙️ <b>Commands:</b>\n"
        "• /settings - Customize your download mode & quality\n"
        "• /mode - Quickly change between MP3, Video, or Ask\n"
        "• /help - Usage guide and info\n\n"
        "👇 <i>Click below to configure your preferences or just send a link!</i>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Open Settings", callback_data="set_menu:main")],
            [
                InlineKeyboardButton(
                    text="🎵 Set MP3 Default",
                    callback_data="set_val:download_mode:audio",
                ),
                InlineKeyboardButton(
                    text="🎬 Set Video Default",
                    callback_data="set_val:download_mode:video",
                ),
            ],
        ]
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=kb)


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """Handle /help command."""
    help_text = (
        "📖 <b>Bot Help & Instructions</b>\n\n"
        "<b>Supported Platforms:</b>\n"
        "• YouTube & YouTube Shorts\n"
        "• TikTok\n"
        "• Instagram Reels & Posts\n"
        "• Twitter / X Videos\n"
        "• SoundCloud & Bandcamp\n"
        "• Reddit, Vimeo, Facebook, and 1000+ more platforms supported by yt-dlp!\n\n"
        "<b>Download Preferences:</b>\n"
        "You can change your preferences at <b>any moment</b>:\n"
        "• <b>Audio (MP3):</b> Extracts high-quality audio with artist & title tags.\n"
        "• <b>Video (MP4):</b> Downloads the full video in your chosen resolution.\n"
        "• <b>Ask Each Time:</b> Shows interactive buttons every time you send a link.\n\n"
        "💡 <i>Tip: Send /settings anytime to change your audio bitrate (up to 320 kbps) or video resolution (up to 1080p).</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Open Settings", callback_data="set_menu:main")]
        ]
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=kb)
