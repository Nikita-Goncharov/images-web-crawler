import hashlib
import io
import logging
import os
from datetime import datetime

import cairosvg
import requests
from PIL import Image


from celery_app import app

logger = logging.getLogger(__name__)


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
        img = Image.open(image_path)
    except Exception as ex:
        png_data = render_svg_to_png_bytes(image_path, dpi=dpi)
        img = Image.open(io.BytesIO(png_data))
    return img.size  # (width, height) in pixels


def is_image_valid(absolute_src: str) -> bool:
    try:
        if ".webp" in absolute_src:  # do not download .webp images
            logger.info("Image is not valid. '.webp' extension in image")
            return False

        w, h = get_image_size(absolute_src)
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
        _, file_ext = os.path.splitext(absolute_src)  # get file extension from URL

        # make correct file extension
        file_ext = file_ext.replace("?", " ").replace("#", " ").replace("&", " ")
        file_ext = file_ext.split(" ")[0]
        file_ext = file_ext if file_ext != ".jpeg" else ".jpg"

        new_image_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        path = os.path.join(save_dir, f"{new_image_name}{file_ext}")

        resp = requests.get(absolute_src, stream=True, timeout=5)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # check image, if not valid - delete
        if not is_image_valid(path):
            os.remove(path)
        else:
            logger.info("Image saved")
    except Exception as ex:
        logger.error(f"Error downloading: {absolute_src}: {ex}")


def file_md5(path, chunk_size=8192):
    """Return MD5 hash (hex string) of a file."""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


@app.task
def remove_duplicates(path):
    if not os.path.exists(path):
        return
    
    directory_list = os.listdir(path)
    for logo_dir in directory_list:
        seen_hashes = {}
        image_dir_path = os.path.join(path, logo_dir)
        for filename in os.listdir(image_dir_path):
            filepath = os.path.join(image_dir_path, filename)
            if not os.path.isfile(filepath):
                continue
            
            file_hash = file_md5(filepath)
            if file_hash in seen_hashes:
                # Duplicate detected
                logger.info(f"[DUPLICATE] Removing {filepath} (same as {seen_hashes[file_hash]})")
                os.remove(filepath)
            else:
                # First time we see this hash
                seen_hashes[file_hash] = filepath
