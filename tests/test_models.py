#!/usr/bin/env python3
import logging
import os
import pathlib

import pandas as pd
import pytest
from darts.models import NaiveDrift, StatsForecastAutoARIMA, StatsForecastAutoETS

from tot.benchmark import SimpleBenchmark
from tot.datasets.dataset import Dataset
from tot.evaluation.metrics import ERROR_FUNCTIONS
from tot.models.models_darts import (
    DartsForecastingModel,
    DartsLocalForecastingModel,
    LinearRegressionModel,
    RandomForestModel,
)
from tot.models.models_naive import NaiveModel, SeasonalNaiveModel
from tot.models.models_neuralprophet import NeuralProphetModel, TorchProphetModel
from tot.models.models_prophet import ProphetModel

log = logging.getLogger("tot.test")
log.setLevel("WARNING")
log.parent.setLevel("WARNING")

DIR = pathlib.Path(__file__).parent.parent.absolute()
DATA_DIR = os.path.join(DIR, "datasets")
PEYTON_FILE = os.path.join(DATA_DIR, "wp_log_peyton_manning.csv")
AIR_FILE = os.path.join(DATA_DIR, "air_passengers.csv")
ERCOT_FILE = os.path.join(DATA_DIR, "ercot_load_reduced.csv")
SAVE_DIR = os.path.join(DIR, "tests", "test-logs")
if not os.path.isdir(SAVE_DIR):
    os.makedirs(SAVE_DIR)

NROWS = 128
EPOCHS = 2
BATCH_SIZE = 64
LR = 1.0
ERCOT_REGIONS = ["NORTH", "EAST", "FAR_WEST"]

PLOT = False


def test_simple_benchmark_prophet():
    log.info("test_simple_benchmark")
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
        Dataset(df=peyton_manning_df, name="peyton_manning", freq="D"),
    ]
    model_classes_and_params = [
        (ProphetModel, {}),
    ]

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,  # iterate over this list of tuples
        datasets=dataset_list,  # iterate over this list
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )

    results_train, results_test = benchmark.run()
    log.debug(results_test.to_string())
    log.info("#### Done with test_simple_benchmark_prophet")


def test_prophet_for_global_modeling():
    ercot_df_aux = pd.read_csv(ERCOT_FILE)
    ercot_df = pd.DataFrame()
    for region in ERCOT_REGIONS:
        ercot_df = pd.concat(
            (
                ercot_df,
                ercot_df_aux[ercot_df_aux["ID"] == region].iloc[:NROWS].copy(deep=True),
            ),
            ignore_index=True,
        )
    dataset_list = [
        Dataset(df=ercot_df, name="ercot_load", freq="H"),
    ]
    model_classes_and_params = [
        (ProphetModel, {}),
    ]

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,  # iterate over this list of tuples
        datasets=dataset_list,  # iterate over this list
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    log.info("#### Done with test_prophet_for_global_modeling")


# parameter input for test_seasonal_naive_model
dataset_input = [
    {
        "df": "peyton_manning_df",
        "name": "peyton_manning",
        "freq": "D",
        "seasonalities": [7, 365.25],
    },
    {
        "df": "peyton_manning_df",
        "name": "peyton_manning",
        "freq": "D",
        "seasonalities": "",
    },
    {
        "df": "peyton_manning_df_with_ID",
        "name": "peyton_manning",
        "freq": "D",
        "seasonalities": "",
    },
]
model_classes_and_params_input = [
    {"n_forecasts": 4},
    {"n_forecasts": 4, "season_length": 3},
]
decorator_input = [
    "dataset_input, model_classes_and_params_input",
    [
        (dataset_input[0], model_classes_and_params_input[0]),
        (dataset_input[1], model_classes_and_params_input[1]),
        (dataset_input[2], model_classes_and_params_input[1]),
    ],
]


@pytest.mark.parametrize(*decorator_input)
def test_seasonal_naive_model(dataset_input, model_classes_and_params_input):
    log.info("test_seasonal_naive_model")
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    peyton_manning_df_with_ID = peyton_manning_df.copy(deep=True)
    peyton_manning_df_with_ID["ID"] = "df1"
    df = {
        "peyton_manning_df": peyton_manning_df,
        "peyton_manning_df_with_ID": peyton_manning_df_with_ID,
    }
    dataset_list = [
        Dataset(
            df=df[dataset_input["df"]],
            name=dataset_input["name"],
            freq=dataset_input["freq"],
            seasonalities=dataset_input["seasonalities"],
        ),
    ]
    model_classes_and_params = [
        (SeasonalNaiveModel, model_classes_and_params_input),
    ]

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )

    results_train, results_test = benchmark.run()
    log.debug(results_test.to_string())


# parameter input for test_seasonal_naive_model_invalid_input
dataset_input = [
    {
        "df": "peyton_manning_df",
        "name": "peyton_manning",
        "freq": "D",
        "seasonalities": "",
    },
]
model_classes_and_params_input = [
    {"n_forecasts": 4},
    {"n_forecasts": 4, "season_length": 1},
]
decorator_input = [
    "dataset_input, model_classes_and_params_input",
    [
        (dataset_input[0], model_classes_and_params_input[0]),
        (dataset_input[0], model_classes_and_params_input[1]),
    ],
]


@pytest.mark.parametrize(*decorator_input)
def test_seasonal_naive_model_invalid_input(dataset_input, model_classes_and_params_input):
    log.info("Test invalid model input - Raise ValueError")
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(
            df=peyton_manning_df,
            name=dataset_input["name"],
            freq=dataset_input["freq"],
            seasonalities=dataset_input["seasonalities"],
        ),
    ]
    model_classes_and_params = [
        (SeasonalNaiveModel, model_classes_and_params_input),
    ]

    with pytest.raises(ValueError):
        benchmark = SimpleBenchmark(
            model_classes_and_params=model_classes_and_params,
            datasets=dataset_list,
            metrics=list(ERROR_FUNCTIONS.keys()),
            test_percentage=0.25,
            save_dir=SAVE_DIR,
            num_processes=1,
        )
        _, _ = benchmark.run()

    log.info("#### Done with test_seasonal_naive_model_invalid_input")


def test_naive_model():
    log.info("test_naive_model")
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(
            df=peyton_manning_df,
            name="peyton_manning",
            freq="D",
        ),
    ]
    model_classes_and_params = [
        (NaiveModel, {"n_forecasts": 4}),
    ]

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )

    results_train, results_test = benchmark.run()
    log.debug(results_test.to_string())


def test_linear_regression_model():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
        Dataset(df=peyton_manning_df, name="peyton_manning", freq="D"),
    ]
    model_classes_and_params = [
        (
            LinearRegressionModel,
            {"lags": 12, "output_chunk_length": 1, "n_forecasts": 4},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    results_train, results_test = benchmark.run()
    log.info("#### test_linear_regression_model")
    print(results_test)


def test_random_forest_model():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
        Dataset(df=peyton_manning_df, name="peyton_manning", freq="D"),
    ]
    model_classes_and_params = [
        (
            RandomForestModel,
            {"lags": 12, "output_chunk_length": 1, "n_forecasts": 4},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    results_train, results_test = benchmark.run()
    log.info("#### test_random_forest_model")
    print(results_test)


def test_darts_model():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
        Dataset(df=peyton_manning_df, name="peyton_manning", freq="D"),
    ]
    model_classes_and_params = [
        (
            DartsForecastingModel,
            {"model": NaiveDrift, "retrain": True, "lags": 12, "n_forecasts": 4},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    results_train, results_test = benchmark.run()
    log.info("#### test_darts_model")
    print(results_test)


# def test_darts_local_model():
#     air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
#     ercot_df_aux = pd.read_csv(ERCOT_FILE)
#     ercot_df = pd.DataFrame()
#     for region in ERCOT_REGIONS:
#         ercot_df = pd.concat(
#             (
#                 ercot_df,
#                 ercot_df_aux[ercot_df_aux["ID"] == region].iloc[:NROWS].copy(deep=True),
#             ),
#             ignore_index=True,
#         )
#
#     dataset_list = [
#         Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
#         Dataset(df=ercot_df, name="ercot_df", freq="H"),
#     ]
#     model_classes_and_params = [
#         (
#             DartsLocalForecastingModel,
#             {"model": StatsForecastAutoARIMA, "lags": 2, "n_forecasts": 1},
#         ),
#         (
#             DartsLocalForecastingModel,
#             {"model": StatsForecastAutoETS, "lags": 2, "n_forecasts": 1, "ETS_model": "ZZZ"},
#         ),
#     ]
#     log.debug("{}".format(model_classes_and_params))
#
#     benchmark = SimpleBenchmark(
#         model_classes_and_params=model_classes_and_params,
#         datasets=dataset_list,
#         metrics=list(ERROR_FUNCTIONS.keys()),
#         test_percentage=0.25,
#         save_dir=SAVE_DIR,
#         num_processes=1,
#     )
#     results_train, results_test = benchmark.run()
#     log.info("#### test_darts_local_model")
#     print(results_test)


def test_torch_prophet_model():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    peyton_manning_df = pd.read_csv(PEYTON_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
        Dataset(df=peyton_manning_df, name="peyton_manning", freq="D"),
    ]
    model_classes_and_params = [
        (
            TorchProphetModel,
            {"seasonality_mode": "multiplicative"},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    results_train, results_test = benchmark.run()
    log.info("#### test_torch_prophet_model")
    print(results_test)


def test_neuralprophet_model():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df, name="air_passengers", freq="MS"),
    ]
    model_classes_and_params = [
        (
            NeuralProphetModel,
            {"seasonality_mode": "multiplicative", "n_lags": 4, "n_forecasts": 3, "epochs": 1},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    results_train, results_test = benchmark.run()
    log.info("#### test_neuralprophet_model")
    print(results_test)


def test_check_min_input_len():
    air_passengers_df = pd.read_csv(AIR_FILE, nrows=NROWS)
    dataset_list = [
        Dataset(df=air_passengers_df[0:12], name="air_passengers", freq="MS"),
    ]
    model_classes_and_params = [
        (
            NeuralProphetModel,
            {"n_lags": 12, "n_forecasts": 6},
        ),
    ]
    log.debug("{}".format(model_classes_and_params))

    benchmark = SimpleBenchmark(
        model_classes_and_params=model_classes_and_params,
        datasets=dataset_list,
        metrics=list(ERROR_FUNCTIONS.keys()),
        test_percentage=0.25,
        save_dir=SAVE_DIR,
        num_processes=1,
    )
    with pytest.raises(ValueError):
        results_train, results_test = benchmark.run()
    log.info("#### test_check_min_input_len")
