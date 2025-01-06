import functools
import logging
import os
from typing import Annotated

import fastapi
import tomllib
from dict_deep import deep_get

from tutina.lib.db import create_async_engine
from tutina.lib.settings import Settings

from .model_wrapper import TutinaModelWrapper

logger = logging.getLogger(__name__)


@functools.cache
def _load_config(config_file: str):
    logger.info("Loading configuration from %s", config_file)
    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)
    return Settings(**config_data)


@functools.cache
def _load_tutina_model(model_file: str):
    logger.info("Loading model from from %s", model_file)
    return TutinaModelWrapper.from_model_file(model_file)


@functools.cache
def _create_engine(database_url: str):
    return create_async_engine(database_url)


def get_config() -> Settings:
    config_file = os.environ["TUTINA_CONFIG_FILE"]
    return _load_config(config_file)


def get_database_engine(config: Annotated[Settings, fastapi.Depends(get_config)]):
    database_url = config.database.url.get_secret_value()
    return _create_engine(database_url)


def get_tutina_model(
    config: Annotated[Settings, fastapi.Depends(get_config)],
) -> TutinaModelWrapper:
    return _load_tutina_model(config.model.model_file)
