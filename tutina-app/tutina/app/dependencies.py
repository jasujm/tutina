import asyncio
import contextlib
import logging
from typing import AsyncIterator

from tutina.lib.db import AsyncEngine, create_async_engine
from tutina.lib.settings import Settings

from .model_wrapper import TutinaModelWrapper
from .preloaded_dependencies import PreloadedDependencies

preloaded_dependencies = PreloadedDependencies()


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_logger():
    # setting up logging assuming this is running in uvicorn
    # TODO: make configurable by using the logging settings from config
    logger = logging.getLogger("tutina")
    logger.setLevel(logging.INFO)
    if handler := logging.getHandlerByName("default"):
        logger.addHandler(handler)
    logger.propagate = False
    yield logger


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_config() -> Settings:
    logger = get_logger()
    logger.info("Loading settings from %r", Settings.model_config.get("toml_file"))
    loop = asyncio.get_event_loop()
    settings = await loop.run_in_executor(None, Settings)
    yield settings


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_database_engine() -> AsyncIterator[AsyncEngine]:
    database_config = get_config().database
    logger = get_logger()
    logger.info("Loading database engine with %s", database_config)
    engine = create_async_engine(database_config.url.get_secret_value())
    yield engine
    await engine.dispose()


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_tutina_model() -> AsyncIterator[TutinaModelWrapper]:
    model_file = get_config().model.get_model_file_path(write=False)
    logger = get_logger()
    logger.info("Loading model from from %s", model_file)
    loop = asyncio.get_event_loop()
    model = await loop.run_in_executor(
        None, TutinaModelWrapper.from_model_file, model_file
    )
    yield model
