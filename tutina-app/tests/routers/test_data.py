import pytest
import sqlalchemy as sa
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient

from tutina.lib import db, models


@pytest.fixture
def measurements(faker) -> list[models.Measurement]:
    return [
        models.Measurement(
            location=faker.pystr(),
            temperature=faker.pyfloat(),
            humidity=faker.pyfloat(),
            pressure=faker.pyfloat(),
        )
        for _ in range(5)
    ]


@pytest.fixture
def hvacs(faker) -> list[models.Hvac]:
    return [
        models.Hvac(
            device=faker.pystr(),
            state=faker.enum(db.HvacState),
            temperature=faker.pyfloat(),
        )
        for _ in range(5)
    ]


@pytest.fixture
def opening_states(faker) -> list[models.OpeningState]:
    return [
        models.OpeningState(
            opening_type=faker.enum(db.OpeningType),
            opening=faker.pystr(),
            is_open=faker.pybool(),
        )
        for _ in range(5)
    ]


@pytest.fixture
def forecasts(faker) -> list[models.Forecast]:
    return [
        models.Forecast(
            reference_timestamp=faker.date_time(),
            temperature=faker.pyfloat(),
            humidity=faker.pyfloat(),
            pressure=faker.pyfloat(),
            wind_speed=faker.pyfloat(),
            status=faker.pystr(),
        )
        for _ in range(5)
    ]


async def test_post_measurements(client, measurements, mock_database_engine):
    serialized_measurements = jsonable_encoder(measurements)
    res = client.post("/data/measurements", json=serialized_measurements)
    assert res.status_code == 204
    async with mock_database_engine.begin() as connection:
        measurements_in_db = [
            models.Measurement(**row)
            for row in (
                await connection.execute(
                    sa.select(
                        db.locations.c.slug.label("location"),
                        db.measurements.c.temperature,
                        db.measurements.c.humidity,
                        db.measurements.c.pressure,
                    ).select_from(db.locations.join(db.measurements))
                )
            ).mappings()
        ]
    assert measurements_in_db == measurements


async def test_post_measurements_empty_request(client, mock_database_engine):
    res = client.post("/data/measurements", json=[])
    assert res.status_code == 422


async def test_post_hvacs(client, hvacs, mock_database_engine):
    serialized_hvacs = jsonable_encoder(hvacs)
    res = client.post("/data/hvacs", json=serialized_hvacs)
    assert res.status_code == 204
    async with mock_database_engine.begin() as connection:
        hvacs_in_db = [
            models.Hvac(**row)
            for row in (
                await connection.execute(
                    sa.select(
                        db.hvac_devices.c.slug.label("device"),
                        db.hvacs.c.state,
                        db.hvacs.c.temperature,
                    ).select_from(db.hvac_devices.join(db.hvacs))
                )
            ).mappings()
        ]
    assert hvacs_in_db == hvacs


async def test_post_hvacs_empty_request(client, mock_database_engine):
    res = client.post("/data/hvacs", json=[])
    assert res.status_code == 422


async def test_post_opening_states(client, opening_states, mock_database_engine):
    serialized_opening_states = jsonable_encoder(opening_states)
    res = client.post("/data/opening_states", json=serialized_opening_states)
    assert res.status_code == 204
    async with mock_database_engine.begin() as connection:
        opening_states_in_db = [
            models.OpeningState(**row)
            for row in (
                await connection.execute(
                    sa.select(
                        db.openings.c.type.label("opening_type"),
                        db.openings.c.slug.label("opening"),
                        db.opening_states.c.is_open,
                    ).select_from(db.openings.join(db.opening_states))
                )
            ).mappings()
        ]
    assert opening_states_in_db == opening_states


async def test_post_opening_states_empty_request(client, mock_database_engine):
    res = client.post("/data/opening_states", json=[])
    assert res.status_code == 422


async def test_post_forecasts(client, forecasts, mock_database_engine):
    serialized_forecasts = jsonable_encoder(forecasts)
    res = client.post("/data/forecasts", json=serialized_forecasts)
    assert res.status_code == 204
    async with mock_database_engine.begin() as connection:
        forecasts_in_db = [
            models.Forecast(**row)
            for row in (
                await connection.execute(
                    sa.select(
                        db.forecasts.c.reference_timestamp,
                        db.forecasts.c.temperature,
                        db.forecasts.c.humidity,
                        db.forecasts.c.pressure,
                        db.forecasts.c.wind_speed,
                        db.forecasts.c.status,
                    )
                )
            ).mappings()
        ]
    assert forecasts_in_db == forecasts


async def test_post_forecasts_empty_request(client, mock_database_engine):
    res = client.post("/data/forecasts", json=[])
    assert res.status_code == 422
