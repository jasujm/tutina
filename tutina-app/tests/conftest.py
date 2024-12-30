import contextlib
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from tutina.app import dependencies as dep
from tutina.app.app import app
from tutina.lib.db import create_async_engine
from tutina.lib.db import metadata as db_metadata


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_tutina_model():
    _mock_tutina_model = mock.Mock()
    return _mock_tutina_model


@pytest.fixture
async def mock_database_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(db_metadata.create_all)
    return engine


@pytest.fixture(autouse=True)
def dependency_overrides(mock_tutina_model, mock_database_engine):
    app.dependency_overrides = {
        dep.get_tutina_model: (lambda: mock_tutina_model),
        dep.get_database_engine: (lambda: mock_database_engine),
    }
    yield
    app.dependency_overrides = {}
