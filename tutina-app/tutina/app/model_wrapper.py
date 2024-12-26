import dotenv

dotenv.load_dotenv()

import logging
import os
import typing

import pandas as pd
import tomllib
from dict_deep import deep_get

from tutina.ai.types import TutinaInputFeatures

if typing.TYPE_CHECKING:
    from tutina.ai.model import TutinaModel

logger = logging.getLogger(__name__)


class TutinaModelWrapper:
    _model: "TutinaModel"

    @classmethod
    def from_config(cls, config):
        from tutina.ai import model as m

        model_file = deep_get(config, "model.model_file")
        logger.info("Loading model from from %s", model_file)
        return cls(m.load_model(model_file))

    @staticmethod
    def plot_prediction(history: pd.DataFrame, prediction: pd.DataFrame):
        from tutina.ai import model as m

        return m.plot_prediction(history, prediction)

    def __init__(self, model: "TutinaModel"):
        self._model = model

    def predict_single(self, model_input: TutinaInputFeatures):
        from tutina.ai import model as m

        return m.predict_single(self._model, model_input)


_tutina_model: TutinaModelWrapper | None = None


def get_tutina_model() -> TutinaModelWrapper:
    global _tutina_model
    if _tutina_model is not None:
        return _tutina_model
    config_file = os.environ["TUTINA_CONFIG_FILE"]
    logger.info("Loading configuration from %s", config_file)
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    _tutina_model = TutinaModelWrapper.from_config(config)
    return _tutina_model
