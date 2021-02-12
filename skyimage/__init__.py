from importlib import reload
import logging
import sys

from skyimage.app import SkyImage as SkyImage
from skyimage.stations import Ground
from skyimage.stations import Sky


if not sys.warnoptions:
    import warnings

    warnings.simplefilter("default")

reload(logging)
logging.basicConfig(filename="logger.log", level=logging.DEBUG)


"Sky Image"
