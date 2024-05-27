import datetime as dt
from typing import List, Optional, Union
from fastapi.exceptions import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
import pandas as pd
from models import BenchmarkIndex


class BenchmarkIndexException(Exception):
    pass


def read(db: Session, start_date: dt.date, end_date: dt.date):
    return db.query(BenchmarkIndex).filter(BenchmarkIndex.date >= start_date).filter(BenchmarkIndex.date <= end_date).all()


def read_before(db: Session, date: dt.date, benchmark: Optional[str]=None):
    if benchmark:
        return db.query(BenchmarkIndex) \
                .filter(BenchmarkIndex.benchmark == benchmark) \
                .filter(BenchmarkIndex.date <= date) \
                .order_by(BenchmarkIndex.date.desc()) \
                .first()

    latest = db.query(BenchmarkIndex.benchmark, func.max(BenchmarkIndex.date).label("max_date")) \
                .filter(BenchmarkIndex.date <= date) \
                .group_by(BenchmarkIndex.benchmark) \
                .subquery()
    return db.query(BenchmarkIndex) \
                .filter(BenchmarkIndex.benchmark == latest.c.benchmark) \
                .filter(BenchmarkIndex.date == latest.c.max_date) \
                .all()


def read_first(db: Session, benchmark: str=None):
    query = db.query(BenchmarkIndex.benchmark, BenchmarkIndex.value, func.min(BenchmarkIndex.date).label("date")) \
              .group_by(BenchmarkIndex.benchmark)
    if benchmark:
        return query.filter(BenchmarkIndex.benchmark == benchmark).first()
    return query.all()


def read_benchmark_names(db: Session) -> List[str]:
    return [name_tuple[0] for name_tuple in db.query(BenchmarkIndex.benchmark).distinct().all()]


def min_date(db: Session) -> dt.date:
    min_dates_query = db.query(func.min(BenchmarkIndex.date)) \
                        .group_by(BenchmarkIndex.benchmark) \
                        .subquery()
    return db.query(func.max(BenchmarkIndex.date).label("max_date")) \
              .filter(BenchmarkIndex.date.in_(min_dates_query)) \
              .first()[0]


def _create_df(indexes: list, start_date: dt.date, end_date: dt.date):
    df = pd.DataFrame([{"date": index.date, index.benchmark: index.value} for index in indexes]) \
                .groupby("date") \
                .mean()
    df = df.append(df.reindex(pd.date_range(start_date, end_date, freq="D").date))
    df.sort_index(inplace=True)
    df.fillna(method="pad", inplace=True)
    df.fillna(method="backfill", inplace=True)
    df = df[(~df.index.duplicated(keep="first")) & (df.index >= start_date) & (df.index <= end_date)]
    return df


def _read_date(db: Session, first_date: bool=True):
    if first_date:
        result = db.query(func.min(BenchmarkIndex.date)).first()
        if not result:
            return None
        return result[0]
    else:
        result = db.query(func.max(BenchmarkIndex.date)).first()
        if not result:
            return None
        return result[0]


def read_dataframe(db: Session, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    first_date = _read_date(db, True)
    last_date = _read_date(db, False)

    if not first_date or not last_date:
        raise BenchmarkIndexException("There is no data in benchmark_index table")

    if end_date < first_date:
        return _create_df(read_first(db), start_date, end_date)

    if start_date > last_date:
        return _create_df(read_before(db, start_date), start_date, end_date)


    indexes = read(db, start_date, end_date) or read_before(db, start_date)
    if not indexes:
        raise BenchmarkIndexException("There is no data in benchmark_index table between {start_date} and {end_date}")

    df = _create_df(indexes, start_date, end_date)

    for benchmark in read_benchmark_names(db):
        if benchmark not in df.columns:
            if start_date <= first_date and end_date <= last_date:
                df[benchmark] = read_first(db, benchmark).value
            elif start_date >= first_date and end_date >= last_date:
                df[benchmark] = read_before(db, last_date, benchmark).value
            else:
                df[benchmark] = read_before(db, last_date, benchmark).value or \
                                read_first(db, benchmark).value
    return df


def create(db: Session, index: BenchmarkIndex):
    try:
        db_index = BenchmarkIndex(**index.dict())
        db.add(db_index)
        db.commit()
        db.refresh(db_index)
        return db_index
    except SQLAlchemyError as e:
        db.rollback()
        raise e
