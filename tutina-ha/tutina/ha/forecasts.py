import typing
from datetime import datetime, timezone

import pydantic
import requests

from tutina.lib.settings import OwmSettings
from tutina.lib.types import Forecast

_DEFAULT_PARAMS = {
    "units": "metric",
}


def fetch_forecasts(owm_settings: OwmSettings) -> list[Forecast]:
    forecasts = requests.get(
        "https://api.openweathermap.org/data/3.0/onecall",
        params={
            "appid": owm_settings.api_key.get_secret_value(),
            **_DEFAULT_PARAMS,
            **owm_settings.coordinates.model_dump(),
        },
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
