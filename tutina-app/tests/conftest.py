from unittest import mock

import pytest

import tutina.app.model_wrapper as mw
from tutina.app.app import app


@pytest.fixture
def mock_tutina_model():
    _mock_tutina_model = mock.Mock()
    return _mock_tutina_model


@pytest.fixture(autouse=True)
def dependency_overrides(mock_tutina_model):
    app.dependency_overrides = {mw.get_tutina_model: lambda: mock_tutina_model}
    yield
    app.dependency_overrides = {}
