import re
import typing
from datetime import datetime

import pydantic
from homeassistant_api import Client

from tutina.lib.models import Hvac, Measurement, OpeningState

from .settings import settings

_measurement_entity_re = re.compile(
    r"^weather_(?P<location>[a-z0-9_-]+)_(temperature|humidity|pressure)$"
)

_hvac_entity_re = re.compile(r"^(?P<device>heat_pump_[a-z0-9_-]+)$")

_opening_re = re.compile(r"^(?P<type>door|window)_(?P<opening>[a-z0-9_-]+)_opening$")


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
