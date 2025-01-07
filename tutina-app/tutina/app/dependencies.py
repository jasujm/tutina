import functools
import logging
import os
from pathlib import Path
from typing import Annotated

import fastapi
import tomllib

from tutina.lib.db import create_async_engine
from tutina.lib.settings import Settings

from .model_wrapper import TutinaModelWrapper

logger = logging.getLogger(__name__)


@functools.cache
def _load_config():
    return Settings()


@functools.cache
def _load_tutina_model(model_file: Path):
    logger.info("Loading model from from %s", model_file)
    return TutinaModelWrapper.from_model_file(model_file)


@functools.cache
def _create_engine(database_url: str):
    return create_async_engine(database_url)


def get_config() -> Settings:
    return _load_config()


def get_database_engine(config: Annotated[Settings, fastapi.Depends(get_config)]):
    database_url = config.database.url.get_secret_value()
    return _create_engine(database_url)


def get_tutina_model(
    config: Annotated[Settings, fastapi.Depends(get_config)],
) -> TutinaModelWrapper:
    return _load_tutina_model(config.model.model_file)
