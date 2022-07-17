import cv2 as cv
import magic
import multiprocessing as mp
import numpy as np
import os
from os.path import isfile, join, isdir
from pathlib import Path
import sys

INPUT_MIME_TYPES = ["image/jpeg", "image/tiff", "image/bmp"]

DESTINATION_FORMAT = "png"


def write_image(image, destination_filename):
    if DESTINATION_FORMAT == "png":
        options = [cv.IMWRITE_PNG_COMPRESSION, 6]
    if DESTINATION_FORMAT == "webp":
        options = [cv.IMWRITE_WEBP_QUALITY, 100]

    cv.imwrite(destination_filename, image, options)


def is_bw(image):
    if len(image.shape) < 3:
        return True
    else:
        # RGB but maybe it's really grayscale
        b, g, r = cv.split(image)

        averages = np.zeros(image.shape[0:2])
        averages = averages + r + g + b
        averages /= 3
        pct = np.percentile(np.abs(averages - r), 99)
        return pct < 4.1


def wrapped_process_single_file(args):
    directory, filename, processed_dir = args
    process_single_file(directory, filename, processed_dir)


def process_single_file(directory, filename, processed_dir):
    abs_filename = join(directory, filename)
    image = cv.imread(abs_filename)
    if is_bw(image):
        processed_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    else:
        processed_image = image

    stem = Path(filename).stem

    processed_filename = join(processed_dir, f"{stem}.{DESTINATION_FORMAT}")
    write_image(processed_image, processed_filename)


def process_files(directory, files):
    processed_dir = join(directory, "processed")
    if not isdir(processed_dir):
        os.mkdir(processed_dir)

    with mp.Pool() as pool:
        args = [(directory, f, processed_dir) for f in files]
        pool.map(wrapped_process_single_file, args)


def process_directory(directory):
    files = []
    for filename in os.listdir(directory):
        abs_filename = join(directory, filename)
        if not isfile(abs_filename):
            continue
        if magic.from_file(abs_filename, mime=True) not in INPUT_MIME_TYPES:
            continue

        files.append(filename)

    process_files(directory, files)


if __name__ == "__main__":
    directory = sys.argv[1]
    process_directory(directory)
