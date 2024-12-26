import dotenv

dotenv.load_dotenv()

import os.path
import random
from typing import Annotated, Callable

import tomllib
import typer
from dict_deep import deep_get
from rich import print

try:
    import IPython

    console: Callable[[], None] = IPython.embed

except ImportError:

    def console():
        pass


from . import model as m


def main(
    config_file: Annotated[
        typer.FileBinaryRead,
        typer.Option(help="Config file", envvar="TUTINA_CONFIG_FILE"),
    ],
    database_url: Annotated[
        str,
        typer.Option(
            help="Database URL for model training data", envvar="TUTINA_DATABASE_URL"
        ),
    ],
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Drop to REPL after loading data"),
    ] = False,
):
    if config_file:
        with config_file:
            config = tomllib.load(config_file)
    else:
        config = {}

    data_file = deep_get(config, "model.data_file")
    print(f"Loading data from {data_file}")
    data = m.load_data_with_cache(data_file, database_url)
    model_config = deep_get(config, "model.config") or {}
    data = m.clean_data(data, model_config)
    features = m.get_features(data, model_config)

    model_file = deep_get(config, "model.model_file")
    if model_file and os.path.exists(model_file):
        print(f"Loading model from {model_file}")
        model = m.load_model(model_file)
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
