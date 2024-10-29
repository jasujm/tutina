import typing
from datetime import datetime, timezone

import pydantic
import requests

from tutina.lib import db
from .settings import settings

_DEFAULT_PARAMS = {
    "appid": settings.owm_api_key.get_secret_value(),
    "units": "metric",
    **settings.owm_coordinates.dict(),
}


class Forecast(pydantic.BaseModel):
    reference_timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    status: str


def fetch_forecasts() -> list[Forecast]:
    forecasts = requests.get(
        "https://api.openweathermap.org/data/3.0/onecall",
        params=_DEFAULT_PARAMS,
        timeout=30,
    ).json()
    return [
        Forecast(
            reference_timestamp=datetime.fromtimestamp(forecast["dt"], tz=timezone.utc),
            temperature=forecast["temp"],
            humidity=forecast["humidity"],
            pressure=forecast["pressure"],
            wind_speed=forecast["wind_speed"],
            status=forecast["weather"][0]["main"],
        )
        for forecast in forecasts["hourly"]
    ]


def store_forecasts(
    forecasts: typing.Iterable[Forecast], *, connection: db.Connection
) -> None:
    connection.execute(
        db.forecasts.insert(), [forecast.dict() for forecast in forecasts]
    )
