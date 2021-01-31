from importlib import reload
import logging
import sys

from skyimage.app import SkyImage as Rectifier


if not sys.warnoptions:
    import warnings

    warnings.simplefilter("default")

reload(logging)
logging.basicConfig(filename="logger.log", level=logging.DEBUG)


"Sky Image"
