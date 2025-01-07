import typing
from datetime import datetime

from . import db, util
from .types import Forecast, Hvac, Measurement, OpeningState

if util.is_testing():
    IGNORE_PREFIX = "OR IGNORE"
else:
    IGNORE_PREFIX = "IGNORE"


async def store_measurements(
    measurements: typing.Iterable[Measurement], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.locations.insert()
        .prefix_with(IGNORE_PREFIX)
        .values([{"slug": measurement.location} for measurement in measurements]),
    )
    locations: dict[str, str] = dict(
        (await connection.execute(db.select(db.locations.c.slug, db.locations.c.id)))
        .tuples()
        .fetchall()
    )
    await connection.execute(
        db.measurements.insert(),
        [
            {
                "location_id": locations[measurement.location],
                **measurement.model_dump(
                    include={"temperature", "humidity", "pressure"}
                ),
            }
            for measurement in measurements
        ],
    )


async def store_hvacs(
    hvacs: typing.Iterable[Hvac], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.hvac_devices.insert()
        .prefix_with(IGNORE_PREFIX)
        .values([{"slug": hvac.device} for hvac in hvacs]),
    )
    devices: dict[str, str] = dict(
        (
            await connection.execute(
                db.select(db.hvac_devices.c.slug, db.hvac_devices.c.id)
            )
        )
        .tuples()
        .fetchall()
    )
    await connection.execute(
        db.hvacs.insert(),
        [
            {
                "device_id": devices[hvac.device],
                **hvac.model_dump(include={"state", "temperature"}),
            }
            for hvac in hvacs
        ],
    )


async def store_opening_states(
    opening_states: typing.Iterable[OpeningState], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.openings.insert()
        .prefix_with(IGNORE_PREFIX)
        .values(
            [
                {"type": opening_state.opening_type, "slug": opening_state.opening}
                for opening_state in opening_states
            ]
        )
    )
    openings = {
        tuple(key): id
        for (*key, id) in (
            await connection.execute(
                db.select(db.openings.c.type, db.openings.c.slug, db.openings.c.id)
            )
        )
        .tuples()
        .fetchall()
    }
    await connection.execute(
        db.opening_states.insert(),
        [
            {
                "opening_id": openings[
                    (opening_state.opening_type, opening_state.opening)
                ],
                **opening_state.model_dump(include={"is_open"}),
            }
            for opening_state in opening_states
        ],
    )


async def store_forecasts(
    forecasts: typing.Iterable[Forecast], *, connection: db.AsyncConnection
) -> None:
    await connection.execute(
        db.forecasts.insert(), [forecast.model_dump() for forecast in forecasts]
    )
