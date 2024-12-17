import dotenv

dotenv.load_dotenv()

import contextlib
import logging
import os
from datetime import datetime
from typing import TypedDict

import fastapi
import pandas as pd
import pydantic
import tomllib
from dict_deep import deep_get

from tutina.ai import model as m

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def _lifespan(_app):
    global _tutina_model
    config_file = os.environ["TUTINA_CONFIG_FILE"]
    logger.info("Loading configuration from %s", config_file)
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    model_file = deep_get(config, "model.model_file")
    logger.info("Loading model from from %s", model_file)
    _tutina_model = m.load_model(model_file)
    yield


app = fastapi.FastAPI(lifespan=_lifespan)
_tutina_model: m.TutinaModel = None

FeatureTimeSeries = dict[datetime, float]


class Forecasts(TypedDict):
    temperature: list[float]


class TutinaModelInput(pydantic.BaseModel):
    history: dict[str, FeatureTimeSeries]
    control: dict[str, FeatureTimeSeries]
    forecasts: Forecasts


def _request_body_to_df(model_input: TutinaModelInput):
    return m.TutinaInputFeatures(
        history=pd.DataFrame.from_dict(model_input.history),
        control=pd.DataFrame.from_dict(model_input.control),
        forecasts=pd.DataFrame.from_dict(model_input.forecasts),
    )


@app.post("/predictions")
def post_predictions(
    model_input: TutinaModelInput,
) -> dict[str, FeatureTimeSeries]:
    model_input_dfs = _request_body_to_df(model_input)
    prediction = m.predict_single(_tutina_model, model_input_dfs)
    return prediction.to_dict()
