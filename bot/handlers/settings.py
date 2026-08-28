from aiogram import F, Router, types
from aiogram.filters import Command
from bot.database import db
from bot.keyboards.settings_kb import (
    get_audio_quality_keyboard,
    get_mode_keyboard,
    get_settings_keyboard,
    get_video_quality_keyboard,
)

router = Router()


def build_settings_text(settings: dict) -> str:
    mode = settings.get("download_mode", "ask")
    audio_q = settings.get("audio_quality", "320")
    video_q = settings.get("video_quality", "best")
    send_as_file = bool(settings.get("send_as_file", 0))

    mode_text = {
        "audio": "🎵 Audio Only (MP3)",
        "video": "🎬 Video (MP4)",
        "ask": "❓ Ask Each Time",
    }.get(mode, "❓ Ask Each Time")

    audio_text = f"{audio_q} kbps" if audio_q != "best" else "Best"
    video_text = video_q.upper() if video_q != "best" else "Best Available"
    file_format = "📄 Document File" if send_as_file else "🎵 Media Player"

    return (
        "⚙️ <b>Your Download Settings</b>\n\n"
        f"• <b>Default Mode:</b> {mode_text}\n"
        f"• <b>Audio Bitrate:</b> {audio_text}\n"
        f"• <b>Video Resolution:</b> {video_text}\n"
        f"• <b>Send Format:</b> {file_format}\n\n"
        "<i>Click any button below to modify your preferences instantly:</i>"
    )


@router.message(Command("settings"))
async def cmd_settings(message: types.Message, user_settings: dict) -> None:
    """Handle /settings command."""
    text = build_settings_text(user_settings)
    kb = get_settings_keyboard(user_settings)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(Command("mode"))
async def cmd_mode(message: types.Message, user_settings: dict) -> None:
    """Handle /mode quick shortcut."""
    current_mode = user_settings.get("download_mode", "ask")
    text = (
        "🔄 <b>Quick Mode Switcher</b>\n\n"
        "Choose how you want incoming links to be downloaded by default:"
    )
    kb = get_mode_keyboard(current_mode)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "set_menu:main")
async def cb_main_menu(query: types.CallbackQuery) -> None:
    """Return to main settings menu."""
    settings = await db.get_user_settings(query.from_user.id)
    text = build_settings_text(settings)
    kb = get_settings_keyboard(settings)
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "set_menu:mode")
async def cb_mode_menu(query: types.CallbackQuery) -> None:
    """Open mode selection submenu."""
    settings = await db.get_user_settings(query.from_user.id)
    current_mode = settings.get("download_mode", "ask")
    text = (
        "📥 <b>Select Preferred Download Mode</b>\n\n"
        "• <b>Audio Only:</b> Automatically extracts MP3 for every link sent.\n"
        "• <b>Video:</b> Automatically downloads MP4 video for every link sent.\n"
        "• <b>Ask Each Time:</b> Gives you buttons to choose format per link."
    )
    kb = get_mode_keyboard(current_mode)
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "set_menu:audio_q")
async def cb_audio_quality_menu(query: types.CallbackQuery) -> None:
    """Open audio quality submenu."""
    settings = await db.get_user_settings(query.from_user.id)
    current_q = settings.get("audio_quality", "320")
    text = (
        "🎧 <b>Select MP3 Audio Bitrate</b>\n\n"
        "Higher bitrates provide better sound quality with slightly larger file sizes."
    )
    kb = get_audio_quality_keyboard(current_q)
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "set_menu:video_q")
async def cb_video_quality_menu(query: types.CallbackQuery) -> None:
    """Open video quality submenu."""
    settings = await db.get_user_settings(query.from_user.id)
    current_q = settings.get("video_quality", "best")
    text = (
        "🎬 <b>Select Preferred Video Resolution</b>\n\n"
        "The bot will download the highest available resolution up to your selected limit."
    )
    kb = get_video_quality_keyboard(current_q)
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await query.answer()


@router.callback_query(F.data == "toggle:send_as_file")
async def cb_toggle_send_as_file(query: types.CallbackQuery) -> None:
    """Toggle between media player view and document file view."""
    settings = await db.get_user_settings(query.from_user.id)
    new_val = 0 if settings.get("send_as_file", 0) == 1 else 1
    await db.update_user_setting(query.from_user.id, "send_as_file", new_val)

    updated_settings = await db.get_user_settings(query.from_user.id)
    text = build_settings_text(updated_settings)
    kb = get_settings_keyboard(updated_settings)
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    status_label = "Document File" if new_val else "Media Player"
    await query.answer(f"Format changed to: {status_label}")


@router.callback_query(F.data.startswith("set_val:"))
async def cb_set_val(query: types.CallbackQuery) -> None:
    """Update a specific setting value and refresh menu."""
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid request.")
        return

    _, key, value = parts
    await db.update_user_setting(query.from_user.id, key, value)

    # Return updated sub-view or main view
    settings = await db.get_user_settings(query.from_user.id)
    if key == "download_mode":
        text = (
            "📥 <b>Select Preferred Download Mode</b>\n\n"
            "• <b>Audio Only:</b> Automatically extracts MP3 for every link sent.\n"
            "• <b>Video:</b> Automatically downloads MP4 video for every link sent.\n"
            "• <b>Ask Each Time:</b> Gives you buttons to choose format per link."
        )
        kb = get_mode_keyboard(value)
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer("Mode preference updated!")
    elif key == "audio_quality":
        text = (
            "🎧 <b>Select MP3 Audio Bitrate</b>\n\n"
            "Higher bitrates provide better sound quality with slightly larger file sizes."
        )
        kb = get_audio_quality_keyboard(value)
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer(f"Audio bitrate set to {value} kbps!")
    elif key == "video_quality":
        text = (
            "🎬 <b>Select Preferred Video Resolution</b>\n\n"
            "The bot will download the highest available resolution up to your selected limit."
        )
        kb = get_video_quality_keyboard(value)
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer(f"Video resolution set to {value.upper()}!")
    else:
        text = build_settings_text(settings)
        kb = get_settings_keyboard(settings)
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer("Setting updated!")


@router.callback_query(F.data == "settings:close")
async def cb_close_settings(query: types.CallbackQuery) -> None:
    """Close the settings menu."""
    await query.message.delete()
    await query.answer("Settings closed.")
