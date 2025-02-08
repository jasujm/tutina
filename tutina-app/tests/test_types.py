import more_itertools as mi
import pydantic
import pytest
from dateutil.relativedelta import relativedelta
from hypothesis import given
from hypothesis import strategies as st

from tutina.lib.types import FeatureTimeSeries, _has_valid_spacing, FeaturesByName

heterogenous_timestamps = st.lists(
    st.datetimes(), min_size=2, max_size=10, unique=True
).filter(lambda ts: not _has_valid_spacing(ts))


@st.composite
def spaced_timestamps(draw):
    start = draw(st.datetimes(allow_imaginary=False)) - relativedelta(
        minute=0, second=0, microsecond=0
    )
    length = draw(st.integers(min_value=1, max_value=10))
    return [start + relativedelta(hours=h) for h in range(length)]


@st.composite
def time_series(draw, timestamps=spaced_timestamps()):
    ts = draw(timestamps)
    features = draw(st.lists(st.floats(), min_size=len(ts), max_size=len(ts)))
    return dict(zip(ts, features))


@st.composite
def features_by_name(draw, timestamps=spaced_timestamps()):
    ts = draw(timestamps)
    return draw(st.dictionaries(keys=st.text(), values=time_series(st.just(ts))))


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
