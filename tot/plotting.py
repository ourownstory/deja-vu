import logging

from tot.plot_utils import (
    _plot_plotly,
    select_plotting_backend,
    validate_df_name_input,
    validate_highlight_forecast_input,
    validate_plotting_backend_input,
)

log = logging.getLogger("tot.plot")


def plot_plotly(
    fcst,
    df_name=None,
    xlabel="ds",
    ylabel="y",
    highlight_forecast=None,
    figsize=(700, 350),
    plotting_backend=None,
):
    """
    Plot the NeuralProphet forecast

    Parameters
    ---------
        fcst : pd.DataFrame
            Output of m.predict
        df_name : str
            optoinal, ID from time series that should be plotted
        xlabel : str
            optional, Label name on X-axis
        ylabel : str
            optional, Label name on Y-axis
        highlight_forecast : Union[int, None]
            optional, i-th step ahead forecast to highlight.
        figsize : tuple[int, int]
            optional, Width, height in inches.
        plotting_backend : str
            optional, overwrites the default plotting backend.

            Options
            * ``plotly-resampler``: Use the plotly backend for plotting in resample mode. This mode uses the
                plotly-resampler package to accelerate visualizing large data by resampling it. For some
                environments (colab, pycharm interpreter) plotly-resampler might not properly visualize the figures.
                In this case, consider switching to 'plotly-auto'.
            * ``plotly``: Use the plotly package for plotting
            * (default) None: Use plotly with resampling for jupyterlab notebooks and vscode notebooks.
                Automatically switch to plotly without resampling for all other environments.

    Returns
    -------
        Plotly figure
    """
    # input check
    fcst = validate_df_name_input(df_name, fcst)
    validate_highlight_forecast_input(highlight_forecast, fcst)
    validate_plotting_backend_input(plotting_backend)
    # Select internal plotting backend
    plotting_backend = select_plotting_backend(plotting_backend)
    return _plot_plotly(
        fcst=fcst,
        quantiles=[0.5],  # set default to median quantile
        xlabel=xlabel,
        ylabel=ylabel,
        highlight_forecast=highlight_forecast,
        figsize=figsize,
        resampler_active=plotting_backend == "plotly-resampler",
    )
