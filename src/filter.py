import asyncio
import logging
import os
import urllib
import urllib.parse
from typing import AsyncGenerator

import tldextract

logger = logging.getLogger(__name__)


class FilterUrl:
    """
    Normalize extracted url,
    Filter out uncrawlable URL(INVALID_EXTENSTION),
    Filter out invalid url(social media domain)
    """

    INVALID_EXTENSTION = [
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp', '.tiff',

    # Audio Files 
    '.mp3','.wav', '.ogg', '.flac', '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',

    # Documents 
    '.zip', '.rar', '.tar.gz', '.7z', '.exe', '.dmg', '.iso', '.deb', '.rpm',

    # Compressed/Executable Files
    '.zip', '.rar', '.exe', '.dll',

    # Scripts/Dynamic Content
    '.css', '.js', '.scss', '.less', '.php', '.py', '.java', '.class',' .jar',

    # Other (Server files, backups, etc.)
    '.ico', '.log', '.sql', '.db', '.bak', '.tmp', '.swp', '.env', '.gitignore'
    ]

    INVALID_PATH = [
    '/cgi-bin/', '/tmp/', '/private/', '/wp-admin/', '/wp-includes/',
    '/api/', '/search?', '/login/', '/signup/', '/account/', '/cart/',
    '/checkout/', '/admin/', '/backup/', '/config/', '/database/',
    '/logs/', '/secret/', '/test/', '/debug/'
    ]

    def __init__(self, domain: str = None, subdomain: str = None):
        self.subdomain = subdomain
        self.domain = domain
        # self.queue = deque()
        self.queue = asyncio.Queue()
        self.seen_url = set()
        self.extract = tldextract.TLDExtract()
        self.lock = asyncio.Lock()

    async def add_url(self, urls: list[str]) -> list[str]:
        async with self.lock:
            for url in urls:
                if (not url in self.seen_url) and self._validate_url(url):
                    self.seen_url.add(url)
                    await self.queue.put(url)

    def _validate_url(self, url: str) -> bool:
        return all(
            [
                self._validate_schema(url),
                self._validate_subdomain(url),
                self._validate_domain(url),
                self._validate_path(url),
                self._validate_extension(url),
            ]
        )

    @classmethod
    def add_invalid_path(cls, path):
        if path not in cls.INVALID_PATH:
            cls.INVALID_PATH.append(path)

    def _validate_schema(self, url) -> bool:
        return urllib.parse.urlparse(url).scheme.lower() in ["http", "https"]

    def _validate_subdomain(self, url) -> bool:
        subdomain = self.extract(url).subdomain
        return (not subdomain or not self.subdomain) or subdomain == self.subdomain

    def _validate_domain(self, url) -> bool:
        domain = self.extract(url).domain
        return (not domain or not self.domain) or domain == self.domain

    def _validate_path(self, url) -> bool:
        path = urllib.parse.urlparse(url).path
        return path not in self.INVALID_PATH

    def _validate_extension(self, url):
        path_without_params, _ = os.path.splitext(url.split("?")[0])
        _, extension = os.path.splitext(path_without_params)
        return extension not in self.INVALID_EXTENSTION

    async def __aiter__(self) -> AsyncGenerator[str, None]:
        while True:
            try:
                yield await self.queue.get()
            except asyncio.QueueEmpty:
                break

    def has_pending(self):
        return not self.queue.empty()
