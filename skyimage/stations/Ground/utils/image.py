from typing import Dict
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from skimage.io import imread


def open_image(path: str):
    return imread(path)


def open_mask(path: Optional[str] =
              "skyimage\\stations\\Ground\\mask.npy"):

    return np.load(path)


def show_image(img):
    plt.imshow(img)
    plt.show()


def save_image(name: str, img):
    plt.imsave(name, img)


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

    mean = round(np.nanmean(array), 2)
    max = round(np.nanmax(array), 2)
    min = round(np.nanmin(array), 2)

    return {"mean": mean, "max": max, "min": min}


def f_above_or_below(p: np.ndarray, boundary: np.ndarray) -> int:
    """ Determine if given point `p` is above
        or below decision `boundary`

        Parameters
        ----------
        p : numpy.ndarray
            given point

        boundary: numpy.ndarray
            decision boundary line

        Returns
        ----------
        int
            `1` if point is above domain
            else (implied below) `0`

        Raises
        ----------
        KeyError
            If `point` falls outside domain of decision `boundary`

        Examples
        ----------
        # TODO 

        """

    if p[0] < np.min(boundary[:, 0]) or \
            p[0] > np.max(boundary[:, 0]):
        raise ValueError(
            "`(BI, SI)` point falls outside `boundary` decision line")

    idx = None

    for i in range(boundary.shape[0]):
        if p[1] > boundary[i, 1]:
            idx = i
            break
    if idx is None:
        return 0
    elif p[0] < boundary[idx, 0]:
        return 0
    else:
        return 1
