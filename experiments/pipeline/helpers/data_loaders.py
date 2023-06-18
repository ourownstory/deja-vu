import os
import random
from pathlib import Path

import pandas as pd
from tot.error_utils import raise_if


DATA_DIR = os.path.join(Path(__file__).parent.parent.parent.parent.absolute(), "datasets")


def load_EIA(n_samples=None, ids=None, n_ids=None):
    df = pd.read_csv(DATA_DIR + "/eia_electricity_hourly.csv")

    raise_if(
        ids is not None and n_ids is not None, "Remove specified ids from input if you want to select a number of ids."
    )
    if ids is None and n_ids is not None:
        unique_ids = df["ID"].unique()
        ids = random.sample(list(unique_ids), k=10)

    if ids is not None:
        df = df[df["ID"].isin(ids)].reset_index(drop=True)
    if n_samples is not None:
        df = df.groupby("ID").apply(lambda x: x.iloc[:n_samples, :].copy(deep=True)).reset_index(drop=True)
    return df


def load_London(n_samples=None, ids=None, n_ids=None):
    df = pd.read_csv(DATA_DIR + "/london_electricity_hourly.csv")

    raise_if(
        ids is not None and n_ids is not None, "Remove specified ids from input if you want to select a number of ids."
    )
    if ids is None and n_ids is not None:
        unique_ids = df["ID"].unique()
        ids = random.sample(list(unique_ids), k=10)

    if ids is not None:
        df = df[df["ID"].isin(ids)].reset_index(drop=True)
    if n_samples is not None:
        df = df.groupby("ID").apply(lambda x: x.iloc[:n_samples, :].copy(deep=True)).reset_index(drop=True)
    return df


def load_ERCOT(n_samples=None, ids=None, n_ids=None):
    df = pd.read_csv(DATA_DIR + "/ercot_load_reduced.csv")

    raise_if(
        ids is not None and n_ids is not None, "Remove specified ids from input if you want to select a number of ids."
    )
    if ids is None and n_ids is not None:
        unique_ids = df["ID"].unique()
        ids = random.sample(list(unique_ids), k=10)

    if ids is not None:
        df = df[df["ID"].isin(ids)].reset_index(drop=True)
    if n_samples is not None:
        df = df.groupby("ID").apply(lambda x: x.iloc[:n_samples, :].copy(deep=True)).reset_index(drop=True)
    return df


def load_Australian(n_samples=None, ids=None, n_ids=None):
    df = pd.read_csv(DATA_DIR + "/australian_electricity_half_hourly.csv")

    raise_if(
        ids is not None and n_ids is not None, "Remove specified ids from input if you want to select a number of ids."
    )
    if ids is None and n_ids is not None:
        unique_ids = df["ID"].unique()
        ids = random.sample(list(unique_ids), k=10)

    if ids is not None:
        df = df[df["ID"].isin(ids)].reset_index(drop=True)
    if n_samples is not None:
        df = df.groupby("ID").apply(lambda x: x.iloc[:n_samples, :].copy(deep=True)).reset_index(drop=True)
    return df


def load_Solar(n_samples=None, ids=None, n_ids=None):
    df = pd.read_csv(DATA_DIR + "/solar_10_minutes_dataset.csv")

    raise_if(
        ids is not None and n_ids is not None, "Remove specified ids from input if you want to select a number of ids."
    )
    if ids is None and n_ids is not None:
        unique_ids = df["ID"].unique()
        ids = random.sample(list(unique_ids), k=10)

    if ids is not None:
        df = df[df["ID"].isin(ids)].reset_index(drop=True)
    if n_samples is not None:
        df = df.groupby("ID").apply(lambda x: x.iloc[:n_samples, :].copy(deep=True)).reset_index(drop=True)
    return df


#  TODO: set proper freq
DATASETS = {
    "EIA": {"load": load_EIA, "freq": "H"},
    "London": {"load": load_London, "freq": "H"},
    "ERCOT": {"load": load_ERCOT, "freq": "H"},
    "Australian": {"load": load_Australian, "freq": "H"},
    "Solar": {"load": load_Solar, "freq": "H"},
}
