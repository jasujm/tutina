import asyncio
import functools
import logging
import time
import typing

import schedule
import typer

from tutina.lib import db
from tutina.lib.client import create_client
from tutina.lib.data import (
    store_forecasts,
    store_hvacs,
    store_measurements,
    store_opening_states,
)
from tutina.lib.settings import Settings

from .forecasts import fetch_forecasts
from .measurements import EntityParser

app = typer.Typer()
logger = logging.getLogger(__name__)


def log_errors(func: typing.Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception("Error when running %s", func.__name__)

    return wrapper


async def _log_errors_async(aw: typing.Awaitable):
    try:
        await aw
    except Exception:
        logger.exception("Error when running %r", aw)


def get_scheduler(tg: asyncio.TaskGroup):
    def _schedule(aw: typing.Awaitable):
        tg.create_task(_log_errors_async(aw))

    return _schedule


@log_errors
def fetch_and_store_measurements(settings: Settings):
    if (homeassistant := settings.homeassistant) is None:
        logger.info("No HA settings, skipping measurements")
        return

    entity_parser = EntityParser(homeassistant)
    measurements = entity_parser.get_measurements()
    hvacs = entity_parser.get_hvacs()
    opening_states = entity_parser.get_opening_states()

    async def _store_measurements():
        engine = db.create_async_engine(settings.database.get_url())
        async with (
            engine.begin() as connection,
            create_client(
                str(settings.tutina.base_url),
                settings.tutina.token_secret.get_secret_value(),
            ) as client,
            asyncio.TaskGroup() as tg,
        ):
            schedule = get_scheduler(tg)
            schedule(store_measurements(measurements, connection=connection))
            schedule(store_hvacs(hvacs, connection=connection))
            schedule(store_opening_states(opening_states, connection=connection))
            schedule(client.submit_measurements(measurements))
            schedule(client.submit_hvacs(hvacs))
            schedule(client.submit_opening_states(opening_states))
        await engine.dispose()

    asyncio.run(_store_measurements())


@log_errors
def fetch_and_store_forecasts(settings: Settings):
    if (owm := settings.owm) is None:
        logger.info("No OWM settings, skipping forecasts")
        return

    forecasts = fetch_forecasts(owm)

    async def _store_forecasts():
        engine = db.create_async_engine(settings.database.get_url())
        async with (
            engine.begin() as connection,
            create_client(
                str(settings.tutina.base_url),
                settings.tutina.token_secret.get_secret_value(),
            ) as client,
            asyncio.TaskGroup() as tg,
        ):
            schedule = get_scheduler(tg)
            schedule(store_forecasts(forecasts, connection=connection))
            schedule(client.submit_forecasts(forecasts))
        await engine.dispose()

    asyncio.run(_store_forecasts())


def schedule_job(func: typing.Callable, minutes: int):
    schedule.every(minutes).minutes.at(":00").do(func)


@app.command()
def ha(ctx: typer.Context):
    """
    Home Assistant addon main command
    """

    settings: Settings = ctx.obj["settings"]

    logger.info("Starting tutina...")
    fetch_and_store_measurements(settings)
    fetch_and_store_forecasts(settings)
    schedule_job(functools.partial(fetch_and_store_forecasts, settings), 60)
    schedule_job(functools.partial(fetch_and_store_measurements, settings), 5)
    while True:
        if idle_seconds := schedule.idle_seconds():
            time.sleep(idle_seconds)
        schedule.run_pending()
