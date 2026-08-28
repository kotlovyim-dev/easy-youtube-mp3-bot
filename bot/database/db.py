import logging
from typing import Any, Dict, Optional
import aiosqlite
from bot.config import config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def init(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    download_mode TEXT DEFAULT 'ask', -- 'audio', 'video', 'ask'
                    audio_quality TEXT DEFAULT '320',  -- '320', '256', '192', '128', 'best'
                    video_quality TEXT DEFAULT 'best', -- 'best', '1080p', '720p', '480p', '360p'
                    send_as_file INTEGER DEFAULT 0,    -- 0: media player, 1: document file
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            await db.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    async def get_or_create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch user settings or create with default values if not exists."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()

            if row:
                # Update username or first_name if changed
                if row["username"] != username or row["first_name"] != first_name:
                    await db.execute(
                        "UPDATE users SET username = ?, first_name = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (username, first_name, user_id),
                    )
                    await db.commit()
                return dict(row)

            # Insert default user
            await db.execute(
                """
                INSERT INTO users (user_id, username, first_name, download_mode, audio_quality, video_quality, send_as_file)
                VALUES (?, ?, ?, 'ask', '320', 'best', 0)
                """,
                (user_id, username, first_name),
            )
            await db.commit()

            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            new_row = await cursor.fetchone()
            return dict(new_row) if new_row else {}

    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Fetch user settings."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return await self.get_or_create_user(user_id)

    async def update_user_setting(self, user_id: int, key: str, value: Any) -> None:
        """Update a specific setting for a user."""
        allowed_keys = {"download_mode", "audio_quality", "video_quality", "send_as_file"}
        if key not in allowed_keys:
            raise ValueError(f"Invalid setting key: {key}")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE users SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (value, user_id),
            )
            await db.commit()


db = Database()
