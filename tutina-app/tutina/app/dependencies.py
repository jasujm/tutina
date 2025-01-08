import asyncio
import contextlib
import logging
from typing import AsyncIterator

from tutina.lib.db import AsyncEngine, create_async_engine
from tutina.lib.settings import Settings

from .model_wrapper import TutinaModelWrapper
from .preloaded_dependencies import PreloadedDependencies

logger = logging.getLogger(__name__)
preloaded_dependencies = PreloadedDependencies()
_settings = Settings()


def get_config() -> Settings:
    return _settings


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_database_engine() -> AsyncIterator[AsyncEngine]:
    database_url = _settings.database.url.get_secret_value()
    engine = create_async_engine(database_url)
    yield engine
    await engine.dispose()


@preloaded_dependencies.register
@contextlib.asynccontextmanager
async def get_tutina_model() -> AsyncIterator[TutinaModelWrapper]:
    model_file = _settings.model.model_file
    logger.info("Loading model from from %s", model_file)
    loop = asyncio.get_event_loop()
    model = await loop.run_in_executor(
        None, TutinaModelWrapper.from_model_file, model_file
    )
    yield model
