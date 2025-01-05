import contextlib
import enum
import functools
import json
from datetime import datetime, timedelta, timezone
from typing import Iterable

import aiohttp
import jwt

from .types import Forecast, Hvac, Measurement, OpeningState

EXP_TIME_IN_MINUTES = 5


def _json_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, enum.Enum):
        return o.value
    raise TypeError(f"Cannot serialize {o!r}")


_json_serialize = functools.partial(json.dumps, default=_json_default)


def _get_exp():
    exp_as_datetime = datetime.now(timezone.utc) + timedelta(
        minutes=EXP_TIME_IN_MINUTES
    )
    return int(exp_as_datetime.timestamp())


class TutinaClient:
    def __init__(self, session: aiohttp.ClientSession, token_secret: str):
        self._session = session
        self._token_secret = token_secret

    async def submit_measurements(self, measurements: Iterable[Measurement]):
        serialized_data = [m.model_dump() for m in measurements]
        async with self._session.post(
            "/data/measurements", json=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_hvacs(self, hvacs: Iterable[Hvac]):
        serialized_data = [h.model_dump() for h in hvacs]
        async with self._session.post(
            "/data/hvacs", json=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_opening_states(self, opening_states: Iterable[OpeningState]):
        serialized_data = [o.model_dump() for o in opening_states]
        async with self._session.post(
            "/data/opening_states", json=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_forecasts(self, forecasts: Iterable[Forecast]):
        serialized_data = [f.model_dump() for f in forecasts]
        async with self._session.post(
            "/data/forecasts", json=serialized_data, headers=self._get_headers()
        ):
            pass

    def _get_headers(self):
        return {"Authorization": f"Bearer {self._generate_token()}"}

    def _generate_token(self):
        return jwt.encode({"exp": _get_exp()}, self._token_secret)


@contextlib.asynccontextmanager
async def create_client(base_url: str, token_secret: str):
    async with aiohttp.ClientSession(
        base_url=base_url, raise_for_status=True, json_serialize=_json_serialize
    ) as session:
        yield TutinaClient(session, token_secret)
