import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Type

import pandas as pd

from tot.df_utils import _check_min_df_len, add_first_inputs_to_df, drop_first_inputs_from_df
from tot.models.models import Model
from tot.models.utils import _predict_darts_model, convert_df_to_TimeSeries

log = logging.getLogger("tot.model")

# check import of implemented models and consider order of imports
try:
    from sklearn.linear_model import LinearRegression

    _sklearn_installed = True
except ImportError:
    LinearRegression = None
    _sklearn_installed = False
    raise ImportError(
        "The LinearRegression model could not be imported."
        "Check for proper installation of sklearn: https://scikit-learn.org/stable/install.html"
    )

try:
    from darts.models import RegressionModel

    _darts_installed = True
except ImportError:
    RegressionModel = None
    _darts_installed = False
    raise ImportError(
        "The RegressionModel could not be imported."
        "Check for proper installation of darts: https://github.com/unit8co/darts/blob/master/INSTALL.md"
    )


@dataclass
class LinearRegressionModel(Model):
    """
    A forecasting model using a linear regression of the target series' lags to obtain a forecast.

    Examples
    --------
    >>> model_classes_and_params = [
    >>>     (
    >>>         LinearRegressionModel,
    >>>         {"lags": 12, "n_forecasts": 4},
    >>>     ),
    >>> ]
    >>>
    >>> benchmark = SimpleBenchmark(
    >>>     model_classes_and_params=model_classes_and_params,
    >>>     datasets=dataset_list,
    >>>     metrics=list(ERROR_FUNCTIONS.keys()),
    >>>     test_percentage=25,
    >>>     save_dir=SAVE_DIR,
    >>>     num_processes=1,
    >>> )
    """

    model_name: str = "LinearRegressionModel"
    model_class: Type = RegressionModel

    def __post_init__(self):
        # check if installed
        if not (_darts_installed or _sklearn_installed):
            raise RuntimeError(
                "Requires darts and sklearn to be installed:"
                "https://scikit-learn.org/stable/install.html"
                "https://github.com/unit8co/darts/blob/master/INSTALL.md"
            )

        model_params = deepcopy(self.params)
        model_params.pop("_data_params")
        # n_forecasts is not a parameter of the model
        model_params.pop("n_forecasts")
        # overwrite output_chunk_length with n_forecasts
        model_params.update({"output_chunk_length": self.params["n_forecasts"]})
        model = LinearRegression(n_jobs=-1)  # n_jobs=-1 indicates to use all processors
        model_params.update({"model": model})  # assign model
        self.model = self.model_class(**model_params)
        self.n_forecasts = self.params["n_forecasts"]
        self.n_lags = model_params["lags"]
        # input checks are provided by model itself

    def fit(self, df: pd.DataFrame, freq: str):
        """Fits the regression model.

        Parameters
        ----------
            df : pd.DataFrame
                dataframe containing column ``ds``, ``y``, and optionally ``ID`` with all data
            freq : str
                frequency of the input data
        """
        _check_min_df_len(df=df, min_len=self.n_forecasts + self.n_lags)
        self.freq = freq
        series = convert_df_to_TimeSeries(df, freq=self.freq)
        self.model = self.model.fit(series)

    def predict(self, df: pd.DataFrame, received_single_time_series, df_historic: pd.DataFrame = None):
        """Runs the model to make predictions.

        Expects all data to be present in dataframe.

        Parameters
        ----------
            df : pd.DataFrame
                dataframe containing column ``ds``, ``y``, and optionally ``ID`` with data
            df_historic : pd.DataFrame
                dataframe containing column ``ds``, ``y``, and optionally ``ID`` with historic data
            received_single_time_series : bool
                whether it is a single time series

        Returns
        -------
            pd.DataFrame
                columns ``ds``, ``y``, optionally [``ID``], and [``yhat<i>``] where yhat<i> refers to the
                i-step-ahead prediction for this row's datetime, e.g. yhat3 is the prediction for this datetime,
                predicted 3 steps ago, "3 steps old".
        """
        if df_historic is not None:
            df = self.maybe_extend_df(df_train=df_historic, df_test=df)
        _check_min_df_len(df=df, min_len=self.n_forecasts + self.n_lags)
        fcst = _predict_darts_model(
            df=df,
            model=self,
            past_observations_per_prediction=self.n_lags,
            future_observations_per_prediction=self.n_forecasts,
            retrain=False,
            received_single_time_series=received_single_time_series,
        )
        if df_historic is not None:
            fcst = self.maybe_drop_added_values_from_df(fcst, df)
        return fcst

    def maybe_extend_df(self, df_train, df_test):
        """
        If model depends on historic values, extend beginning of df_test with last
        df_train values.
        """
        df_test = add_first_inputs_to_df(samples=self.n_lags, df_train=df_train, df_test=df_test)

        return df_test

    def maybe_drop_added_values_from_df(self, predicted, df):
        """
        If model depends on historic values, drop first values of predicted and df_test.
        """
        predicted = drop_first_inputs_from_df(samples=self.n_lags, predicted=predicted, df=df)
        return predicted
