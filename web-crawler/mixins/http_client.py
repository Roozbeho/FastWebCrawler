from types import TracebackType
from typing import Optional, Type

import aiohttp
import logging

logger = logging.getLogger(__name__)

class AsyncHTTPClientMixin:
    def __init__(self, timeout: float = 10):
        self.session: aiohttp.ClientSession = None
        self.timeout = timeout
    
    async def start_client(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))

    async def stop_client(self):
        if self.session:
            await self.session.close()
            self.session = None

    @property
    def client(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            logger.warning("Client session not created")
            raise RuntimeError("Client session not created")
        return self.session

    async def __aenter__(self):
        await self.start_client()
    
    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        await self.stop_client()