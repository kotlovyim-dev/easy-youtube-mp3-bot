from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from bot.database import db


class UserSettingsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: User = data.get("event_from_user")
        if event_user and not event_user.is_bot:
            user_settings = await db.get_or_create_user(
                user_id=event_user.id,
                username=event_user.username,
                first_name=event_user.first_name,
            )
            data["user_settings"] = user_settings

        return await handler(event, data)
