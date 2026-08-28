import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.resolve()


@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "bot_database.sqlite3"))
    DOWNLOADS_DIR: Path = BASE_DIR / os.getenv("DOWNLOADS_DIR", "downloads")

    def validate(self) -> None:
        if not self.BOT_TOKEN or self.BOT_TOKEN == "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ":
            raise ValueError(
                "BOT_TOKEN is not set or using the default dummy token. "
                "Please set a valid BOT_TOKEN in your .env file or environment."
            )
        self.DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


config = Config()
