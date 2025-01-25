import logging
import logging.config as lconfig

from rich.logging import RichHandler

from .settings import Settings


def setup_logging(settings: Settings):
    if (logging_config := settings.logging) is None:
        logging.basicConfig(handlers=[RichHandler()])
        logging.getLogger("tutina").setLevel(logging.INFO)
    else:
        lconfig.dictConfig(logging_config)
