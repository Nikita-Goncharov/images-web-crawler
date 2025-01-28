import os
import time
import logging
from datetime import datetime
from urllib.parse import urljoin
from multiprocessing import Process  #, Queue

import cv2
import requests
from PIL import Image
from bs4 import BeautifulSoup
from bs4.element import PageElement


logging.basicConfig(level=logging.INFO)

class CryptoCrawler:
    def __init__(self, keywords: list[str], text_to_keyword: str):
        self.keywords = keywords
        # make links pointed to google images by request
        self.text_to_keyword = text_to_keyword.replace(" ", "+")  # ai generated, coins logo, memes, stock images
        self.urls = [f"https://www.google.com/search?q={keyword.replace(' ', '+')}+{self.text_to_keyword}&tbm=isch" for keyword in self.keywords]
        self.parsing_processes = {}
        # self.visited_queue = Queue()
        # self.to_visit_queue = Queue()

        logging.log(logging.INFO, f"Keywords: {self.keywords}")
        logging.log(logging.INFO, f"Urls for parsing: {self.urls}")

    def start_parsing(self):
        for url in self.urls:
            self.parsing_processes[url] = Process(target=self.crawl_site, args=(url,))
            self.parsing_processes[url].start()
        logging.log(logging.INFO, f"All parsing processes is started")
        logging.log(logging.INFO, f"Parsing processes: {self.parsing_processes}")

    def stop_parsing(self):
        for url, process in self.parsing_processes.items():
            process.terminate()
        logging.log(logging.INFO, f"All parsing processes is stopped")

    def download_image(self, url, save_dir="logos"):
        os.makedirs(save_dir, exist_ok=True)
        _, file_ext = os.path.splitext(url)  # get file extension from URL
        path = os.path.join(save_dir, f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{file_ext}')

        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.log(logging.INFO, f"Saved: {path}")
        except Exception as e:
            logging.log(logging.INFO, f"Error downloading {url}: {e}")

    def image_find_keyword(self, img_tag: PageElement, filename: str) -> str | None:
        # Перевіримо alt або назву файлу
        alt = img_tag.get("alt", "").lower()
        title = img_tag.get("title", "").lower()

        logging.log(logging.INFO, f"alt: {alt}, title: {title}, filename: {filename}")

        for keyword in self.keywords:
            logging.log(logging.INFO, f"Check keyword: {keyword} in img data")
            if keyword in alt or keyword in filename or keyword in title:
                logging.log(logging.INFO, f"Found keyword: {keyword} in tag: {img_tag}")
                return keyword
        return None

    def is_image_valid(self, absolute_src: str) -> bool:
        # is_img = (".png" in file_ext or ".jpg" in file_ext or ".svg" in file_ext or ".jpeg" in file_ext) and "webp" not in file_ext
        try:
            img = Image.open(absolute_src)
            w, h = img.size
            logging.log(logging.INFO, f"Image size: {w}x{h}")
            if w > 240 and h > 240:
                return True
        except Exception as ex:
            logging.log(logging.INFO, f"Exception when image validation: {str(ex)}")
            if ".svg" in absolute_src:  # image can not open if broken or if it is svg, svg we save
                return True  # TODO: check svg image size

        return False

    def scrape_images(self, page_url):
        response = requests.get(page_url, timeout=10)
        if not response.ok:
            logging.log(logging.INFO, f"Error loading page {page_url} with code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        for img_tag in soup.find_all("img"):
            src = img_tag.get("src")

            if not src:
                continue

            logging.log(logging.INFO, img_tag)

            # make absolute URL
            absolute_src = urljoin(page_url, src)
            filename = absolute_src.split("/")[-1].lower()
            filename, file_ext = os.path.splitext(filename)

            found_keyword = self.image_find_keyword(img_tag, filename)
            if found_keyword is not None:
                if self.is_image_valid(absolute_src):
                    logging.log(logging.INFO, f"Found image for saving")
                    self.download_image(absolute_src, save_dir=f"logos_{found_keyword}")


    def find_links(self, page_url):
        links = set()
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.log(logging.INFO, f"Error loading page {page_url}: {e}")
            return links

        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href")
            if not href:
                continue
            abs_url = urljoin(page_url, href)

            links.add(abs_url)
        return links

    def crawl_site(self, url):
        visited = set()
        to_visit = set([url])

        while to_visit:
            current_url, *_ = to_visit

            if current_url in visited:
                continue

            visited.add(current_url)
            logging.log(logging.INFO, f"Crawling: {current_url}")

            # parse images by keywords
            self.scrape_images(current_url)

            # find all links on page and append in to_visit not visited
            links = self.find_links(current_url)
            logging.log(logging.INFO, f"Found links on page: {links}")
            logging.log(logging.INFO, f"Already visited links: {visited}")
            to_visit.update(links.difference(visited))
            logging.log(logging.INFO, f"Resulted to_visit links: {to_visit}")

        logging.log(logging.INFO, f"\nFinished crawling. Visited {len(visited)} pages.")


if __name__ == "__main__":
    keywords = [
        "Bitcoin",
        "BTC",
        "Ethereum",
        "ETH",
        "Tether",
        "USDT",
        "BNB",
        "USD Coin",
        "USD_Coin",
        "USDC",
        "XRP",
        "Cardano",
        "ADA",
        "Dogecoin",
        "DOGE",
        "Solana",
        "SOL",
        "Polygon",
        "MATIC",
        "Polkadot",
        "DOT",
        "Binance USD",
        "Binance_USD",
        "BUSD",
        "Shiba Inu",
        "Shiba_Inu",
        "SHIB",
        "Tron",
        "TRX",
        "Litecoin",
        "LTC",
        "Avalanche",
        "AVAX",
        "Dai",
        "DAI",
        "Wrapped Bitcoin",
        "Wrapped_Bitcoin",
        "WBTC",
        "Uniswap",
        "UNI",
        "Chainlink",
        "LINK",
        "Cosmos",
        "ATOM",
        "Toncoin",
        "TON",
        "Stellar",
        "XLM",
        "Ethereum Classic",
        "Ethereum_Classic",
        "ETC",
        "Monero",
        "XMR",
        "Bitcoin Cash",
        "Bitcoin_Cash",
        "BCH",
        "Cronos",
        "CRO",
        "Aptos",
        "APT",
        "Lido DAO",
        "Lido_DAO",
        "LDO",
        "NEAR Protocol",
        "NEAR_Protocol",
        "NEAR"
    ]
    keywords = [k.lower() for k in keywords]

    crawler = CryptoCrawler(keywords, "crypto coin stock images")

    crawler.start_parsing()
    time.sleep(60*4)  # wait one hour
    crawler.stop_parsing()



# TODO: remove visited links periodicly
# TODO: some how(using QUEUE make one set of need visit links)
