import contextlib
import enum
import functools
from datetime import datetime, timedelta, timezone
from typing import Iterable

import aiohttp
import jwt
import orjson

from .types import Forecast, Hvac, Measurement, OpeningState

EXP_TIME_IN_MINUTES = 5


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
        serialized_data = orjson.dumps([m.model_dump() for m in measurements])
        async with self._session.post(
            "/data/measurements", data=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_hvacs(self, hvacs: Iterable[Hvac]):
        serialized_data = orjson.dumps([h.model_dump() for h in hvacs])
        async with self._session.post(
            "/data/hvacs", data=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_opening_states(self, opening_states: Iterable[OpeningState]):
        serialized_data = orjson.dumps([o.model_dump() for o in opening_states])
        async with self._session.post(
            "/data/opening_states", data=serialized_data, headers=self._get_headers()
        ):
            pass

    async def submit_forecasts(self, forecasts: Iterable[Forecast]):
        serialized_data = orjson.dumps([f.model_dump() for f in forecasts])
        async with self._session.post(
            "/data/forecasts", data=serialized_data, headers=self._get_headers()
        ):
            pass

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self._generate_token()}",
            "Content-Type": "application/json",
        }

    def _generate_token(self):
        return jwt.encode({"exp": _get_exp()}, self._token_secret)


@contextlib.asynccontextmanager
async def create_client(base_url: str, token_secret: str):
    async with aiohttp.ClientSession(
        base_url=base_url, raise_for_status=True
    ) as session:
        yield TutinaClient(session, token_secret)
