import os
import shutil
import logging

from flask import Flask, send_file

from config import config

app = Flask(__name__)
logger = logging.getLogger(__name__)


PARSED_IMAGES_DIR = config.SAVE_IMAGES_PATH
ARCHIVE_PATH = f"./{config.IMAGES_ARCHIVE_NAME}.zip"

@app.route("/get_images_archive")
def images_archive():
    if not os.path.exists(PARSED_IMAGES_DIR) or not os.listdir(PARSED_IMAGES_DIR):
        logger.error("Found no images dir, cannot make archive")
        return "No images found", 404
    
    shutil.make_archive(config.IMAGES_ARCHIVE_NAME, "zip", PARSED_IMAGES_DIR)
    shutil.rmtree(config.SAVE_IMAGES_PATH)
    logger.info("Archive was made")
    return send_file(ARCHIVE_PATH, as_attachment=True)


if __name__ == "__main__":
    app.run(host=config.SERVER_HOST, port=config.SERVER_PORT)