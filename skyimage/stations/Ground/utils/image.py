import numpy as np


"""

pixel processing utilities for GroundImage class

"""


def f_above_or_below(p: np.ndarray, boundary: np.ndarray) -> int:
    """Determine if given point `p` is above
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

    if p[0] < np.min(boundary[:, 0]) or p[0] > np.max(boundary[:, 0]):
        raise ValueError("`(BI, SI)` point falls outside `boundary` decision domain")

    idx: int = None

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
