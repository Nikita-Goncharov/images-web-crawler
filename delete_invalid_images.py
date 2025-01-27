import os

import cv2
import numpy as np
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


def hamming_distance(hash1, hash2):
    # Count the number of set bits in XOR
    return bin(hash1 ^ hash2).count('1')


def main():
    directory_list = os.listdir()
    logo_dirs = [directory for directory in directory_list if "logos_" in directory]
    for logo_dir in logo_dirs:
        logo_images = os.listdir(logo_dir)
        for logo_img in logo_images:
            if ".svg" not in logo_img:
                try:
                    img = Image.open(f"{logo_dir}/{logo_img}")
                    width, height = img.size
                    if width < 240 or height < 240 or "webp" in logo_img:  # TODO: check .svg
                        print("REMOVED")
                        os.remove(f"{logo_dir}/{logo_img}")
                except UnidentifiedImageError:
                    os.remove(f"{logo_dir}/{logo_img}")


def rm_duplicates():
    directory_list = os.listdir()
    logo_dirs = [directory for directory in directory_list if "logos_" in directory]

    for logo_dir in logo_dirs:
        logo_images = os.listdir(logo_dir)
        for first_logo_img in logo_images:
            if ".svg" not in first_logo_img:
                for second_logo_img in logo_images:
                    if ".svg" not in second_logo_img:
                        first_hash = dhash(cv2.imread(f"{logo_dir}/{first_logo_img}"))
                        second_hash = dhash(cv2.imread(f"{logo_dir}/{second_logo_img}"))
                        if first_hash == second_hash:
                            print(f"{logo_dir}/{first_logo_img}", f"{logo_dir}/{second_logo_img}")
                            print("EQUAL")
                        # print(hamming_distance(first_hash, second_hash))
        break


if __name__ == "__main__":
    main()
    rm_duplicates()