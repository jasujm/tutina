import functools
import logging
import time
import typing
from datetime import datetime

import click
import schedule

from tutina.lib import db
from .forecasts import fetch_forecasts, store_forecasts
from .measurements import (
    EntityParser,
    store_hvacs,
    store_measurements,
    store_opening_states,
)

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
    with db.engine.begin() as connection:
        store_measurements(entity_parser.get_measurements(), connection=connection)
        store_hvacs(entity_parser.get_hvacs(), connection=connection)
        store_opening_states(entity_parser.get_opening_states(), connection=connection)


@log_errors
def fetch_and_store_forecasts():
    forecasts = fetch_forecasts()
    with db.engine.begin() as connection:
        store_forecasts(forecasts, connection=connection)


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
