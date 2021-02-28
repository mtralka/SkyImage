from importlib import reload
import logging
import sys

from rich.traceback import install as rich_trace

from skyimage.app import SkyImage


if not sys.warnoptions:
    import warnings
    warnings.simplefilter("default")

reload(logging)
logging.basicConfig(filename="logger.log", level=logging.INFO)

rich_trace()

"Sky Image"
