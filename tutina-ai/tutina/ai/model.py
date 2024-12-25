import contextlib
import functools
import itertools
from typing import TypedDict

import more_itertools as mi
import numpy as np
import pandas as pd
import sqlalchemy as sa
import tensorflow as tf
from sqlalchemy import func as saf

from tutina.lib.db import (
    HvacState,
    forecasts,
    get_engine,
    hvac_devices,
    hvacs,
    locations,
    measurements,
    opening_states,
    openings,
)
from tutina.lib.db import (
    metadata as db_metadata,
)

TIME_WINDOW_IN_SECONDS = 3600
MAX_FORECAST_IN_HOURS = 24
HISTORY_TIMESTEPS_IN_FEATURES = 12
CONTROL_TIMESTEPS_IN_FEATURES = 12
TRAIN_CHUNK_SIZE = 2048
VALIDATION_CHUNK_SIZE = 256
TEST_CHUNK_SIZE = 256
N_EPOCHS = 64

OUTDOOR = "outdoor"
TEMPERATURE_OUTDOOR = f"temperature_{OUTDOOR}"
MEASUREMENTS = "measurements"
TEMPERATURE = "temperature"
FORECASTS = "forecasts"
HVACS = "hvacs"
OPENINGS = "openings"
IS_OPEN = "is_open"
LABELS = "labels"
INPUTS = "inputs"
HISTORY = "history"
CONTROL = "control"


class TutinaInputFeatures(TypedDict):
    history: pd.DataFrame
    control: pd.DataFrame
    forecasts: pd.DataFrame


def _windowed_timestamp(column: sa.Column, window=TIME_WINDOW_IN_SECONDS):
    return saf.from_unixtime(
        saf.floor(saf.unix_timestamp(column) / window) * window
    ).label("timestamp")


def _prepend_column(column: str | tuple[str], name: str):
    if isinstance(column, str):
        return (name, column)
    else:
        return (name, *column)


def _prepend_column_level(df: pd.DataFrame, name: str):
    df.columns = pd.MultiIndex.from_tuples(
        _prepend_column(column, name) for column in df.columns
    )
    return df


def _fill_forecasts(df: pd.DataFrame, index: pd.Index):
    columns = [column for column in df.columns if column[0] == FORECASTS]
    index_it = iter(index)
    range_first = next(index_it)
    for first, last in mi.pairwise(index_it):
        if last - first > pd.Timedelta("1h"):
            range_last = last - pd.Timedelta("1s")  # this is to make exclusive bound
            df.loc[range_first:range_last, columns] = df.loc[
                range_first:range_last, columns
            ].ffill()
            range_first = last
    df.loc[range_first:, columns] = df.loc[range_first:, columns].ffill()


def _tensorize_with_batch(data):
    return tf.expand_dims(tf.constant(data), axis=0)


def load_measurements_data(connection: sa.Connection):
    time_column = _windowed_timestamp(measurements.c.timestamp)
    expression = (
        sa.select(
            time_column,
            locations.c.slug.label("location"),
            saf.avg(measurements.c.temperature).label(TEMPERATURE),
            saf.avg(measurements.c.humidity).label("humidity"),
            saf.avg(measurements.c.pressure).label("pressure"),
        )
        .select_from(measurements.join(locations))
        .group_by(
            time_column,
            measurements.c.location_id,
        )
    )
    data = pd.read_sql(expression, connection)
    return data.pivot(
        index="timestamp",
        columns="location",
        values=[TEMPERATURE, "humidity", "pressure"],
    )


def load_hvacs_data(connection: sa.Connection):
    time_column = _windowed_timestamp(hvacs.c.timestamp)
    expression = (
        sa.select(
            time_column,
            hvac_devices.c.slug.label("device"),
            hvacs.c.temperature,
            *(saf.avg(hvacs.c.state == state).label(state.name) for state in HvacState),
        )
        .select_from(hvacs.join(hvac_devices))
        .group_by(time_column, hvacs.c.device_id)
    )
    data = pd.read_sql(expression, connection)
    return data.pivot(
        index="timestamp",
        columns="device",
    )


def load_openings_data(connection: sa.Connection):
    time_column = _windowed_timestamp(opening_states.c.timestamp)
    expression = (
        sa.select(
            time_column,
            saf.concat(openings.c.slug, "_", openings.c.type).label("opening"),
            saf.avg(opening_states.c.is_open).label("is_open"),
        )
        .select_from(opening_states.join(openings))
        .group_by(time_column, opening_states.c.opening_id)
    )
    data = pd.read_sql(expression, connection)
    return data.pivot(
        index="timestamp",
        columns="opening",
    )


def load_forecasts_data(connection: sa.Connection):
    time_column = _windowed_timestamp(forecasts.c.timestamp, 3600)
    in_hours_column = saf.hour(
        saf.timediff(forecasts.c.reference_timestamp, time_column)
    ).label("in_hours")
    expression = (
        sa.select(
            time_column,
            in_hours_column,
            saf.avg(forecasts.c.temperature).label(TEMPERATURE),
            saf.avg(forecasts.c.humidity).label("humidity"),
            saf.avg(forecasts.c.pressure).label("pressure"),
            saf.avg(forecasts.c.wind_speed).label("wind_speed"),
        )
        .where(in_hours_column < MAX_FORECAST_IN_HOURS)
        .group_by(time_column, in_hours_column)
    )
    data = pd.read_sql(expression, connection)
    return data.pivot(
        index="timestamp",
        columns="in_hours",
    )


def load_data(connection: sa.Connection):
    measurements = _prepend_column_level(
        load_measurements_data(connection), MEASUREMENTS
    )
    hvacs = _prepend_column_level(load_hvacs_data(connection), HVACS)
    openings = _prepend_column_level(load_openings_data(connection), "openings")
    forecasts = _prepend_column_level(load_forecasts_data(connection), FORECASTS)

    df = functools.reduce(pd.DataFrame.join, [measurements, hvacs, openings, forecasts])
    _fill_forecasts(df, forecasts.index)
    return df


def load_data_with_cache(filename: str | None, database_url: str):
    if filename:
        with contextlib.suppress(OSError):
            return pd.read_parquet(filename)

    engine = get_engine(database_url)
    db_metadata.create_all(engine)
    with engine.begin() as connection:
        data = load_data(connection)

    if filename:
        data.to_parquet(filename)

    return data


def clean_data(data: pd.DataFrame, config=None):
    range_start = pd.Timestamp(ts) if (ts := config.get("timestamp_start")) else None
    range_end = pd.Timestamp(ts) if (ts := config.get("timestamp_end")) else None
    slice_range = slice(range_start, range_end)
    return data.loc[slice_range, :].ffill()


def get_temperatures(data: pd.DataFrame, rooms: list[str] | None):
    temperatures = data[MEASUREMENTS, TEMPERATURE]
    if rooms:
        if OUTDOOR in rooms:
            included_temperatures = rooms
        else:
            included_temperatures = [*rooms, OUTDOOR]
        temperatures = temperatures[included_temperatures]
    return temperatures.rename(lambda col: f"temperature_{col}", axis="columns")


def get_forecast_features(data: pd.DataFrame):
    return data[FORECASTS, TEMPERATURE].rename(
        lambda col: f"temperature_{col:0>2}", axis="columns"
    )


def get_hvac_features(data: pd.DataFrame, devices: list[str] | None):
    hvacs_data = data[HVACS]
    hvac_temperatures = hvacs_data[TEMPERATURE]
    hvac_states = hvacs_data[["heat", "cool"]]
    if devices:
        hvac_temperatures = hvac_temperatures[devices]
        hvac_states = hvac_states.loc[:, (slice(None), devices)]
    hvac_temperatures = hvac_temperatures.mul(
        hvac_states.gt(0).astype(int), level=1, axis=0
    )
    hvac_temperatures.columns = [
        f"hvac_temperature_{state}_{device}"
        for (state, device) in hvac_temperatures.columns
    ]
    hvac_states.columns = [
        f"hvac_state_{state}_{device}" for (state, device) in hvac_states.columns
    ]
    hvac_features = pd.concat([hvac_temperatures, hvac_states], axis="columns")
    return hvac_features.loc[:, hvac_features.ne(0).any()]


def get_opening_features(data: pd.DataFrame, openings: list[str] | None):
    openings_data = data[OPENINGS, IS_OPEN]
    if openings:
        openings_data = openings_data[openings]
    return openings_data.rename(lambda col: f"is_open_{col}", axis="columns")


def get_features(data: pd.DataFrame, config=None):
    if not config:
        config = {}
    temperatures = get_temperatures(data, config.get("rooms"))
    hvacs = get_hvac_features(data, config.get("hvac_devices"))
    openings = get_opening_features(data, config.get("openings"))
    labels = _prepend_column_level(temperatures, LABELS)
    controls = _prepend_column_level(
        pd.concat([hvacs, openings], axis="columns"), CONTROL
    )
    forecasts = _prepend_column_level(get_forecast_features(data), FORECASTS)
    features = pd.concat([controls, forecasts, labels], axis="columns")
    return features


def _features_to_model_input(
    features, *, labels_slice: slice, control_slice: slice, forecasts_slice: slice
):
    n_labels = labels_slice.stop - labels_slice.start
    n_controls = control_slice.stop - control_slice.start
    n_forecasts = forecasts_slice.stop - forecasts_slice.start
    history_inputs = features[:, :HISTORY_TIMESTEPS_IN_FEATURES, labels_slice]
    history_inputs.set_shape([None, HISTORY_TIMESTEPS_IN_FEATURES, n_labels])
    control_inputs = features[:, HISTORY_TIMESTEPS_IN_FEATURES:, control_slice]
    control_inputs.set_shape([None, CONTROL_TIMESTEPS_IN_FEATURES, n_controls])
    forecast_inputs = tf.expand_dims(
        features[:, HISTORY_TIMESTEPS_IN_FEATURES, forecasts_slice], axis=2
    )
    forecast_inputs.set_shape([None, n_forecasts, 1])
    labels = features[:, HISTORY_TIMESTEPS_IN_FEATURES:, labels_slice]
    labels.set_shape([None, CONTROL_TIMESTEPS_IN_FEATURES, n_labels])
    return {
        HISTORY: history_inputs,
        CONTROL: control_inputs,
        FORECASTS: forecast_inputs,
    }, labels


def features_to_dataset(features: pd.DataFrame):
    labels_slice = features.columns.get_loc((LABELS,))
    control_slice = features.columns.get_loc((CONTROL,))
    forecasts_slice = features.columns.get_loc((FORECASTS,))
    return tf.keras.utils.timeseries_dataset_from_array(
        features, None, HISTORY_TIMESTEPS_IN_FEATURES + CONTROL_TIMESTEPS_IN_FEATURES
    ).map(
        functools.partial(
            _features_to_model_input,
            labels_slice=labels_slice,
            control_slice=control_slice,
            forecasts_slice=forecasts_slice,
        )
    )


def features_to_model_input(
    features: pd.DataFrame, last_history_ts: pd.Timestamp
) -> TutinaInputFeatures:
    features = features.sort_index(axis="columns")
    history_input = features.loc[:last_history_ts, LABELS]
    control_input = features.loc[last_history_ts:, CONTROL].drop(
        last_history_ts, errors="ignore"
    )
    forecast_input = features.loc[last_history_ts, FORECASTS].to_frame()
    forecast_input.index = pd.date_range(
        last_history_ts, periods=len(forecast_input.index), freq="h"
    )
    forecast_input.columns = [TEMPERATURE]
    return TutinaInputFeatures(
        history=history_input,
        control=control_input,
        forecasts=forecast_input,
    )


def split_data_to_train_and_validation(features: pd.DataFrame):
    features = features.sort_index(axis="columns")
    datasets = [None, None, None]
    chunk_sizes = [TRAIN_CHUNK_SIZE, VALIDATION_CHUNK_SIZE, TEST_CHUNK_SIZE]
    for i, chunk_size in itertools.cycle(list(enumerate(chunk_sizes))):
        next_features = features.iloc[:chunk_size, :]
        if next_features.empty:
            break
        features.drop(next_features.index, inplace=True)
        next_dataset = features_to_dataset(next_features)
        datasets[i] = (
            dataset.concatenate(next_dataset)
            if (dataset := datasets[i]) is not None
            else next_dataset
        )
    return datasets


class TutinaModel(tf.keras.Model):
    def __init__(self, n_labels: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_labels = n_labels
        # history part
        self.history_normalization_layer = tf.keras.layers.Normalization(
            name="history_normalization"
        )
        self.lstm_cell = tf.keras.layers.LSTMCell(32, name="history_ltsm_cell")
        self.rnn = tf.keras.layers.RNN(
            self.lstm_cell, return_state=True, name="history_ltsm"
        )
        # control part
        self.control_normalization_layer = tf.keras.layers.Normalization(
            name="control_normalization"
        )
        # forecasts part
        self.forecasts_normalization_layer = tf.keras.layers.Normalization(
            axis=None, name="forecasts_normalization"
        )
        self.forecasts_layer = tf.keras.Sequential(
            [
                self.forecasts_normalization_layer,
                tf.keras.layers.Conv1D(4, 2),
            ],
            name="forecasts_layer",
        )
        # output
        self.mlp = tf.keras.Sequential(
            [
                tf.keras.layers.Concatenate(),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(
                    n_labels, kernel_initializer=tf.initializers.zeros()
                ),
            ],
            name="mlp",
        )

    def get_config(self):
        return {
            **super().get_config(),
            "n_labels": self.n_labels,
        }

    def adapt(self, training_data: tf.data.Dataset):
        self.history_normalization_layer.adapt(
            training_data.map(lambda inputs, _: inputs[HISTORY])
        )
        self.control_normalization_layer.adapt(
            training_data.map(lambda inputs, _: inputs[CONTROL])
        )
        self.forecasts_normalization_layer.adapt(
            training_data.map(lambda inputs, _: inputs[FORECASTS])
        )

    def call(self, inputs, training=None):
        history_inputs = inputs[HISTORY]
        latest = history_inputs[:, -1, :]
        control_inputs = self.control_normalization_layer(inputs[CONTROL])
        forecasts_input = self.forecasts_layer(inputs[FORECASTS])
        n_output_steps = control_inputs.shape[1]
        predictions = tf.TensorArray(tf.float32, size=n_output_steps)
        x1 = self.history_normalization_layer(history_inputs)
        x1, *states = self.rnn(x1, training=training)
        x2 = control_inputs[:, 0, :]
        x3 = forecasts_input[:, 0, :]
        x = self.mlp([x1, x2, x3], training=training)
        latest = tf.keras.ops.add(latest, x)
        predictions = predictions.write(0, latest)
        for i, control_input in enumerate(tf.unstack(control_inputs, axis=1)):
            x = self.history_normalization_layer(latest)
            x = tf.squeeze(x, axis=0)
            x1, states = self.lstm_cell(x, states=states, training=training)
            x2 = control_input
            x3 = forecasts_input[:, i, :]
            x = self.mlp([x1, x2, x3], training=training)
            latest = tf.keras.ops.add(latest, x)
            predictions = predictions.write(i, latest)
        predictions = predictions.stack()
        predictions = tf.transpose(predictions, [1, 0, 2])
        return predictions


def load_model(model_file: str):
    return tf.keras.models.load_model(model_file)


def create_and_train_model(
    train_dataset: tf.data.Dataset, validation_dataset: tf.data.Dataset
):
    n_labels = train_dataset.element_spec[1].shape[-1]
    model = TutinaModel(n_labels)
    model.adapt(train_dataset)
    model.compile(
        loss=tf.keras.losses.MeanSquaredError(),
        optimizer=tf.keras.optimizers.Adam(),
        metrics=[tf.keras.metrics.MeanAbsoluteError()],
    )
    history = model.fit(
        train_dataset, validation_data=validation_dataset, epochs=N_EPOCHS
    )
    return model, history


def predict_single(model: TutinaModel, model_input: TutinaInputFeatures):
    tensorized_input = dict(
        (k, _tensorize_with_batch(v)) for (k, v) in model_input.items()
    )
    prediction = tf.squeeze(model(tensorized_input, training=False), axis=0)
    return pd.DataFrame(
        prediction,
        columns=model_input[HISTORY].columns,
        index=model_input[CONTROL].index,
    )


def plot_comparison(sample: pd.DataFrame, prediction: pd.DataFrame):
    import seaborn as sns
    from matplotlib import pyplot as plt

    comparison_data = pd.concat(
        [sample[LABELS], prediction], keys=["actual", "predicted"], axis="columns"
    )
    comparison_data.columns.names = ["type", "room"]
    comparison_data = comparison_data.melt(
        value_name="temperature", ignore_index=False
    ).reset_index(names="timestamp")
    sns.relplot(
        comparison_data,
        x="timestamp",
        y="temperature",
        col="room",
        col_wrap=4,
        hue="type",
    )
    plt.show()


def plot_prediction(history: pd.DataFrame, prediction: pd.DataFrame):
    import matplotlib.colors as mcolors
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    prediction = pd.concat([history.iloc[-1:], prediction])
    history_mean = history.drop(columns=TEMPERATURE_OUTDOOR, errors="ignore").mean(
        axis="columns"
    )
    prediction_mean = prediction.drop(
        columns=TEMPERATURE_OUTDOOR, errors="ignore"
    ).mean(axis="columns")
    locator = mdates.HourLocator(byhour=np.arange(0, 24, 4))
    formatter = mdates.ConciseDateFormatter(locator)
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    lines = []
    lines.append(
        ax.plot(
            history_mean.index,
            history_mean,
            label="Measured",
            linestyle="solid",
            color="black",
            linewidth=3,
        )[0]
    )
    lines.append(
        ax.plot(
            prediction_mean.index,
            prediction_mean,
            linestyle="dashed",
            color="black",
            label="Predicted",
            linewidth=3,
        )[0]
    )
    colors = mcolors.TABLEAU_COLORS.values()
    for column, color in zip(history.columns, colors):
        lines.append(
            ax.plot(
                history.index,
                history[column],
                label=column,
                linestyle="solid",
                color=color,
                alpha=0.5,
            )[0]
        )
        ax.plot(
            prediction.index,
            prediction[column],
            linestyle="dashed",
            color=color,
            alpha=0.5,
        )
    ax.set(ylabel="Temperature (℃)", title="Room temperature prediction")
    ax.legend(handles=lines)
    ax.grid()
    ax.autoscale(axis="x", tight=True)
    return fig, ax
