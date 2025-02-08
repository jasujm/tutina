import pydantic
import pytest
from dateutil.relativedelta import relativedelta
from hypothesis import given
from hypothesis import strategies as st

from tutina.lib.types import FeatureTimeSeries, _has_valid_spacing


@st.composite
def spaced_timestamps(draw):
    start = draw(st.datetimes(allow_imaginary=False)) - relativedelta(
        minute=0, second=0, microsecond=0
    )
    length = draw(st.integers(min_value=1, max_value=1000))
    return [start + relativedelta(hours=h) for h in range(length)]


@st.composite
def time_series(draw, timestamps=spaced_timestamps()):
    ts = draw(timestamps)
    features = draw(st.lists(st.floats(), min_size=len(ts), max_size=len(ts)))
    return dict(zip(ts, features))


@given(time_series())
def test_valid_timeseries(feature_time_series: FeatureTimeSeries):
    FeatureTimeSeries(root=feature_time_series)


@given(
    time_series(
        timestamps=st.sets(st.datetimes(), min_size=2, max_size=1000).filter(
            lambda ts: not _has_valid_spacing(ts)
        )
    )
)
def test_timeseries_not_spaced_by_hour_should_fail(
    feature_time_series: FeatureTimeSeries,
):
    with pytest.raises(pydantic.ValidationError):
        FeatureTimeSeries(root=feature_time_series)
