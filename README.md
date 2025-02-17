# Images Web Crawler
***

## Project Description and Purpose

**Images Web Crawler** is a Python-based project that automates searching and downloading images from the web. It includes a Telegram bot, through which users can control the process of scanning webpages. The main goal of the project is to gather a collection of images by keywords from publicly available sources (including Google Images) for further usage—such as creating an image database, displaying in applications, or performing analytics.


## Installation and Launch

### Docker Deployment

The easiest way is to use **docker-compose**, which sets up three containers: the Telegram bot, a Celery worker, and Redis.

#### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nikita-Goncharov/images-web-crawler.git
   cd crypto-logos-web-crawler
   ```

2. **Create a `.env` file** in the project's root folder and set the required environment variables:
   ```bash
   BOT_API_TOKEN=<your Telegram bot token>
   CELERY_BROKER_URL=redis://redis:6379/0
   ```
   - `BOT_API_TOKEN` must be set to your actual Telegram bot token.
   - `CELERY_BROKER_URL` tells the bot and Celery to use the Redis service (available at host `redis` in the docker-compose network) as the message broker.

3. **Run docker-compose**:
   ```bash
   docker-compose up --build
   ```
   This command will build the Docker image (based on the provided Dockerfile) and start three containers:
   - **tg_bot_crawler** – the Telegram bot container (`python bot.py`).
   - **celery_worker** – the Celery worker and scheduler container (`celery -A tasks worker -B ...`).
   - **redis** – the Redis container (`redis:latest` image).

4. **Check the logs**: The bot container log should show a startup message like “Bot is starting up...”, and the Celery worker should connect successfully to Redis. If everything is running properly, no error messages should appear.

5. **Start using the bot**: Open your Telegram client, search for your bot by its token or username, and send `/start`. The bot should greet you and show its command menu.

To stop the containers, press `Ctrl+C` in the terminal running `docker-compose` or run `docker-compose down` in another shell.

## Usage Examples

Below is an example usage scenario after the bot is running:

1. **Start**: Send `/start` to the bot. It will greet you and display an action menu, usually including:
   ```
   1) Show Keywords
   2) Add Keyword
   3) Remove Keyword
   4) Start Search
   5) Stop Search
   ```

2. **Add Keywords**: Press **Add Keyword** (or type it). The bot will ask for a keyword. Send `nature`. The bot confirms the keyword has been added. You can add more, such as `dog` or `cat`, each time pressing **Add Keyword**.

3. **Show Keywords**: Press **Show Keywords**. If not empty, the bot lists currently stored keywords, e.g., *"Current keywords: nature, cat, dog"*. If there are none, it tells you there are no keywords.

4. **Start Search**: Press **Start Search**. The bot will begin crawling web pages (in the background via Celery) and reply with a message like: *“Crawling started. Keywords: dog, cat, nature. To stop crawling press: Stop Search.”* It will scan through Google Images and other links, searching for relevant images. Discovered images matching the keywords are saved in `parsed_images/<keyword>/...` folders.

5. **Stop Search**: Press **Stop Search** at any time. The bot will halt the crawling process and confirm with *“Crawling stopped.”* All previously downloaded images remain in the `parsed_images` directory.

6. **Repeat**: You can start the search again anytime. Just ensure you have some keywords added before starting (the bot will not search if the list is empty).

*Note*: The system automatically runs a duplication-cleanup task (`remove_duplicates`) every 20 seconds, removing duplicate files based on their MD5 checksum.

## Project Structure

The repository includes the following key files and modules:

- **`bot.py`**: Main Telegram bot script using Aiogram. It defines command handlers and message handlers for keywords management (`/start`, “Show Keywords”, “Add Keyword”, “Remove Keyword”, “Start Search”, “Stop Search”) and starts the crawling process through an instance of `Crawler`.

- **`crawler.py`**: Contains the **Crawler** class, which manages the web crawling logic:
  - Constructor (`__init__`) sets up search URLs for each keyword.
  - `start_parsing()` initiates an asynchronous crawling process (in a separate `multiprocessing.Process`).
  - `crawl_site(url, shared_data)` performs recursive page crawling, finds `<img>` tags, matches them to keywords, and triggers image download tasks.
  - `scrape_images(page_url)` uses BeautifulSoup to parse images and anchors on a page. Images matching the current keyword(s) are queued for download via Celery.

- **`tasks.py`**: Contains Celery tasks:
  - `download_image(...)` – downloads an image from the given URL and saves it locally. If the image is invalid, it is removed.
  - `remove_duplicates(path)` – walks through all image files in `parsed_images` and deletes duplicates using MD5 checksums. Scheduled to run every 20 seconds by Celery Beat.

- **`celery_app.py`**: Celery configuration (broker URL, result backend, and a `beat_schedule` for periodic tasks).

- **`requirements.txt`**: List of Python dependencies required by the project.

- **`Dockerfile`**: Builds a Docker image based on `python:3.11-slim`, installing `libcairo2` and all required Python packages.

- **`docker-compose.yaml`**: Defines three services for Docker Compose: `tg_bot_crawler` (the bot), `celery_worker` (the Celery worker + beat), and `redis`.

- **`parsed_images/`**: Created automatically to store downloaded images, organized into subfolders named after each keyword.

## License

No explicit license is provided in the repository. By default, all rights are reserved by the author. For usage or distribution, please contact the author for permissions. If you need clarification about using parts of the code, feel free to open an issue or send a message via GitHub.