from typing import List
import json
import importlib
import datetime as dt

import numpy as np
import pandas as pd
import tensorflow as tf
from sqlalchemy.orm import Session

import crud
from database import DatabaseContextManager

models = pd.DataFrame()


class WeightsException(Exception):
    pass


class WeightLoadingException(WeightsException):
    pass


class WeightReadingException(WeightsException):
    pass


def _configs(db: Session) -> List[pd.DataFrame]:
    configs = crud.model_config.read(db)
    if not configs:
        raise WeightReadingException("No model_config data is available in the database")

    df = pd.DataFrame([{
            "date": config.date,
            "name": config.model_name,
            "version": config.model_version,
            "config": config.config
        } for config in configs]
    ).set_index("date")

    for name, version in set([(config.model_name, config.model_version) for config in configs]):
        new = df[(df["name"] == name) & (df["version"] == version)].copy()

        for date, row in new.iterrows():
            for key, value in row["config"].items():
                new.loc[date, key] = str(value) if type(value) == dict else value

        new.drop(['config'], axis='columns', inplace=True)  
        new.fillna(method="pad", inplace=True)
        yield new


def _model(row: pd.Series) -> tf.keras.Model:
    class_ = getattr(importlib.import_module("core.models"), row["class"])
    model = class_(
        inputs = json.loads(row["inputs"].replace("\'", "\"")),
        units = json.loads(row["structure"].replace("\'", "\"")),
        outputs = json.loads(row["outputs"].replace("\'", "\""))
    )
    model.load_weights(f"./core/data/{row['weights']}")
    return model


def load() -> list:
    global models
    if not models.empty:
        return
    
    with DatabaseContextManager() as db:
        for df in _configs(db):
            df["model"] = df.apply(lambda row: _model(row), axis=1)
            models = models.append(df)


def reload() -> list:
    global models
    models = pd.DataFrame()
    return load()


def get(db: Session, name: str, version: str, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    if models.empty:
        load()

    df = models[(models["name"] == name) & (models["version"] == version)].copy()
    if df.empty:
        raise WeightReadingException(f"No weights found in the database for model with name: {name} and version: {version}")

    # Read model_config data from database but use the cached model instance.
    # Note: Although we perform the weight reloading, for now this is necessary due to the app running across multiple k8s pods
    refreshed_df = next(df for df in _configs(db) if df.iloc[0]["name"] == name and df.iloc[0]["version"] == version)
    df = pd.concat([df["model"], refreshed_df], axis=1).sort_index().fillna(method="pad")

    first_date = df.index[0]
    last_date = df.index[-1]

    if end_date < first_date:
        df.rename(index={first_date: start_date}, inplace=True)
        return df[df.index == start_date]

    if start_date > last_date:
        df.rename(index={last_date: start_date}, inplace=True)
        return df[df.index == start_date]
    
    if start_date < first_date:
        df.rename(index={first_date: start_date}, inplace=True)
    
    if start_date not in df.index:
        df.loc[start_date, df.columns] = np.nan
        df.sort_index(inplace=True)
        df.fillna(method="pad", inplace=True)
    
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    return df
