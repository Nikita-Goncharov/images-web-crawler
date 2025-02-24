import os
import re
import asyncio
import logging
from urllib.parse import urljoin
from multiprocessing import Process, Manager

import httpx
import redis
from bs4 import BeautifulSoup
from bs4.element import PageElement

from celery_app import app
from tasks import download_image
from config import config

logging.getLogger("httpx").setLevel(logging.ERROR)  # disable httpx INFO logs
logger = logging.getLogger(__name__)
redis_client = redis.Redis("redis")

class Crawler:
    def __init__(self, keywords: list[str], text_to_keyword: str):
        self.keywords = set(keywords)

        # make links pointed to google images by request
        self.text_to_keyword = text_to_keyword.replace(" ", "+")
        self.urls = [
            f"https://www.google.com/search?q={keyword.replace(' ', '+')}+{self.text_to_keyword}&tbm=isch"
            for keyword in self.keywords
        ]
        self.parsing_process: None | Process = None
        self.manager = Manager()
        self.shared_data = self.manager.dict()
        self.shared_data["running"] = False

        self.visited = set()
        self.to_visit = set(self.urls)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        }
        self.httpx_client = httpx.AsyncClient(headers=headers)  # , max_redirects=5

    def start_parsing(self):
        logger.info("Start Crawling")
        self.shared_data["running"] = True
        self.parsing_process = Process(
            target=self._run_async, args=(self.start_crawling, self.shared_data)
        )
        self.parsing_process.start()

    def stop_parsing(self):
        if isinstance(self.parsing_process, Process):
            logger.info("Stop Crawling")
            self.shared_data["running"] = False
            self.parsing_process.join()
            app.control.purge()  # clear queue for downloading images

    def image_find_keyword(self, img_tag: PageElement, filename: str) -> set:
        # Check alt, title or file name
        alt = img_tag.get("alt", "").lower()
        title = img_tag.get("title", "").lower()

        # Replace any NOT letters/numbers/spaces with a space
        alt = re.sub(r"[^a-zA-Z0-9\s]+", " ", alt)
        title = re.sub(r"[^a-zA-Z0-9\s]+", " ", title)
        filename = re.sub(r"[^a-zA-Z0-9\s]+", " ", filename)

        alt_matches = set(alt.split(" ")).intersection(set(self.keywords))
        title_matches = set(title.split(" ")).intersection(set(self.keywords))
        filename_matches = set(filename.split(" ")).intersection(set(self.keywords))

        return alt_matches.union(title_matches).union(filename_matches)

    async def scrape_images(self, page_url):
        links = set()

        try:
            response = await self.httpx_client.get(
                page_url, timeout=3, follow_redirects=True
            )
            response.raise_for_status()
        except Exception as ex:
            logger.error(f"Error while loading page {page_url}, ex: {str(ex)}, exception class: {ex.__class__}")
            return links

        soup = BeautifulSoup(response.text, "html.parser")
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")

            if not src:
                continue

            filename = src.split("/")[-1].lower()
            filename, file_ext = os.path.splitext(filename)

            found_keywords = self.image_find_keyword(img_tag, filename)
            if found_keywords:
                first_found, *_ = found_keywords
                absolute_src = urljoin(page_url, src)
                download_image.delay(absolute_src, f"{config.SAVE_IMAGES_PATH}/{first_found}")

        for a_tag in soup.find_all("a"):
            href = a_tag.get("href")
            if not href:
                continue
            abs_url = urljoin(page_url, href)

            links.add(abs_url)
        return links

    async def crawl_site(self, shared_data):
        while self.to_visit and shared_data["running"]:
            current_url, *_ = self.to_visit
            self.to_visit.remove(current_url)

            if current_url in self.visited:
                continue

            self.visited.add(current_url)
            logger.info(f"Crawling: {current_url}")

            # parse images by keywords & find all links on page and append in to_visit not visited
            links = await self.scrape_images(current_url)

            for link in links:
                if link not in self.visited:
                    self.to_visit.add(link)
            redis_client.incr("crawled_links_count")

    def _run_async(self, coro_fn, shared_data):
        """
        Starts the event loop and executes coro_fn(shared_data).
        """
        asyncio.run(coro_fn(shared_data))

    async def start_crawling(self, shared_data):
        async_tasks = []

        for _ in self.urls:
            task = asyncio.create_task(self.crawl_site(shared_data))
            async_tasks.append(task)

        try:
            await asyncio.gather(*async_tasks, return_exceptions=True)
            logger.info(f"\nFinished crawling. Visited {len(self.visited)} pages.")
        except Exception as ex:
            logger.error(f"\nError while crawling: {str(ex)}")
