import typing
from datetime import datetime

import pydantic

from . import db


class Measurement(pydantic.BaseModel):
    location: str
    temperature: typing.Optional[float]
    humidity: typing.Optional[float]
    pressure: typing.Optional[float]


class Hvac(pydantic.BaseModel):
    device: str
    state: typing.Optional[db.HvacState]
    temperature: typing.Optional[float]


class OpeningState(pydantic.BaseModel):
    opening_type: db.OpeningType
    opening: str
    is_open: bool


class Forecast(pydantic.BaseModel):
    reference_timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    status: str


async def store_measurements(
    measurements: typing.Iterable[Measurement], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.locations.insert()
        .prefix_with("IGNORE")
        .values([{"slug": measurement.location} for measurement in measurements]),
    )
    locations = dict(
        (
            await connection.execute(db.select(db.locations.c.slug, db.locations.c.id))
        ).fetchall()
    )
    await connection.execute(
        db.measurements.insert(),
        [
            {
                "location_id": locations[measurement.location],
                **measurement.dict(include={"temperature", "humidity", "pressure"}),
            }
            for measurement in measurements
        ],
    )


async def store_hvacs(
    hvacs: typing.Iterable[Hvac], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.hvac_devices.insert()
        .prefix_with("IGNORE")
        .values([{"slug": hvac.device} for hvac in hvacs]),
    )
    devices = dict(
        (
            await connection.execute(
                db.select(db.hvac_devices.c.slug, db.hvac_devices.c.id)
            )
        ).fetchall()
    )
    await connection.execute(
        db.hvacs.insert(),
        [
            {
                "device_id": devices[hvac.device],
                **hvac.dict(include={"state", "temperature"}),
            }
            for hvac in hvacs
        ],
    )


async def store_opening_states(
    opening_states: typing.Iterable[OpeningState], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.openings.insert()
        .prefix_with("IGNORE")
        .values(
            [
                {"type": opening_state.opening_type, "slug": opening_state.opening}
                for opening_state in opening_states
            ]
        )
    )
    openings = {
        tuple(key): id
        for (*key, id) in await connection.execute(
            db.select(db.openings.c.type, db.openings.c.slug, db.openings.c.id)
        )
    }
    await connection.execute(
        db.opening_states.insert(),
        [
            {
                "opening_id": openings[
                    (opening_state.opening_type, opening_state.opening)
                ],
                **opening_state.dict(include={"is_open"}),
            }
            for opening_state in opening_states
        ],
    )


async def store_forecasts(
    forecasts: typing.Iterable[Forecast], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.forecasts.insert(), [forecast.dict() for forecast in forecasts]
    )
