import json
import os
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient


def _fixture_from_file(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path) as f:
        ret = json.load(f)
    return ret


@pytest.fixture(scope="module")
def model_input():
    return _fixture_from_file("model-input.json")


@pytest.fixture(scope="module")
def prediction():
    return _fixture_from_file("prediction.json")


def test_post_predictions_json(
    client: TestClient, mock_tutina_model, model_input, prediction
):
    mock_tutina_model.predict_single.return_value = pd.DataFrame.from_dict(prediction)
    response = client.post("/predictions", json=model_input)
    assert response.status_code == 200
    assert response.json() == prediction


def test_post_predictions_svg(
    client: TestClient, mock_tutina_model, model_input, prediction
):
    SVG_CONTENT = b"<svg></svg>"
    mock_figure = Mock(savefig=lambda f, **_: f.write(SVG_CONTENT))
    mock_tutina_model.predict_single.return_value = pd.DataFrame.from_dict(prediction)
    mock_tutina_model.plot_prediction.return_value = (mock_figure, None)
    response = client.post(
        "/predictions", headers={"accept": "image/svg+xml"}, json=model_input
    )
    assert response.status_code == 200
    assert response.content == SVG_CONTENT
