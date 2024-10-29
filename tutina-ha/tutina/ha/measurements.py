import re
import typing
from datetime import datetime

import pydantic
from homeassistant_api import Client

from tutina.lib import db
from .settings import settings

_measurement_entity_re = re.compile(
    r"^weather_(?P<location>[a-z0-9_-]+)_(temperature|humidity|pressure)$"
)

_hvac_entity_re = re.compile(r"^(?P<device>heat_pump_[a-z0-9_-]+)$")

_opening_re = re.compile(r"^(?P<type>door|window)_(?P<opening>[a-z0-9_-]+)_opening$")


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


_client = Client(
    str(settings.homeassistant_api_url),
    settings.homeassistant_api_token.get_secret_value(),
)


class EntityParser:
    def __init__(self):
        self._entities = _client.get_entities()

    def get_measurements(self) -> list[Measurement]:
        sensor_entities = self._entities["sensor"].entities

        def _get_measurement(location, measurement) -> typing.Optional[str]:
            if (
                entity := sensor_entities.get(f"weather_{location}_{measurement}")
            ) and entity.state.state != "unavailable":
                return entity.state.state
            return None

        sensor_locations = set(
            m.group("location")
            for key in sensor_entities.keys()
            if (m := _measurement_entity_re.match(key)) is not None
        )
        return [
            Measurement(
                location=location,
                **{
                    measurement: _get_measurement(location, measurement)
                    for measurement in ["temperature", "humidity", "pressure"]
                },
            )
            for location in sensor_locations
        ]

    def get_hvacs(self) -> list[Hvac]:
        return [
            Hvac(
                device=device,
                state=(
                    state if (state := entity.state.state) != "unavailable" else None
                ),
                temperature=entity.state.attributes.get("temperature"),
            )
            for (device, entity) in self._entities["climate"].entities.items()
        ]

    def get_opening_states(self) -> list[OpeningState]:
        openings = [
            OpeningState(
                opening_type=m.group("type"),
                opening=m.group("opening"),
                is_open=entity.state.state == "on",
            )
            for (opening, entity) in self._entities["binary_sensor"].entities.items()
            if (m := _opening_re.match(opening)) is not None
        ]

        return openings


def store_measurements(
    measurements: typing.Iterable[Measurement], *, connection: db.Connection
) -> None:
    connection.execute(
        db.locations.insert()
        .prefix_with("IGNORE")
        .values([{"slug": measurement.location} for measurement in measurements]),
    )
    locations = dict(
        connection.execute(db.select(db.locations.c.slug, db.locations.c.id)).fetchall()
    )
    connection.execute(
        db.measurements.insert(),
        [
            {
                "location_id": locations[measurement.location],
                **measurement.dict(include={"temperature", "humidity", "pressure"}),
            }
            for measurement in measurements
        ],
    )


def store_hvacs(hvacs: typing.Iterable[Hvac], *, connection: db.Connection) -> None:
    connection.execute(
        db.hvac_devices.insert()
        .prefix_with("IGNORE")
        .values([{"slug": hvac.device} for hvac in hvacs]),
    )
    devices = dict(
        connection.execute(
            db.select(db.hvac_devices.c.slug, db.hvac_devices.c.id)
        ).fetchall()
    )
    connection.execute(
        db.hvacs.insert(),
        [
            {
                "device_id": devices[hvac.device],
                **hvac.dict(include={"state", "temperature"}),
            }
            for hvac in hvacs
        ],
    )


def store_opening_states(
    opening_states: typing.Iterable[OpeningState], *, connection: db.Connection
) -> None:
    connection.execute(
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
        for (*key, id) in connection.execute(
            db.select(db.openings.c.type, db.openings.c.slug, db.openings.c.id)
        )
    }
    connection.execute(
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
