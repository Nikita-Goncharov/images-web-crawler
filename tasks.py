import hashlib
import io
import logging
import os
from datetime import datetime

import cv2
import redis
import numpy as np
import cairosvg
import requests
from PIL import Image, UnidentifiedImageError


from celery_app import app

logger = logging.getLogger(__name__)
redis_client = redis.Redis("redis")

def render_svg_to_png_bytes(svg_path, dpi=96):
    """
    Converts SVG to PNG in memory at the given DPI,
    returns PNG data as bytes.
    """
    with open(svg_path, "rb") as f:
        svg_data = f.read()
    png_data = cairosvg.svg2png(bytestring=svg_data, dpi=dpi)
    return png_data


def get_image_size(image_path, dpi=96):
    """Try to open image, if it is .png, .jpg, .gif,
    else if .svg we are need to convert to .png

    """
    try:
        img = cv2.imread(image_path)
        h, w, _ = img.shape
        return (w, h)
    except UnidentifiedImageError:  # error if image is svg 
        png_data = render_svg_to_png_bytes(image_path, dpi=dpi)
        img = Image.open(io.BytesIO(png_data))
        return img.size  # (width, height) in pixels
    except FileNotFoundError:
        return (0, 0)


def has_ext(filename: str, extenstions: list[str] | None = None) -> bool:
    if extenstions is None:
        valid_extensions = [".png", ".jpg", ".gif", ".svg", ".PNG"]
    else:
        valid_extensions = extenstions
    
    if any([ext in filename for ext in valid_extensions]):
        return True
    
    logger.info("Image is not valid. Unknown extension in image")
    return False


def is_image_valid(path: str) -> bool:
    try:
        if not has_ext(path):
            return False

        w, h = get_image_size(path)
        if w > 240 and h > 240:
            return True
    except Exception as ex:
        logger.error(f"Exception when image validation: {str(ex)}")
    
    logger.info("Image is not valid. small image size")
    return False


@app.task
def download_image(absolute_src: str, save_dir: str):
    try:
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"Received image path: {absolute_src}")
        _, file_ext = os.path.splitext(absolute_src)  # get file extension from URL
        logger.info(f"Found extension: {file_ext}")
        
        # make correct file extension
        file_ext = file_ext.replace("?", " ").replace("#", " ").replace("&", " ").replace("@", " ")
        file_ext = file_ext.split(" ")[0]
        file_ext = file_ext if file_ext != ".jpeg" else ".jpg"
        logger.info(f"Clean extension: {file_ext}")
        
        new_image_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        path = os.path.join(save_dir, f"{new_image_name}{file_ext}")
        logger.info(f"Image path to save: {path}")
        # TODO: check ext before saving ??
        response = requests.get(absolute_src, timeout=5)
        response.raise_for_status()
        
        image_raw_data = response.content
        image_hash = hashlib.md5(image_raw_data).hexdigest()
        if not redis_client.sismember("image_hashes", image_hash):  # check if image already saved
            image = np.asarray(bytearray(image_raw_data), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            cv2.imwrite(path, image)
            
            redis_client.sadd("image_hashes", image_hash)
            
            # check image, if not valid - delete
            if not is_image_valid(path):
                os.remove(path)
            else:
                redis_client.incr("saved_images_count")
                logger.info("Image saved")
        else:
            logger.info("Duplicate image, do not save")
    except Exception as ex:
        logger.error(f"Error downloading: {absolute_src}: {ex}")
