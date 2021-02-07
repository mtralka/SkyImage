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
