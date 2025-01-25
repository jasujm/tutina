import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Annotated

import typer
from rich import print

from .logging import setup_logging
from .settings import Settings

app = typer.Typer()

for subcommand in entry_points(group="tutina_cli"):
    app.add_typer(subcommand.load())


@app.callback()
def main(
    ctx: typer.Context,
    config_file: Annotated[Path | None, typer.Option(help="Config file path")] = None,
):
    """
    Tutina: Predict and control indoor temperatures
    """

    if config_file:
        if config_file.exists():
            Settings.set_config_file(config_file)
        else:
            print(f"File {config_file.absolute()} does not exist", file=sys.stderr)
            sys.exit(1)

    settings = Settings()
    setup_logging(settings)

    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings
