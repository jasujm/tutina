from datetime import datetime

import more_itertools as mi
import pydantic
import pytest
from dateutil.relativedelta import relativedelta
from hypothesis import assume, given
from hypothesis import strategies as st

from tutina.lib.types import (
    FeaturesByName,
    FeatureTimeSeries,
    TutinaModelInput,
    _has_valid_spacing,
)

heterogenous_timestamps = st.lists(
    st.datetimes(), min_size=2, max_size=10, unique=True
).filter(lambda ts: not _has_valid_spacing(ts))


@st.composite
def spaced_timestamps(
    draw,
    start=st.datetimes(allow_imaginary=False),
    length=st.integers(min_value=1, max_value=10),
):
    start_val = draw(start)
    length_val = draw(length)
    return [start_val + relativedelta(hours=h) for h in range(length_val)]


@st.composite
def time_series(draw, timestamps=spaced_timestamps()):
    ts = draw(timestamps)
    features = draw(st.lists(st.floats(), min_size=len(ts), max_size=len(ts)))
    return dict(zip(ts, features))


@st.composite
def features_by_name(draw, timestamps=spaced_timestamps()):
    ts = draw(timestamps)
    return draw(
        st.dictionaries(keys=st.text(), values=time_series(st.just(ts)), min_size=1)
    )


@st.composite
def forecast_features(draw, timestamps=spaced_timestamps()):
    return draw(st.fixed_dictionaries({"temperature": time_series(timestamps)}))


@st.composite
def features_by_name_for_each(draw, timestamps):
    names = draw(
        st.lists(
            st.text(), min_size=len(timestamps), max_size=len(timestamps), unique=True
        )
    )
    return {
        name: dict(
            zip(ts, draw(st.lists(st.floats(), min_size=len(ts), max_size=len(ts))))
        )
        for (name, ts) in zip(names, timestamps)
    }


@st.composite
def any_tutina_model_input(
    draw,
    history_timestamps=spaced_timestamps(),
    control_timestamps=spaced_timestamps(),
    forecast_timestamps=spaced_timestamps(),
):
    return {
        "history": draw(features_by_name(history_timestamps)),
        "control": draw(features_by_name(control_timestamps)),
        "forecasts": draw(forecast_features(forecast_timestamps)),
    }


@st.composite
def tutina_model_input(
    draw,
    first_prediction=st.datetimes(
        allow_imaginary=False, min_value=datetime(year=2000, month=1, day=1)
    ),
    n_predictions=st.integers(min_value=1, max_value=12),
    n_history=st.integers(min_value=1, max_value=12),
):
    first_prediction_val = draw(first_prediction)
    n_predictions_val = draw(n_predictions)
    n_history_val = draw(n_history)
    return draw(
        any_tutina_model_input(
            history_timestamps=spaced_timestamps(
                st.just(first_prediction_val - relativedelta(hours=n_history_val)),
                st.just(n_history_val),
            ),
            control_timestamps=spaced_timestamps(
                st.just(first_prediction_val), st.just(n_predictions_val)
            ),
            forecast_timestamps=spaced_timestamps(
                st.just(first_prediction_val - relativedelta(hours=1)),
                st.just(n_predictions_val + 1),
            ),
        )
    )


@given(time_series())
def test_valid_timeseries(feature_time_series):
    FeatureTimeSeries(root=feature_time_series)


@given(time_series(heterogenous_timestamps))
def test_timeseries_not_spaced_by_hour_should_fail(feature_time_series):
    with pytest.raises(pydantic.ValidationError):
        FeatureTimeSeries(root=feature_time_series)


@given(features_by_name())
def test_valid_features_by_name(features):
    FeaturesByName(root=features)


@given(
    st.lists(spaced_timestamps(), max_size=10)
    .filter(lambda timestamps: not mi.all_equal(timestamps))
    .flatmap(features_by_name_for_each)
)
def test_features_by_name_with_unequal_timestamps_should_fail(features):
    with pytest.raises(pydantic.ValidationError):
        FeaturesByName(root=features)


@given(tutina_model_input())
def test_valid_tutina_model_input(model_input):
    TutinaModelInput(**model_input)


@given(any_tutina_model_input())
def test_any_tutina_model_input(model_input):
    # It is almost impossible that hypothesis randomly finds a valid model input
    # without constraints
    with pytest.raises(pydantic.ValidationError):
        TutinaModelInput(**model_input)
