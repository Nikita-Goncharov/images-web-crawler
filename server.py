import os
import shutil
from flask import Flask, send_file

from config import config

app = Flask(__name__)

PARSED_IMAGES_DIR = "./parsed_images/"  # Директорія з зображеннями
ARCHIVE_PATH = "./parsed_images.zip"   # Шлях до архіву

@app.route("/get_images_archive")
def images_archive():
    """Створює та віддає архів із зображеннями"""
    if not os.path.exists(PARSED_IMAGES_DIR) or not os.listdir(PARSED_IMAGES_DIR):
        return "No images found", 404

    # Створюємо новий архів
    shutil.make_archive("parsed_images", "zip", PARSED_IMAGES_DIR)
    
    return send_file(ARCHIVE_PATH, as_attachment=True)


if __name__ == "__main__":
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT)