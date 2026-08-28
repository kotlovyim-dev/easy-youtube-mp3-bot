import html
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import FSInputFile

from bot.database import db
from bot.keyboards.download_kb import (
    get_cached_url,
    get_download_choice_keyboard,
)
from bot.services import Downloader, extract_urls, is_supported_url

logger = logging.getLogger(__name__)
router = Router()
downloader = Downloader()


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds:
        return "Unknown"
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


@router.message(Command("download", "dl"))
@router.message(F.text)
async def handle_url_message(message: types.Message, user_settings: Dict[str, Any]) -> None:
    """Handle incoming messages with media links."""
    text = message.text or ""
    urls = extract_urls(text)

    if not urls:
        if message.text.startswith("/"):
            return  # Let other command handlers take care or ignore
        await message.answer(
            "💡 <b>Send a valid video link</b> to download.\n\n"
            "Supported: YouTube, TikTok, Instagram Reels, Twitter/X, SoundCloud, and more!\n"
            "Use /settings to adjust your download preferences.",
            parse_mode="HTML",
        )
        return

    url = urls[0]
    mode = user_settings.get("download_mode", "ask")

    if mode == "ask":
        status_msg = await message.answer("🔍 <i>Fetching media information...</i>", parse_mode="HTML")
        try:
            info = await downloader.get_info(url)
            title = info.title if info else "Media Link"
            uploader = info.uploader if info and info.uploader else "Unknown Author"
            duration_str = format_duration(info.duration) if info else "Unknown"

            card_text = (
                f"🎬 <b>{html.escape(title)}</b>\n\n"
                f"👤 <b>Author:</b> {html.escape(uploader)}\n"
                f"⏱ <b>Duration:</b> {duration_str}\n\n"
                "<i>Select your preferred format to download:</i>"
            )
            kb = get_download_choice_keyboard(url)
            await status_msg.edit_text(card_text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logger.error("Error extracting info for %s: %s", url, e)
            kb = get_download_choice_keyboard(url)
            await status_msg.edit_text(
                f"🔗 <b>Target URL:</b> <code>{html.escape(url)}</code>\n\n"
                "<i>Select format to download:</i>",
                parse_mode="HTML",
                reply_markup=kb,
            )
    elif mode == "audio":
        status_msg = await message.answer("⏳ <i>Processing audio request...</i>", parse_mode="HTML")
        await process_download(
            bot=message.bot,
            chat_id=message.chat.id,
            status_msg=status_msg,
            url=url,
            media_type="audio",
            user_settings=user_settings,
        )
    elif mode == "video":
        status_msg = await message.answer("⏳ <i>Processing video request...</i>", parse_mode="HTML")
        await process_download(
            bot=message.bot,
            chat_id=message.chat.id,
            status_msg=status_msg,
            url=url,
            media_type="video",
            user_settings=user_settings,
        )


@router.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(query: types.CallbackQuery, user_settings: Dict[str, Any]) -> None:
    """Handle download choice callback buttons."""
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid request.")
        return

    _, action, token = parts

    if action == "cancel":
        await query.message.edit_text("❌ <i>Download cancelled.</i>", parse_mode="HTML")
        await query.answer()
        return

    url = get_cached_url(token)
    if not url:
        await query.answer("⚠️ Session expired. Please send the link again.", show_alert=True)
        await query.message.delete()
        return

    await query.answer("Starting download...")
    status_msg = await query.message.edit_text(
        f"⏳ <i>Downloading & converting to {action.upper()}... Please wait.</i>",
        parse_mode="HTML",
    )

    await process_download(
        bot=query.bot,
        chat_id=query.message.chat.id,
        status_msg=status_msg,
        url=url,
        media_type=action,
        user_settings=user_settings,
    )


async def process_download(
    bot: Bot,
    chat_id: int,
    status_msg: types.Message,
    url: str,
    media_type: str,
    user_settings: Dict[str, Any],
) -> None:
    """Execute download, upload to Telegram, and clean up temporary files."""
    audio_q = user_settings.get("audio_quality", "320")
    video_q = user_settings.get("video_quality", "best")
    send_as_file = bool(user_settings.get("send_as_file", 0))

    result = None
    try:
        if media_type == "audio":
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
            await status_msg.edit_text(
                f"🎵 <i>Extracting MP3 ({audio_q} kbps)...</i>",
                parse_mode="HTML",
            )
            result = await downloader.download_audio(url=url, quality=audio_q)
        else:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VIDEO)
            await status_msg.edit_text(
                f"🎬 <i>Downloading Video ({video_q.upper()})...</i>",
                parse_mode="HTML",
            )
            result = await downloader.download_video(url=url, quality=video_q)

        await status_msg.edit_text("📤 <i>Uploading to Telegram...</i>", parse_mode="HTML")

        file_to_send = FSInputFile(result.file_path, filename=result.file_path.name)
        thumb_file = (
            FSInputFile(result.thumbnail_path)
            if result.thumbnail_path and result.thumbnail_path.exists()
            else None
        )

        caption = f"✨ <b>{html.escape(result.title)}</b>\n💾 {result.file_size_mb:.1f} MB"

        if send_as_file:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await bot.send_document(
                chat_id=chat_id,
                document=file_to_send,
                thumbnail=thumb_file,
                caption=caption,
                parse_mode="HTML",
            )
        elif result.media_type == "audio":
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VOICE)
            await bot.send_audio(
                chat_id=chat_id,
                audio=file_to_send,
                title=result.title,
                performer=result.uploader,
                duration=result.duration,
                thumbnail=thumb_file,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
            await bot.send_video(
                chat_id=chat_id,
                video=file_to_send,
                duration=result.duration,
                width=result.width,
                height=result.height,
                thumbnail=thumb_file,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
            )

        # Remove the status message on success
        try:
            await status_msg.delete()
        except TelegramAPIError:
            pass

    except Exception as err:
        logger.error("Download/Upload failed for %s: %s", url, err, exc_info=True)
        error_message = str(err)
        if "exceeds Telegram bot limit" in error_message:
            display_err = (
                f"❌ <b>File Too Large!</b>\n\n"
                f"{html.escape(error_message)}\n"
                "💡 <i>Try selecting a lower resolution/bitrate in /settings or choose audio only.</i>"
            )
        else:
            display_err = (
                f"❌ <b>Download Failed!</b>\n\n"
                f"<code>{html.escape(error_message[:200])}</code>\n\n"
                "Please verify that the link is public and accessible."
            )
        try:
            await status_msg.edit_text(display_err, parse_mode="HTML")
        except TelegramAPIError:
            await bot.send_message(chat_id=chat_id, text=display_err, parse_mode="HTML")

    finally:
        # Always clean up downloaded files
        if result:
            result.cleanup()
