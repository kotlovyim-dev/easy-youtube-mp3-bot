import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

import static_ffmpeg

from bot.config import config
from bot.database import db
from bot.handlers import setup_routers
from bot.middlewares import UserSettingsMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """Register bot menu commands in Telegram UI."""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot & view intro"),
        BotCommand(command="settings", description="⚙️ Customize download preferences"),
        BotCommand(command="mode", description="🔄 Toggle default MP3 / Video mode"),
        BotCommand(command="help", description="📖 Usage guide & supported sites"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully.")


async def main() -> None:
    """Main application entry point."""
    logger.info("Initializing static ffmpeg binaries...")
    static_ffmpeg.add_paths()

    # Validate configuration
    config.validate()

    logger.info("Initializing SQLite database...")
    await db.init()

    # Initialize Bot and Dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register Middlewares
    user_middleware = UserSettingsMiddleware()
    dp.message.middleware(user_middleware)
    dp.callback_query.middleware(user_middleware)

    # Register Routers
    main_router = setup_routers()
    dp.include_router(main_router)

    # Set up Telegram UI commands
    await set_bot_commands(bot)

    logger.info("Starting bot polling...")
    try:
        # Drop pending updates to avoid spamming upon restart
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Closing bot session...")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
