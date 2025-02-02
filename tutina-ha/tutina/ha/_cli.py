import asyncio
import contextlib
import functools
import logging
import time
import typing

import schedule
import typer

from tutina.lib.client import create_client
from tutina.lib.settings import Settings

from .forecasts import fetch_forecasts
from .measurements import EntityParser

app = typer.Typer()
logger = logging.getLogger(__name__)


def log_errors(func: typing.Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.debug("Running %s", func.__name__)
            return func(*args, **kwargs)
        except Exception:
            logger.exception("Error when running %s", func.__name__)

    return wrapper


async def _log_errors_async(aw: typing.Awaitable):
    try:
        logger.debug("Running %r", aw)
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
        logger.debug("No HA settings, skipping measurements")
        return

    entity_parser = EntityParser(homeassistant)
    measurements = entity_parser.get_measurements()
    logger.debug("Measurements: %r", measurements)
    hvacs = entity_parser.get_hvacs()
    logger.debug("Hvacs: %r", hvacs)
    opening_states = entity_parser.get_opening_states()
    logger.debug("Opening states: %r", opening_states)

    async def _store_measurements():
        async with contextlib.AsyncExitStack() as exit_stack:
            if tutina := settings.tutina:
                client = await exit_stack.enter_async_context(
                    create_client(
                        str(tutina.base_url),
                        tutina.token_secret.get_secret_value(),
                    )
                )
            else:
                logger.debug("No tutina settings, skipping submitting measurements")
                client = None
            tg = await exit_stack.enter_async_context(asyncio.TaskGroup())
            schedule = get_scheduler(tg)
            if client:
                schedule(client.submit_measurements(measurements))
                schedule(client.submit_hvacs(hvacs))
                schedule(client.submit_opening_states(opening_states))

    asyncio.run(_store_measurements())


@log_errors
def fetch_and_store_forecasts(settings: Settings):
    if (owm := settings.owm) is None:
        logger.debug("No OWM settings, skipping forecasts")
        return

    forecasts = fetch_forecasts(owm)
    logger.debug("Forecasts: %r", forecasts)

    async def _store_forecasts():
        async with contextlib.AsyncExitStack() as exit_stack:
            if tutina := settings.tutina:
                client = await exit_stack.enter_async_context(
                    create_client(
                        str(tutina.base_url),
                        tutina.token_secret.get_secret_value(),
                    )
                )
            else:
                logger.debug("No client settings, skipping submitting forecasts")
                client = None
            tg = await exit_stack.enter_async_context(asyncio.TaskGroup())
            schedule = get_scheduler(tg)
            if client:
                schedule(client.submit_forecasts(forecasts))

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
