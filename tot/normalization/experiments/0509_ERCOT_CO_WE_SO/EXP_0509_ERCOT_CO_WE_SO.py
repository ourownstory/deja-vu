import os
import pathlib

import pandas as pd
from neuralprophet import set_log_level
from plotly_resampler import unregister_plotly_resampler
from sklearn.preprocessing import MinMaxScaler, StandardScaler, MaxAbsScaler

from tot.models.models_neuralprophet import NeuralProphetModel
from tot.normalization.experiments.pipeline import (
    concat_and_save_results,
    plot_and_save_multiple_dfs_multiple_ids,
    run_pipeline,
)

unregister_plotly_resampler()


set_log_level("INFO")
DIR = pathlib.Path(__file__).parent.parent.absolute()
EXP_NAME = "0509_ERCOT_CO_WE_SO"
EXP_DIR = os.path.join(DIR, f"{EXP_NAME}")
PLOTS_DIR = os.path.join(EXP_DIR, f"plots_NeuralProphetModel")
PLOT = False

SERIES_LENGTH = 24 * 7 * 15
# DATE_RNG = date_rng = pd.date_range(start=pd.to_datetime("2011-01-01 01:00:00"), periods=SERIES_LENGTH, freq="H")
MODEL_CLASS = NeuralProphetModel
PARAMS = {
    "n_forecasts": 1,
    "n_lags": 24,
    "n_changepoints": 0,
    "growth": "off",
    "global_normalization": True,
    "normalize": "off",
    # Disable seasonality components, except yearly
    # "yearly_seasonality": False,
    # "weekly_seasonality": False,
    # "daily_seasonality": True,
    "epochs": 20,
    "_data_params": {},
}
data_location = "https://raw.githubusercontent.com/ourownstory/neuralprophet-data/main/datasets/"
df_ercot = pd.read_csv(data_location + "multivariate/ercot-panel.csv")
df_ercot = df_ercot.sort_values(['ID', 'ds']).groupby('ID').apply(lambda x: x[0:SERIES_LENGTH]).reset_index(drop=True)
df_ercot = df_ercot[df_ercot['ID'].isin(['COAST', 'WEST', 'SOUTHERN'])]
min_date = df_ercot[df_ercot['ID']=='COAST'].loc[:, 'ds'].min()
max_date = df_ercot[df_ercot['ID']=='COAST'].loc[:, 'ds'].max()
DATE_RNG = pd.date_range(start=min_date, end=max_date, freq="H")

fcsts_train, fcsts_test, metrics_test, elapsed_time = run_pipeline(
    df=df_ercot,
    model_class=MODEL_CLASS,
    params=PARAMS,
    freq="H",
    test_percentage=0.4,
    metrics=["MAPE", "MAE", "RMSE", "MASE"],
    scale_levels=[None, "local", "global"],
    scalers=[MinMaxScaler(feature_range=(0, 0.5)), StandardScaler(), MaxAbsScaler()],
)
plot_and_save_multiple_dfs_multiple_ids(
    fcst_dfs=fcsts_test,
    date_rng=DATE_RNG,
    ids=['COAST', 'WEST', 'SOUTHERN'],
    PLOT=PLOT,
    PLOTS_DIR=PLOTS_DIR,
    EXP_NAME=EXP_NAME,
)
concat_and_save_results(
    metric_dfs=metrics_test,
    elapsed_time=elapsed_time,
    EXP_DIR=EXP_DIR,
    EXP_NAME=EXP_NAME,
)
