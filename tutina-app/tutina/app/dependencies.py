import dotenv

dotenv.load_dotenv()

import functools
import logging
import os
from typing import Annotated

import fastapi
import tomllib
from dict_deep import deep_get

from tutina.lib.db import create_async_engine

from .model_wrapper import TutinaModelWrapper

logger = logging.getLogger(__name__)


@functools.cache
def _load_config():
    config_file = os.environ["TUTINA_CONFIG_FILE"]
    logger.info("Loading configuration from %s", config_file)
    with open(config_file, "rb") as f:
        return tomllib.load(f)


@functools.cache
def _load_tutina_model(model_file: str):
    logger.info("Loading model from from %s", model_file)
    return TutinaModelWrapper.from_model_file(model_file)


@functools.cache
def _create_engine(database_url: str):
    return create_async_engine(database_url)


def get_config():
    return _load_config()


def get_database_engine():
    database_url = os.environ["TUTINA_DATABASE_URL"]
    return _create_engine(database_url)


def get_tutina_model(
    config: Annotated[dict, fastapi.Depends(get_config)],
) -> TutinaModelWrapper:
    model_file = deep_get(config, "model.model_file")
    return _load_tutina_model(model_file)
