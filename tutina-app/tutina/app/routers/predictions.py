import io
from datetime import datetime
from typing import Annotated, TypedDict

import fastapi
import fastapi.responses as fresponses
import pandas as pd
import pydantic

from tutina.lib.types import (
    FeaturesByName,
    FeatureTimeSeries,
    ForecastFeatures,
    TutinaModelInput,
)

from ..dependencies import get_tutina_model
from ..model_wrapper import TutinaInputFeatures, TutinaModelWrapper

router = fastapi.APIRouter(
    prefix="/predictions",
    tags=["predictions"],
)


SVG_MEDIA_TYPE = "image/svg+xml"


def _request_body_to_df(model_input: TutinaModelInput):
    return TutinaInputFeatures(
        history=pd.DataFrame.from_dict(model_input.history.model_dump()),
        control=pd.DataFrame.from_dict(model_input.control.model_dump()),
        forecasts=pd.DataFrame.from_dict(model_input.forecasts.model_dump()),
    )


def _parse_accepted_media_types(accept: str | None):
    if not accept:
        return []
    return [media_type.strip().partition(";")[0] for media_type in accept.split(",")]


def _create_plot_response(
    tutina_model: TutinaModelWrapper, history: pd.DataFrame, prediction: pd.DataFrame
):
    fig, _ = tutina_model.plot_prediction(history, prediction)
    f = io.BytesIO()
    fig.savefig(f, format="svg")
    f.seek(0)
    return fresponses.StreamingResponse(f, media_type=SVG_MEDIA_TYPE)


@router.post(
    "",
    summary="Create new prediction",
    responses={
        200: {
            "content": {
                "application/json": {
                    "schema": {
                        "example": {
                            "temperature_bedroom": {
                                "2020-01-01T09:00:00Z": 21.0,
                                "2020-01-01T10:00:00Z": 20.5,
                            },
                            "temperature_outdoor": {
                                "2020-01-01T09:00:00Z": -5.0,
                                "2020-01-01T10:00:00Z": -4.0,
                            },
                        },
                    }
                },
                SVG_MEDIA_TYPE: {},
            }
        }
    },
)
def post_predictions(
    tutina_model: Annotated[TutinaModelWrapper, fastapi.Depends(get_tutina_model)],
    model_input: TutinaModelInput,
    accept: Annotated[
        str | None,
        fastapi.Header(
            description="By default, return the response in `application/json`. Request `image/*` or `image/svg+xml` for a plot in SVG format."
        ),
    ] = None,
) -> FeaturesByName:
    accepted_media_types = _parse_accepted_media_types(accept)
    model_input_dfs = _request_body_to_df(model_input)
    prediction = tutina_model.predict_single(model_input_dfs)
    if SVG_MEDIA_TYPE in accepted_media_types or "image/*" in accepted_media_types:
        return _create_plot_response(
            tutina_model, model_input_dfs["history"], prediction
        )
    else:
        return prediction.to_dict()
