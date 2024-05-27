from typing import List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm import aliased
import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay
import datetime as dt
from models import Benchmark
from crud.forex import fetch_forex_data
from schemas.benchmark import BenchmarkMetric, BenchmarkCreate, BenchmarkUpdate, BenchmarkDelete


def fetch_benchmark_dataframe(db: Session, name=None, symbol=None, type=None, start_date=None, end_date=None, lookback=1, frequency='D', ccy_convert=False):
    query = db.query(Benchmark.date, Benchmark.close, Benchmark.currency)

    # instrument selection
    if name is not None:
        query = query.filter(Benchmark.name == name)
    if symbol is not None:
        query = query.filter(Benchmark.symbol == symbol)
    if type is not None:
        query = query.filter(Benchmark.type == type)

    # date filtering
    if start_date is not None:
        query = query.filter(Benchmark.date >= start_date.strftime('%Y-%m-%d'))
        if end_date is not None:
            query = query.filter(Benchmark.date <= end_date.strftime('%Y-%m-%d'))
    else:
        query = query.limit(1 + lookback)

    # ordering
    query = query.order_by(Benchmark.date)

    # get data
    data = query.all()

    # dataframe creation
    df = pd.DataFrame.from_records(data, index='date', columns=['date', 'value', 'currency'])

    # fill the gaps and fill forward and fill backward for cases when data is recorded way after INDEX_REFERENCE_DATE
    df = df.reindex(pd.date_range(start_date if start_date else df.index[0], end_date if end_date else df.index[-1], freq=frequency))
    df.fillna(method="pad", inplace=True)  # forward fill
    df.fillna(method="backfill", inplace=True) # backward fill

    # assume conversion to USD
    if ccy_convert:
        ccy = df.iloc[0]['currency']
        if ccy != 'USD':
            forex_df = fetch_forex_data(db, currency=ccy, start_date=start_date)
            forex_df = forex_df.reindex(pd.date_range(forex_df.index[0], df.index[-1], freq=frequency))
            forex_df.fillna(method="pad", inplace=True)  # forward fill before join; if issues with FX, fx rate will be stale instead of ignoring latest benchmark

            df = df.join(forex_df, how='left')
            df['value_usd'] = df['value'] / df['fx_rate']
            df.dropna(inplace=True)  # delete nan to play safe. nan could be introduced by join with forex
        else:
            df['value_usd'] = df['value']
    else:
        df['value_usd'] = df['value']

    return df


def fetch_latest_metrics(db: Session):

    # EUA
    current_date = dt.datetime.now()
    eua_df = fetch_benchmark_dataframe(db, current_date, name='EUA', type='spot', lookback=5, frequency='B')
    eua_df['ema5'] = pd.Series.ewm(eua_df['value'], span=5).mean()
    eua_df['ema10'] = pd.Series.ewm(eua_df['value'], span=5).mean()

    print(eua_df)

    metrics = []

    metrics.append(BenchmarkMetric(
        date=eua_df.index[-1],
        name='EUA_SPOT_EMA5',
        value=eua_df.iloc[-1]['ema5']
    ))

    metrics.append(BenchmarkMetric(
        date=eua_df.index[-1],
        name='EUA_SPOT_EMA10',
        value=eua_df.iloc[-1]['ema10']
    ))

    return metrics


def read_benchmarks(db: Session, date=dt.date, name=None, type=None):
    max_date_query = db.query(Benchmark.name, Benchmark.type, func.max(Benchmark.date).label('max_date')).filter(Benchmark.date <= date).group_by(Benchmark.name, Benchmark.type).subquery()
    main_query = db.query(Benchmark).filter(Benchmark.name == max_date_query.c.name).filter(Benchmark.type == max_date_query.c.type).filter(Benchmark.date == max_date_query.c.max_date)

    if name is not None:
        main_query = main_query.filter(Benchmark.name == name)

    if type is not None:
        main_query = main_query.filter(Benchmark.type == type)

    return main_query.all()


def read_latest_benchmarks(db: Session, name=None, type=None):
    # SELECT t1.name, t1.type, t2.date, t2.symbol, t2.close, t2.currency
    # FROM BENCHMARK AS `t2`, (SELECT NAME, TYPE, MAX(DATE) AS `MAX_DATE` FROM benchmark GROUP BY NAME, TYPE) AS `t1`
    # WHERE t1.name=t2.name AND t1.type=t2.type AND t2.date = t1.MAX_DATE
    # ORDER BY NAME, type

    # SELECT t1.NAME, t1.symbol, t1.TYPE, t1.DATE, t1.close FROM benchmark t1,
    # (SELECT NAME, symbol, TYPE, MAX(DATE) AS `max_date`
    # FROM benchmark
    # GROUP BY NAME, symbol, TYPE) t2
    # WHERE t1.name = t2.NAME AND
    # t1.symbol = t2.symbol AND
    # t1.TYPE = t2.TYPE AND
    # t1.date = t2.max_date
    # GROUP BY t1.NAME, t1.symbol, t1.TYPE

    # on subqueries
    # https://stackoverflow.com/questions/14123763/how-can-i-join-two-queries-on-the-same-table-with-python-sqlalchemy

    # query to get max date for each benchmark / type
    max_date_query = db.query(Benchmark.name, Benchmark.type, func.max(Benchmark.date).label('max_date')).group_by(Benchmark.name, Benchmark.type).subquery()

    # main query
    main_query = db.query(Benchmark).filter(Benchmark.name == max_date_query.c.name).filter(Benchmark.type == max_date_query.c.type).filter(Benchmark.date == max_date_query.c.max_date)

    if name is not None:
        main_query = main_query.filter(Benchmark.name == name)

    if type is not None:
        main_query = main_query.filter(Benchmark.type == type)

    return main_query.all()

    # return db.query(Benchmark).\
    # filter(Benchmark.name == max_date_query.c.name)\
    # .filter(Benchmark.type == max_date_query.c.type)\
    # .filter(Benchmark.date == max_date_query.c.max_date)\
    # .all()

    # max_date = db.query(func.max(Benchmark.date))
    # return db.query(Benchmark).filter_by(date=max_date).all()


def read(db: Session, start_date: dt.date, end_date: dt.date, name: str=None, type: str=None):
    query = db.query(Benchmark)
    if name:
        query = query.filter(Benchmark.name == name)
    if type:
        query = query.filter(Benchmark.type == type)
    
    return query.filter(Benchmark.date >= start_date).filter(Benchmark.date <= end_date).all()


def read_before(db: Session, date: dt.date) -> List[Benchmark]:
    latest = db.query(Benchmark.name, func.max(Benchmark.date).label("max_date")) \
                .filter(Benchmark.date <= date) \
                .group_by(Benchmark.name) \
                .subquery()
    return db.query(Benchmark) \
                .filter(Benchmark.name == latest.c.name) \
                .filter(Benchmark.date == latest.c.max_date) \
                .all()


def read_latest(db: Session, name: str, date: dt.date) -> Benchmark:
    return db.query(Benchmark.name, Benchmark.close, func.max(Benchmark.date).label("max_date")) \
             .filter(Benchmark.date <= date) \
             .filter(Benchmark.name == name) \
             .group_by(Benchmark.name) \
             .first()


def read_dataframe(db: Session, names: List[str], start_date: dt.date, end_date: dt.date):
    benchmarks = read(db, start_date, end_date)
    if not benchmarks:
        benchmarks = read_before(db, end_date)
    
    df = pd.DataFrame([{"date": benchmark.date, benchmark.name.lower(): benchmark.close} for benchmark in benchmarks]) \
           .groupby("date") \
           .mean()

    for name in names:
        if name not in df.columns:
            df[name] = np.nan

    df = df.append(df.reindex(pd.date_range(start_date, end_date, freq="D").date))
    df.sort_index(inplace=True)

    for name, value in df.iloc[0].items():
        if pd.isnull(value):
            df.iloc[0, df.columns.get_loc(name)] = read_latest(db, name, start_date).close

    df.fillna(method="pad", inplace=True)

    df = df[(~df.index.duplicated(keep="first")) & (df.index >= start_date) & (df.index <= end_date)]
    return df


def create(db: Session, benchmark: BenchmarkCreate):
    try:
        db_benchmark = Benchmark(**benchmark.dict())
        db.add(db_benchmark)
        db.commit()
        db.refresh(db_benchmark)
        return db_benchmark
    except SQLAlchemyError:
        return db.rollback()


def update(db: Session, benchmark: BenchmarkUpdate):
    try:
        db_benchmark: Benchmark = db.query(Benchmark).filter_by(
            date=benchmark.date,
            name=benchmark.name,
            type=benchmark.type,
            symbol=benchmark.symbol
        ).first()

        if db_benchmark is None:
            return None

        for key, value in benchmark.dict(exclude_unset=True).items():
            setattr(db_benchmark, key, value)
        db.commit()

        return db_benchmark
    except SQLAlchemyError as e:
        return db.rollback()


def delete(db: Session, benchmark: BenchmarkDelete):
    try:
        db_benchmark: Benchmark = db.query(Benchmark).filter_by(
            date=benchmark.date,
            name=benchmark.name,
            type=benchmark.type,
            symbol=benchmark.symbol
        ).first()

        if not db_benchmark:
            return
        
        db.delete(db_benchmark)
        db.commit()
        return True
    except SQLAlchemyError:
        return db.rollback()
