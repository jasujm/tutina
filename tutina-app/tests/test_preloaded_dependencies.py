import contextlib
from unittest.mock import AsyncMock

import fastapi

from tutina.app.preloaded_dependencies import PreloadedDependencies


async def test_preloaded_dependencies():
    setup = AsyncMock()
    teardown = AsyncMock()
    dependency = object()
    app = fastapi.FastAPI()

    preloaded_dependencies = PreloadedDependencies()

    @preloaded_dependencies.register
    @contextlib.asynccontextmanager
    async def get_dependency():
        await setup()
        yield dependency
        await teardown()

    async with preloaded_dependencies.preload(app):
        setup.assert_awaited_once()
        teardown.assert_not_awaited()
        assert get_dependency() is dependency

    teardown.assert_awaited_once()
