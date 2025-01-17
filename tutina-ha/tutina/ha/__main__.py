import asyncio
import functools
import logging
import time
import typing
from datetime import datetime

import click
import schedule

from tutina.lib import db
from tutina.lib.client import create_client
from tutina.lib.data import (
    store_forecasts,
    store_hvacs,
    store_measurements,
    store_opening_states,
)

from .forecasts import fetch_forecasts
from .measurements import EntityParser
from .settings import settings

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def log_errors(func: typing.Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception(f"Error when running {func.__name__}")

    return wrapper


@log_errors
def fetch_and_store_measurements():
    entity_parser = EntityParser()
    measurements = entity_parser.get_measurements()
    hvacs = entity_parser.get_hvacs()
    opening_states = entity_parser.get_opening_states()

    async def _store_measurements():
        engine = db.create_async_engine(settings.get_database_url())
        async with (
            engine.begin() as connection,
            create_client(
                settings.base_url, settings.token_secret.get_secret_value()
            ) as client,
            asyncio.TaskGroup() as tg,
        ):
            tg.create_task(store_measurements(measurements, connection=connection))
            tg.create_task(store_hvacs(hvacs, connection=connection))
            tg.create_task(store_opening_states(opening_states, connection=connection))
            tg.create_task(client.submit_measurements(measurements))
            tg.create_task(client.submit_hvacs(hvacs))
            tg.create_task(client.submit_opening_states(opening_states))
        await engine.dispose()

    asyncio.run(_store_measurements())


@log_errors
def fetch_and_store_forecasts():
    forecasts = fetch_forecasts()

    async def _store_forecasts():
        engine = db.create_async_engine(settings.get_database_url())
        async with (
            engine.begin() as connection,
            create_client(
                settings.base_url, settings.token_secret.get_secret_value()
            ) as client,
            asyncio.TaskGroup() as tg,
        ):
            tg.create_task(store_forecasts(forecasts, connection=connection))
            tg.create_task(client.submit_forecasts(forecasts))
        await engine.dispose()

    asyncio.run(_store_forecasts())


def schedule_job(func: typing.Callable, minutes: int):
    schedule.every(minutes).minutes.at(":00").do(func)


@click.command()
def cli():
    logger.info("Starting tutina...")
    fetch_and_store_measurements()
    fetch_and_store_forecasts()
    schedule_job(fetch_and_store_forecasts, 60)
    schedule_job(fetch_and_store_measurements, 5)
    while True:
        time.sleep(schedule.idle_seconds())
        schedule.run_pending()


if __name__ == "__main__":
    cli()
