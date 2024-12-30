from typing import Annotated

import annotated_types as at
import fastapi
import pydantic

from tutina.lib import db, models

from ..dependencies import get_database_engine

router = fastapi.APIRouter(
    prefix="/data",
    tags=["data"],
)


@router.post("/measurements", status_code=204, summary="Submit new measurement data")
async def post_measurements(
    measurements: Annotated[list[models.Measurement], at.MinLen(1)],
    engine: Annotated[db.AsyncEngine, fastapi.Depends(get_database_engine)],
) -> None:
    async with engine.begin() as connection:
        await models.store_measurements(measurements, connection=connection)


@router.post("/hvacs", status_code=204, summary="Submit new HVAC states")
async def post_hvacs(
    hvacs: Annotated[list[models.Hvac], at.MinLen(1)],
    engine: Annotated[db.AsyncEngine, fastapi.Depends(get_database_engine)],
) -> None:
    async with engine.begin() as connection:
        await models.store_hvacs(hvacs, connection=connection)


@router.post("/opening_states", status_code=204, summary="Submit new opening states")
async def post_opening_states(
    opening_states: Annotated[list[models.OpeningState], at.MinLen(1)],
    engine: Annotated[db.AsyncEngine, fastapi.Depends(get_database_engine)],
) -> None:
    async with engine.begin() as connection:
        await models.store_opening_states(opening_states, connection=connection)


@router.post("/forecasts", status_code=204, summary="Submit new weather forecasts")
async def post_forecasts(
    forecasts: Annotated[list[models.Forecast], at.MinLen(1)],
    engine: Annotated[db.AsyncEngine, fastapi.Depends(get_database_engine)],
) -> None:
    async with engine.begin() as connection:
        await models.store_forecasts(forecasts, connection=connection)
