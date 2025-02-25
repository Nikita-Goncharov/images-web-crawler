# Images Web Crawler
***
## Description

**Images Web Crawler** is a Python-based application that automatically searches for and downloads images from the web based on user-provided keywords. It provides a Telegram bot interface (built with Aiogram) that allows users to add keywords and control the crawling process (start or stop) directly from a chat. The crawler fetches images from public sources like Google Images and organizes the downloaded files by keyword. This tool can help in building image datasets or gathering pictures for projects and analytics.

## Project Structure

- **bot.py** – The main Telegram bot script (using Aiogram). It handles user commands and menu actions (such as listing current keywords, adding new keywords, removing keywords, and starting or stopping the image search). When a search is triggered, the bot uses the `Crawler` class to run the crawling process asynchronously in the background via Celery.
- **crawler.py** – Defines the `Crawler` class that handles the web crawling logic. It builds search URLs for each keyword (including Google Images queries) and uses BeautifulSoup to parse pages for image links. The crawler recursively scans pages, finds `<img>` tags related to the target keywords, and dispatches image download tasks to Celery workers.
- **tasks.py** – Contains Celery task definitions for asynchronous processing:
  - `download_image(url, keyword)`: Downloads an image from the given URL and saves it to the directory by keyword(skipping or removing any invalid images and duplicates).
- **celery_app.py** – Configures the Celery application (message broker URL, result backend, and scheduled tasks).
- **server.py** – A simple Flask web server that provides an endpoint to download all collected images as a single zip file. When you access `/get_images_archive` on this server, it packages the parsed images folder into a zip archive and returns it (and can optionally clear the images directory after archiving). This runs as a separate service (see Docker Compose configuration) on port 5000, allowing easy retrieval of the collected images.
- **config.py** – The configuration module that loads environment variables (via `dotenv`) and provides configuration values to the application. It defines settings such as the Telegram bot token, Celery broker URL, Flask server host/port, and the path for saving images.
- **Dockerfile** – Defines the Docker image for the project. It uses a Python 3.11-slim base image, installs system dependencies (e.g. `libcairo2` required by some libraries), and then installs all Python packages listed in `requirements.txt`.
- **docker-compose.yaml** – Docker Compose configuration that sets up the multi-container environment. It defines four services:
  - `tg_bot_crawler` – runs the Telegram bot (executes `python bot.py`).
  - `flask_server` – runs the Flask web server for image archive (executes `python server.py` on port 5000).
  - `celery_worker` – runs the Celery worker and scheduler (executes the Celery worker with Beat to schedule tasks).
  - `redis` – a Redis instance (using the `redis:latest` image, serving as the message broker for Celery).
- **requirements.txt** – List of Python dependencies required by the project (libraries such as aiogram for the bot, beautifulsoup4 for parsing HTML, celery, redis, etc.).

## Running with Docker Compose

Using Docker Compose is the easiest way to set up and run all components of the Images Web Crawler. Make sure you have **Docker** and **Docker Compose** installed on your system, then follow these steps:

1. **Clone the repository**:  
   ```bash
   git clone https://github.com/Nikita-Goncharov/images-web-crawler.git
   cd images-web-crawler
   ```
2. **Create a `.env` file** in the project root and set the required environment variables:  
   ```env
   BOT_API_TOKEN=<your_telegram_bot_token>
   CELERY_BROKER_URL=redis://redis:6379/0
   SAVE_IMAGES_PATH=imges
   IMAGES_ARCHIVE_NAME=images_archive
   SERVER_HOST=host
   SERVER_HOST_HUMANABLE=host
   SERVER_PORT=port
   ```  
   - `BOT_API_TOKEN` should be your Telegram bot's API token (obtained from BotFather on Telegram).  
   - `CELERY_BROKER_URL` tells Celery where to find the Redis broker. The default value above points to the `redis` service on the Docker network (container name "redis" on port 6379, database 0).  
   - `SERVER_HOST`(`SERVER_HOST_HUMANABLE`)/`SERVER_PORT` for the Flask server configuration.
   - `SAVE_IMAGES_PATH` directory where images will be saved in container.
   - `IMAGES_ARCHIVE_NAME` name of output archive.
3. **Launch the application with Docker Compose**:  
   ```bash
   docker-compose up --build
   ```  
   This will build the Docker image and start up all four containers (Telegram bot, Flask server, Celery worker with scheduler, and Redis). On the first run, it will also create a directory in your project folder to store downloaded images.
4. **Verify all services are running**:  
   - The Telegram bot container's log should show a startup message like "*Bot is starting up...*".  
   - The Celery worker container should log that it connected to Redis and is ready (it will also log periodic tasks execution for removing duplicates).  
   - The Flask server container should report that it's running (listening on port 5000).  
   - If anything is misconfigured (for example, an invalid bot token or missing environment variable), you will see error messages in the corresponding container's logs.
5. **Use the Telegram bot**: Open Telegram and start a chat with your bot (find it by the username you set up with the given token). Send the `/start` command to initiate the conversation. The bot should greet you and present a menu of commands (such as **Show Keywords**, **Add Keyword**, **Remove Keyword**, **Start Search**, **Stop Search`). Now you can:  
   - **Add a keyword** – Choose "Add Keyword" (or type the command) and send a keyword (for example, `nature`). The bot will confirm the keyword was added. You can add multiple keywords one by one.  
   - **Start the search** – Choose "Start Search" to begin crawling. The bot will start the background crawling process via Celery and usually respond with a message like "*Crawling started...*". It will search for images matching the keywords you added. All found images will be downloaded into the folder (organized by keyword).  
   - **Stop the search** – You can stop the crawling at any time by choosing "Stop Search". The bot will halt the background crawler. Any images downloaded before stopping will remain saved.  
   - **Show keywords** – At any time, you can check which keywords are stored by choosing "Show Keywords". This will list all current keywords the bot will use for searching.
6. **Download collected images (optional)**: If you want to retrieve all the images that have been collected, you can use the Flask web service. Open a web browser (or use curl) to visit **`http://host:port/get_images_archive`**. This will generate a ZIP archive of the parsed images directory and prompt a download. After the archive is created, the server will delete the images folder to clean up (so the next search starts fresh). Be sure to stop the crawling process before downloading the archive, to ensure all files are zipped.
7. **Shut down**: When you're done, stop the Docker Compose services by pressing `Ctrl+C` in the terminal where it's running. Alternatively, you can open another terminal in the project directory and run `docker-compose down` to stop and remove the containers. This will **not** delete any images or data saved on your host.