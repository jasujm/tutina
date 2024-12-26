import typing

if typing.TYPE_CHECKING:
    from pandas import DataFrame


class TutinaInputFeatures(typing.TypedDict):
    history: "DataFrame"
    control: "DataFrame"
    forecasts: "DataFrame"
