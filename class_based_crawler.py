import os
import requests
from datetime import datetime
from multiprocessing import Process
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def download_image(url, save_dir="logos"):
    os.makedirs(save_dir, exist_ok=True)
    filename, file_ext = os.path.splitext(url)  # Витягуємо ім'я файлу з URL
    path = os.path.join(save_dir, f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{file_ext}')

    try:
        resp = requests.get(url, stream=True, timeout=10)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved: {path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


def scrape_images(page_url, keywords):
    """
    Парсить одну сторінку:
      - витягує всі <img>
      - якщо в alt або назві файлу є keyword, додає в список

    Повертає: список URL зображень
    """
    images = []
    try:
        resp = requests.get(page_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error loading page {page_url}: {e}")
        return images

    soup = BeautifulSoup(resp.text, "html.parser")
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if not src:
            continue

        print(img_tag)

        # Якщо src відносний, робимо абсолютну URL
        abs_src = urljoin(page_url, src)

        # Перевіримо alt або назву файлу
        alt_text = img_tag.get("alt", "").lower()
        title = img_tag.get("title", "").lower()
        filename = abs_src.split("/")[-1].lower()
        print(alt_text, title, filename)

        for keyword in keywords:
            if keyword in alt_text or keyword in filename or keyword in title:
                is_img = (
                                     ".png" in filename or ".jpg" in filename or ".svg" in filename or ".jpeg" in filename) and "webp" not in filename
                if is_img:
                    print("SHOULD BE SAVED")
                    images.append({keyword: abs_src})
    return images


def find_links(page_url):
    """
    Шукаємо всі <a href="...">,
    Повертаємо список абсолютних URL.
    """
    links = set()
    try:
        resp = requests.get(page_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error loading page {page_url}: {e}")
        return links

    soup = BeautifulSoup(resp.text, "html.parser")
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if not href:
            continue
        abs_url = urljoin(page_url, href)

        links.add(abs_url)
    return links


def crawl_site(domain, keywords, max_pages=50):
    """
    Проста функція краулінгу:
      - Починає з domain
      - Знаходить картинки, завантажує
      - Знаходить посилання на тому ж домені -> переходить туди рекурсивно/ітеративно
      - max_pages: обмежуємо, щоб не обійти геть увесь інтернет ;)
    """
    visited = set()
    to_visit = set(domain)

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)
        print(f"\nCrawling: {current_url}")

        # Парсимо зображення з ключовим словом
        image_urls = scrape_images(current_url, keywords=keywords)
        for keyword_img in image_urls:
            keyword, img = tuple(keyword_img.items())[0]
            download_image(img, save_dir=f"logos_{keyword}")

        # Знаходимо всі внутрішні посилання та записуємо у to_visit тільки не оброблені ще
        links = find_links(current_url)
        to_visit.update(links.difference(visited))

    print(f"\nFinished crawling. Visited {len(visited)} pages.")


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


    # ai generated, coins logo, memes, stock images
    additional_text = "crypto coin memes".replace(" ", "+")

    domains = [f"https://www.google.com/search?q={keyword.replace(' ', '+')}&tbm=isch" for keyword in keywords]

    print(keywords, domains)

    # some how(using QUEUE make one set of need visit links)
    for domain in domains:
        process = Process(target=crawl_site, args=(domain, keywords, 1_000_000))
        process.start()

# TODO: remove do not save files with "?webp"
# TODO: check img size
# TODO: remove visited links periodicly
# TODO: remove broken images
# TODO: check svg image size