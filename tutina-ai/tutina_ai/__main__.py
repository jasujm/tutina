import dotenv

dotenv.load_dotenv()

import random
from typing import Callable

import rich_click as click
import tomllib
from rich import print

try:
    import IPython

    console: Callable[[], None] = IPython.embed

except ImportError:

    def console():
        pass


from . import model as m


@click.command()
@click.option("--data-file", help="Cache file for data", type=click.Path())
@click.option("--config-file", help="Config file", type=click.File("rb"))
@click.option(
    "--interactive", "-i", help="Drop to REPL after loading data", is_flag=True
)
def main(data_file: str | None, config_file, interactive: bool):
    if config_file:
        with config_file:
            config = tomllib.load(config_file)
    else:
        config = None

    data = m.load_data_with_cache(data_file)
    data = m.clean_data(data, config)
    features = m.get_features(data, config)
    train_dataset, validation_dataset, test_dataset = (
        m.split_data_to_train_and_validation(features)
    )
    model, history = m.create_and_train_model(train_dataset, validation_dataset)
    evaluation = model.evaluate(test_dataset, return_dict=True)
    print("Model evaluation result:", evaluation)

    start = random.randrange(0, len(features.index) - 30)
    sample = features.iloc[start : start + 30, :]
    cutoff = sample.index[11]
    prediction = m.predict_single(model, sample, cutoff)
    m.plot_comparison(sample, prediction)

    if interactive:
        console()


if __name__ == "__main__":
    main(auto_envvar_prefix="TUTINA")
