import asyncio
import aiohttp
import logging
from typing import List, Optional
from urllib.parse import urljoin

import aiofiles
from aiohttp import ClientError
from bs4 import BeautifulSoup

from decorators import async_timed
from filter import FilterUrl
from mixins.http_client import AsyncHTTPClientMixin

logger = logging.getLogger(__name__)


class Crawler(AsyncHTTPClientMixin):
    def __init__(
        self,
        urls: List[str],
        domain: str = None,
        subdomain: str = None,
        crawl_count: int = 10,
        max_connection: int = 10,
        retries: int = 1,
        timeout: float = 10,
        output_file: Optional[str] = None,
    ):
        super().__init__(timeout=timeout)
        self.max_connection = max_connection
        self.semaphore = asyncio.Semaphore(max_connection)
        self.remaining_crawls = crawl_count
        self.urls = urls
        self.processed_count = 0
        self.retries = retries
        self.max_crawls = crawl_count
        self.lock = asyncio.Lock()
        self.file_lock = asyncio.Lock()
        self.output_file = output_file or "../data/scrape_data.csv"
        self.filter = FilterUrl(domain, subdomain)

    async def custom_create_task(self) -> List[asyncio.Task]:
        tasks = []

        async for url in self.filter:
            if self.remaining_crawls <= 0:
                break
            tasks.append(asyncio.create_task(self.fetch_urls_and_urldata(url)))
            async with self.lock:
                self.remaining_crawls -= 1
            logger.debug(f"Task created for {url}, remaining: {self.remaining_crawls}")

            if len(tasks) >= self.max_connection:
                break

        return tasks

    async def fetch_urls_and_urldata(self, url: str) -> None:
        async with self.semaphore:
            for attempt in range(self.retries):
                try:
                    async with asyncio.timeout(self.timeout):
                        async with self.client.get(url) as response:
                            if response.status != 200:
                                logger.warning(
                                    f"Non-200 status code for {url}: {response.status}"
                                )
                                return

                            html_content = await response.text()
                            await self.extract_url_links(url, html_content)
                            text = await self.extract_text_from_html(html_content)
                            await self.asynchronous_write_to_file(url, text)

                            async with self.lock:
                                self.processed_count += 1
                            logger.info(f"Processed {self.processed_count} of {self.max_crawls} URL: {url}")
                            return

                except asyncio.TimeoutError as e:
                    logger.warning(
                        f"Timeout on {url} (attempt {attempt + 1})"
                    )
                    if attempt == self.retries - 1:
                        logger.error(f"Failed to fetch {url} after {self.retries} attempts")
                        return
                except ClientError as e:
                    logger.error(f"Network error while fetching {url}: {e}")
                    return
                except Exception as e:
                    logger.error(f"Unexpected error while fetching {url} : {e}")
                    return

    async def fetch_all(self):
        while self.remaining_crawls > 0 and self.filter.has_pending():
            logger.info(f"Remaining crawls: {self.remaining_crawls}")

            tasks = await self.custom_create_task()
            if not tasks:
                logger.error("No more links discovered")
                break

            logger.info(f"Created {len(tasks)} tasks. Waiting for completion...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task Error: {result}")
            
        if not self.filter.has_pending() and self.remaining_crawls > 0:
            logger.error("No more links discovered but remaining crawls are not zero!")

        logger.info(f"Finished crawling. Processed: {self.processed_count}/{self.max_crawls}")

    async def extract_url_links(self, url: str, html_content: str):
        soup = BeautifulSoup(html_content, "lxml")
        links = [urljoin(url, tag["href"]) for tag in soup.find_all("a", href=True)]

        if links:
            await self.filter.add_url(links)
            logger.debug(f"Discovered {len(links)} links from {url}")

    async def extract_text_from_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.extract()
        return ' '.join(soup.stripped_strings)

    async def asynchronous_write_to_file(self, url: str, data: str):
        try:
            async with self.file_lock:
                async with aiofiles.open(self.output_file, mode="a") as f:
                    await f.write(f"url: {url}, scraped_data: {data}\n")
            logger.debug(f"Content stored for {url}")
        except IOError as e:
            logger.error(f"Failed to write content of {url} to file, error: {str(e)}")

    @async_timed()
    async def run(self):
        async with self:
            await self.filter.add_url(self.urls)
            logger.info("Fetching URLs...")
            await self.fetch_all()
