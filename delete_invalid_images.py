import io
import os
import hashlib

import cv2
import numpy as np
import cairosvg
from multiprocessing import Process

from PIL import Image, UnidentifiedImageError


def dhash(image, hash_size=8):
    """
    Compute the 'difference hash' for an image
    :param image: BGR or grayscale image (numpy array)
    :param hash_size: size of the hash dimension
    :return: 64-bit integer (or a hex string) representing the hash
    """
    # 1) Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # 2) Resize to (hash_size+1) x hash_size
    #    e.g., 9x8. Each row we compare adjacent pixels
    resized = cv2.resize(gray, (hash_size + 1, hash_size))

    # 3) Compute differences row by row
    diff = resized[:, 1:] > resized[:, :-1]

    # 4) Convert bool array to integer (64 bits)
    #    E.g., for an 8x8 = 64 bits total
    hash_val = 0
    for val in diff.flatten():
        hash_val = (hash_val << 1) | int(val)
    return hash_val


def render_svg_to_png_bytes(svg_path, dpi=96):
    """
    Converts SVG to PNG in memory at the given DPI,
    returns PNG data as bytes.
    """
    with open(svg_path, 'rb') as f:
        svg_data = f.read()
    png_data = cairosvg.svg2png(bytestring=svg_data, dpi=dpi)
    return png_data


def get_rendered_size(svg_path, dpi=96):
    png_data = render_svg_to_png_bytes(svg_path, dpi=dpi)
    # Read the PNG data into PIL to get dimensions
    img = Image.open(io.BytesIO(png_data))
    return img.size  # (width, height) in pixels


def set_correct_extension(img_path: str) -> str:
    new_img_path = img_path
    try:
        if "?fit=" in new_img_path:  # remove symbols after extension
            new_img_path = new_img_path.split("?fit=")[0]

        if ".jpeg" in new_img_path:  # change .jpeg to .jpg
            new_img_path = new_img_path.replace(".jpeg", ".jpg")

        os.rename(img_path, new_img_path)
    except:
        pass
    return new_img_path


def rm_small_images(img_path):
    try:
        img = Image.open(img_path)
        width, height = img.size
        if width < 240 or height < 240:
            print("REMOVED")
            os.remove(img_path)
    except:  # UnidentifiedImageError   # can not open image
        if os.path.exists(img_path):
            os.remove(img_path)


def rm_duplicates():
    directory_list = os.listdir()
    logo_dirs = [directory for directory in directory_list if "logos_" in directory]

    for logo_dir in logo_dirs:
        logo_images = os.listdir(logo_dir)
        logo_images = [img for img in logo_images if ".svg" not in img]  # exclude .svg

        for first_logo_img in logo_images:
            for second_logo_img in logo_images:
                if first_logo_img != second_logo_img:
                    try:
                        first_img_path = f"{logo_dir}/{first_logo_img}"
                        second_img_path = f"{logo_dir}/{second_logo_img}"
                        print(first_img_path, second_img_path)
                        first_hash = dhash(cv2.imread(first_img_path))
                        second_hash = dhash(cv2.imread(second_img_path))
                        if first_hash == second_hash:  # print(hamming_distance(first_hash, second_hash))
                            print("EQUAL")
                            os.remove(second_img_path)
                    except:
                        pass


def file_md5(path, chunk_size=8192):
    """Return MD5 hash (hex string) of a file."""
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def remove_exact_duplicates(folder):
    """
    Scans 'folder' for exact duplicate SVGs (or any files).
    Removes duplicates, keeps one copy of each unique file.
    """
    seen_hashes = {}
    for filename in os.listdir(folder):
        if not filename.lower().endswith(".svg"):
            continue
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            file_hash = file_md5(filepath)
            if file_hash in seen_hashes:
                # Duplicate detected
                print(f"[DUPLICATE] Removing {filepath} (same as {seen_hashes[file_hash]})")
                os.remove(filepath)
            else:
                # First time we see this hash
                seen_hashes[file_hash] = filepath


def rm_svg_duplicates():
    first_level_dir = "./"
    dirs = os.listdir(first_level_dir)
    logo_dirs = [directory for directory in dirs if "logos_" in directory]

    for logo_dir in logo_dirs:
        try:
            remove_exact_duplicates(logo_dir)
        except:
            pass

def main():
    first_level_dir = "./"
    dirs = os.listdir(first_level_dir)
    logo_dirs = [directory for directory in dirs if "logos_" in directory]

    for logo_dir in logo_dirs:
        current_dir = os.path.join(first_level_dir, logo_dir)
        images = os.listdir(current_dir)
        for img in images:
            image_path = os.path.join(current_dir, img)
            if ".svg" in img:
                w, h = get_rendered_size(image_path)
                if w < 240 or h < 240:
                    os.remove(image_path)
            else:
                new_image_path = set_correct_extension(image_path)
                if "webp" in new_image_path:
                    os.remove(new_image_path)
                else:
                    print(new_image_path)
                    rm_small_images(new_image_path)


if __name__ == "__main__":
    Process(target=main).start()
    Process(target=rm_duplicates).start()
    Process(target=rm_svg_duplicates).start()