import logging
import typing

import pandas as pd

from tutina.ai.types import TutinaInputFeatures

if typing.TYPE_CHECKING:
    from tutina.ai.model import TutinaModel


class TutinaModelWrapper:
    _model: "TutinaModel"

    @classmethod
    def from_model_file(cls, model_file):
        from tutina.ai import model as m

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
