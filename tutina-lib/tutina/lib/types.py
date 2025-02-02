from datetime import datetime
from enum import Enum
from typing import Annotated

import pydantic


class HvacState(Enum):
    off = "off"
    auto = "auto"
    cool = "cool"
    heat = "heat"
    dry = "dry"
    fan_only = "fan_only"


class OpeningType(Enum):
    door = "door"
    window = "window"


class Measurement(pydantic.BaseModel):
    """A single measurement from thermometer/hygrometer/barometer"""

    location: str
    temperature: float | None
    humidity: float | None
    pressure: float | None


class Hvac(pydantic.BaseModel):
    """HVAC device state"""

    device: str
    state: HvacState | None
    temperature: float | None


class OpeningState(pydantic.BaseModel):
    """Door/window opening state"""

    opening_type: OpeningType
    opening: str
    is_open: bool


class Forecast(pydantic.BaseModel):
    """Weather forecast at a single point of time"""

    reference_timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    status: str


class FeatureTimeSeries(pydantic.RootModel):
    """Time series of numeric data"""

    root: dict[datetime, float]


class FeaturesByName(pydantic.RootModel):
    """Collection of feature time series by name"""

    root: dict[str, FeatureTimeSeries]


class ForecastFeatures(pydantic.BaseModel):
    """Weather forecast as time series"""

    temperature: FeatureTimeSeries


class TutinaModelInput(pydantic.BaseModel):
    """Serialized input to the tutina model"""

    history: Annotated[
        FeaturesByName,
        pydantic.Field(
            description="History of measurements prior to the predicted timesteps",
            json_schema_extra={
                "example": {
                    "temperature_bedroom": {
                        "2020-01-01T07:00:00Z": 20.0,
                        "2020-01-01T08:00:00Z": 21.0,
                    },
                    "temperature_outdoor": {
                        "2020-01-01T07:00:00Z": -5.0,
                        "2020-01-01T08:00:00Z": -4.0,
                    },
                }
            },
        ),
    ]
    control: Annotated[
        FeaturesByName,
        pydantic.Field(
            description="Control input for the predicted timesteps",
            json_schema_extra={
                "example": {
                    "hvac_state_heat_radiator": {
                        "2020-01-01T09:00:00Z": 1.0,
                        "2020-01-01T10:00:00Z": 1.0,
                    },
                    "hvac_temperature_heat_radiator": {
                        "2020-01-01T09:00:00Z": 21.0,
                        "2020-01-01T10:00:00Z": 21.0,
                    },
                }
            },
        ),
    ]
    forecasts: Annotated[
        ForecastFeatures,
        pydantic.Field(
            description="Weather forecast for the predicted timesteps",
            json_schema_extra={
                "example": {
                    "temperature": {
                        "2020-01-01T08:00:00Z": -4.5,
                        "2020-01-01T09:00:00Z": -3.5,
                        "2020-01-01T10:00:00Z": -3.5,
                    }
                }
            },
        ),
    ]
