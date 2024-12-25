import io
from datetime import datetime
from typing import Annotated, TypedDict

import fastapi
import fastapi.responses as fresponses
import pandas as pd
import pydantic

from tutina.ai import model as m

from ..dependencies import get_tutina_model

router = fastapi.APIRouter(
    prefix="/predictions",
    tags=["predictions"],
)

FeatureTimeSeries = dict[datetime, float]

SVG_MEDIA_TYPE = "image/svg+xml"


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


@router.post("", summary="Create new prediction")
def post_predictions(
    tutina_model: Annotated[m.TutinaModel, fastapi.Depends(get_tutina_model)],
    model_input: TutinaModelInput,
    accept: Annotated[str | None, fastapi.Header()] = None,
) -> dict[str, FeatureTimeSeries]:
    accepted_media_types = _parse_accepted_media_types(accept)
    model_input_dfs = _request_body_to_df(model_input)
    prediction = m.predict_single(tutina_model, model_input_dfs)
    if SVG_MEDIA_TYPE in accepted_media_types or "image/*" in accepted_media_types:
        return _create_plot_response(model_input_dfs["history"], prediction)
    else:
        return prediction.to_dict()
