import asyncio
import os
import tempfile
import unittest
from pathlib import Path

from bot.database.db import Database
from bot.keyboards.download_kb import cache_url, get_cached_url, get_download_choice_keyboard
from bot.keyboards.settings_kb import (
    get_audio_quality_keyboard,
    get_mode_keyboard,
    get_settings_keyboard,
    get_video_quality_keyboard,
)
from bot.services.url_utils import extract_urls, is_supported_url


class TestDatabase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()
        self.db = Database(db_path=self.temp_db_path)
        await self.db.init()

    async def asyncTearDown(self):
        try:
            os.unlink(self.temp_db_path)
        except OSError:
            pass

    async def test_user_creation_and_defaults(self):
        user = await self.db.get_or_create_user(user_id=123456, username="tester", first_name="Test")
        self.assertEqual(user["user_id"], 123456)
        self.assertEqual(user["download_mode"], "ask")
        self.assertEqual(user["audio_quality"], "320")
        self.assertEqual(user["video_quality"], "best")
        self.assertEqual(user["send_as_file"], 0)

    async def test_update_settings(self):
        await self.db.get_or_create_user(user_id=999, username="user2", first_name="User2")
        await self.db.update_user_setting(user_id=999, key="download_mode", value="audio")
        await self.db.update_user_setting(user_id=999, key="audio_quality", value="256")
        await self.db.update_user_setting(user_id=999, key="send_as_file", value=1)

        updated = await self.db.get_user_settings(user_id=999)
        self.assertEqual(updated["download_mode"], "audio")
        self.assertEqual(updated["audio_quality"], "256")
        self.assertEqual(updated["send_as_file"], 1)


class TestUrlUtils(unittest.TestCase):
    def test_extract_urls(self):
        sample = "Check this out https://www.youtube.com/watch?v=dQw4w9WgXcQ and this https://youtu.be/test"
        urls = extract_urls(sample)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(urls[1], "https://youtu.be/test")

    def test_is_supported_url(self):
        self.assertTrue(is_supported_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(is_supported_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertTrue(is_supported_url("https://tiktok.com/@user/video/123456789"))
        self.assertTrue(is_supported_url("https://soundcloud.com/artist/track"))
        self.assertFalse(is_supported_url("hello world not a url"))


class TestKeyboards(unittest.TestCase):
    def test_settings_keyboard(self):
        settings = {
            "download_mode": "audio",
            "audio_quality": "320",
            "video_quality": "1080p",
            "send_as_file": 0,
        }
        kb = get_settings_keyboard(settings)
        self.assertIsNotNone(kb)
        self.assertTrue(len(kb.inline_keyboard) > 0)

    def test_mode_keyboard(self):
        kb = get_mode_keyboard("audio")
        self.assertIsNotNone(kb)
        found_checkmark = any("✅" in btn.text for row in kb.inline_keyboard for btn in row)
        self.assertTrue(found_checkmark)

    def test_url_cache_and_choice_kb(self):
        url = "https://www.youtube.com/watch?v=test12345"
        token = cache_url(url)
        self.assertEqual(get_cached_url(token), url)

        kb = get_download_choice_keyboard(url)
        self.assertIsNotNone(kb)


if __name__ == "__main__":
    unittest.main()
