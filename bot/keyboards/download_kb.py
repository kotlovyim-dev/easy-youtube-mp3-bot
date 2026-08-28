import uuid
from typing import Dict
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# In-memory mapping from short_id to full URL to keep callback_data <= 64 bytes
_URL_CACHE: Dict[str, str] = {}


def cache_url(url: str) -> str:
    """Store URL and return an 8-character token."""
    token = uuid.uuid4().hex[:8]
    _URL_CACHE[token] = url
    # Prevent cache from unbounded growth (keep last 1000 items)
    if len(_URL_CACHE) > 1000:
        oldest_key = next(iter(_URL_CACHE))
        del _URL_CACHE[oldest_key]
    return token


def get_cached_url(token: str) -> str | None:
    return _URL_CACHE.get(token)


def get_download_choice_keyboard(url: str) -> InlineKeyboardMarkup:
    """Generate choice keyboard for downloading MP3 or Video."""
    token = cache_url(url)
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🎵 Download MP3 (Audio)",
            callback_data=f"dl:audio:{token}",
        ),
        InlineKeyboardButton(
            text="🎬 Download MP4 (Video)",
            callback_data=f"dl:video:{token}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=f"dl:cancel:{token}",
        )
    )

    return builder.as_markup()
