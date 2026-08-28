import re
from typing import List

URL_PATTERN = re.compile(
    r"(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|"
    r"https?://youtu\.be/[a-zA-Z0-9_-]+|"
    r"https?://(?:www\.)?youtube\.com/[^\s]+)",
    re.IGNORECASE,
)


def extract_urls(text: str) -> List[str]:
    """Extract all valid HTTP/HTTPS URLs from the input text."""
    if not text:
        return []
    return URL_PATTERN.findall(text)


def is_supported_url(url: str) -> bool:
    """Check if the string contains a valid web URL."""
    return bool(URL_PATTERN.match(url.strip()))
