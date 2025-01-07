import dotenv

dotenv.load_dotenv()

import random
from pathlib import Path
from typing import Annotated, Callable

import tomllib
import typer
from rich import print

from tutina.lib.settings import Settings

try:
    import IPython

    console: Callable[[], None] = IPython.embed

except ImportError:

    def console():
        pass


from . import model as m


def main(
    config_file: Annotated[Path | None, typer.Option(help="Config file")] = None,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Drop to REPL after loading data"),
    ] = False,
):
    if config_file:
        if config_file.exists():
            Settings.set_config_file(config_file)
        else:
            print(f"File {config_file.absolute()} does not exist")

    settings = Settings()

    data_file = settings.model.data_file
    print(f"Loading data from {data_file}")
    data = m.load_data_with_cache(
        str(data_file), settings.database.url.get_secret_value()
    )
    model_config = settings.model.config
    data = m.clean_data(data, model_config)
    features = m.get_features(data, model_config)

    model_file = settings.model.model_file
    if model_file and model_file.is_file():
        print(f"Loading model from {model_file}")
        model = m.load_model(str(model_file))
    else:
        print(f"Model file not found, training")
        train_dataset, validation_dataset, test_dataset = (
            m.split_data_to_train_and_validation(features)
        )
        model, history = m.create_and_train_model(train_dataset, validation_dataset)
        evaluation = model.evaluate(test_dataset, return_dict=True)
        print("Model evaluation result:", evaluation)
        print(f"Saving model to {model_file}")
        if model_file:
            model.save(model_file)

    start = random.randrange(0, len(features.index) - 30)
    sample = features.iloc[start : start + 30, :]
    cutoff = sample.index[11]
    model_input = m.features_to_model_input(sample, cutoff)
    prediction = m.predict_single(model, model_input)
    m.plot_comparison(sample, prediction)

    if interactive:
        console()


if __name__ == "__main__":
    typer.run(main)
