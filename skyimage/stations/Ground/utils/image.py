from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
from skimage.io import imread


def open_image(path: str):
    return imread(path)


def open_mask():
    return np.load("skyimage\stations\Ground\mask.npy")


def show_image(img):
    plt.imshow(img)
    plt.show()


def extract_color_bands(img):

    R = img[:, :, 0] / 255
    G = img[:, :, 1] / 255
    B = img[:, :, 2] / 255

    return R, G, B


def calc_SI(R, B):

    SI = (B - R) / (B + R)
    # SI[SI == 0] = np.nan

    return SI


def calc_BI(R, G, B):

    BI = (R + G + B) / 3
    # BI[BI == 0] = np.nan

    return BI


def extract_stats(array) -> dict:

    mean = np.nanmean(array)
    max = np.nanmax(array)
    min = np.nanmin(array)

    return {"mean": mean, "max": max, "min": min}
