import dotenv

dotenv.load_dotenv()

import contextlib
import logging
import os

import tomllib
from dict_deep import deep_get

from tutina.ai import model as m

logger = logging.getLogger(__name__)

_tutina_model: m.TutinaModel = None


@contextlib.asynccontextmanager
async def lifespan(_app):
    global _tutina_model
    config_file = os.environ["TUTINA_CONFIG_FILE"]
    logger.info("Loading configuration from %s", config_file)
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    model_file = deep_get(config, "model.model_file")
    logger.info("Loading model from from %s", model_file)
    _tutina_model = m.load_model(model_file)
    yield


def get_tutina_model():
    return _tutina_model
