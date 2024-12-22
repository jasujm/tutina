import dotenv

dotenv.load_dotenv()

import contextlib
import io
import logging
import os
from datetime import datetime
from typing import Annotated, TypedDict

import fastapi
import fastapi.responses as fresponses
import pandas as pd
import pydantic
import tomllib
from dict_deep import deep_get

from tutina.ai import model as m

SVG_MEDIA_TYPE = "image/svg+xml"

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
    temperature: FeatureTimeSeries


class TutinaModelInput(pydantic.BaseModel):
    history: dict[str, FeatureTimeSeries]
    control: dict[str, FeatureTimeSeries]
    forecasts: Forecasts


def _request_body_to_df(model_input: TutinaModelInput):
    return m.TutinaInputFeatures(
        history=pd.DataFrame.from_dict(model_input.history),
        control=pd.DataFrame.from_dict(model_input.control),
        forecasts=pd.DataFrame.from_dict(model_input.forecasts),  # type: ignore
    )


def _parse_accepted_media_types(accept: str | None):
    if not accept:
        return []
    return [media_type.strip().partition(";")[0] for media_type in accept.split(",")]


def _create_plot_response(history: pd.DataFrame, prediction: pd.DataFrame):
    fig, _ = m.plot_prediction(history, prediction)
    f = io.BytesIO()
    fig.savefig(f, format="svg")
    f.seek(0)
    return fresponses.StreamingResponse(f, media_type=SVG_MEDIA_TYPE)


@app.post(
    "/predictions",
    responses={
        200: {
            "content": {SVG_MEDIA_TYPE: {}},
        }
    },
)
def post_predictions(
    model_input: TutinaModelInput, accept: Annotated[str, fastapi.Header()] = None
) -> dict[str, FeatureTimeSeries]:
    accepted_media_types = _parse_accepted_media_types(accept)
    model_input_dfs = _request_body_to_df(model_input)
    prediction = m.predict_single(_tutina_model, model_input_dfs)
    if SVG_MEDIA_TYPE in accepted_media_types or "image/*" in accepted_media_types:
        return _create_plot_response(model_input_dfs["history"], prediction)
    else:
        return prediction.to_dict()
