import datetime as dt
from typing import List

import pandas as pd
from fastapi import Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models import StandardizedInstrument
from schemas.standardized_instrument import StandardizedInstrumentCreate, StandardizedInstrumentBase


class StandardizedInstrumentException(Exception):
    pass


def read(instrument_base: StandardizedInstrumentBase, db: Session) -> StandardizedInstrument:
    return db.query(StandardizedInstrument).filter_by(instrument=instrument_base.instrument)\
        .filter_by(source=instrument_base.source).filter_by(date=instrument_base.date)\
        .filter_by(type=instrument_base.type).first()


def read_instruments_by_period(start_date: dt.date, end_date: dt.date, db: Session) -> List[StandardizedInstrument]:
    query: Query = db.query(StandardizedInstrument)
    if start_date is not None:
        query = query.filter(StandardizedInstrument.date >= start_date)
    if end_date is not None:
        query = query.filter(StandardizedInstrument.date <= end_date)
    return query.all()


def read_latest_bid_ask(db: Session):
    db_bid_and_dates = db.query(StandardizedInstrument.price, StandardizedInstrument.date).filter_by(instrument="CET")\
        .filter_by(source="ACX").filter_by(type="BID").order_by(desc(StandardizedInstrument.date)).all()

    for db_bid_and_date in db_bid_and_dates:
        bid = db_bid_and_date[0]
        if bid is None:
            continue
        ask = db.query(StandardizedInstrument.price).filter_by(instrument="CET").filter_by(source="ACX").\
            filter_by(date=db_bid_and_date[1]).filter_by(type="ASK").first()

        if ask is not None and ask[0] is not None:
            return bid, ask[0], db_bid_and_date[1]

    return None, None, None


def _read_date(db: Session, first_date: bool=True):
    if first_date:
        result = db.query(func.min(StandardizedInstrument.date)).first()
        if not result:
            return None
        return result[0]
    else:
        result = db.query(func.max(StandardizedInstrument.date)).first()
        if not result:
            return None
        return result[0]


def _create_df(instruments: list, start_date, end_date):
    df = pd.DataFrame([{"date": instrument.date, instrument.type: float(instrument.price)} for instrument in instruments]) \
            .groupby("date") \
            .mean()
    df["corsia_date"] = df.index
    df = df.append(df.reindex(pd.date_range(start_date, end_date, freq="D").date))
    df.sort_index(inplace=True)
    df.fillna(method="pad", inplace=True)
    df.fillna(method="backfill", inplace=True)
    df = df[(~df.index.duplicated(keep="first")) & (df.index >= start_date) & (df.index <= end_date)]
    return df


def read_dataframe(db: Session, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    first_date = _read_date(db, True)
    last_date = _read_date(db, False)

    if not first_date or not last_date:
        raise StandardizedInstrumentException("There is no data in standardized_instrument table")

    if end_date < first_date:
        return _create_df(read_instruments_by_period(first_date, first_date, db), start_date, end_date)

    if start_date > last_date:
        return _create_df(read_instruments_by_period(last_date, last_date, db), start_date, end_date)

    instruments = read_instruments_by_period(start_date, end_date, db)
    if not instruments:
        raise StandardizedInstrumentException("There is no data in the standardized_instrument table between {start_date} and {end_date}")

    return _create_df(instruments, start_date, end_date)


def create(instrument_create: StandardizedInstrumentCreate, db: Session) -> StandardizedInstrument:
    try:
        db_instrument = StandardizedInstrument(**instrument_create.dict())
        db.add(db_instrument)
        db.commit()
    except Exception as e:
        db.rollback()
        return None
    return db_instrument


def update(instruments: List[StandardizedInstrument], db: Session)\
        -> (List[StandardizedInstrument], List[StandardizedInstrument]):
    succeed_instruments: List[StandardizedInstrument] = []
    failed_instruments: List[StandardizedInstrument] = []
    for instrument in instruments:
        try:
            db_instrument = read(instrument_base=instrument, db=db)
            if db_instrument is None:
                failed_instruments.append(instrument)

            else:
                for key, value in instrument.dict(exclude_unset=True).items():
                    setattr(db_instrument, key, value)

                db.commit()
                succeed_instruments.append(instrument)
        except Exception as e:
            db.rollback()
            failed_instruments.append(instrument)

    return succeed_instruments, failed_instruments


def delete(instruments: List[StandardizedInstrument], db: Session)\
        -> (List[StandardizedInstrument], List[StandardizedInstrument]):
    succeed_instruments: List[StandardizedInstrument] = []
    failed_instruments: List[StandardizedInstrument] = []
    for instrument in instruments:
        try:
            db_instrument = read(instrument_base=instrument, db=db)
            if db_instrument is None:
                failed_instruments.append(instrument)
            else:
                db.query(StandardizedInstrument).filter_by(instrument=instrument.instrument).\
                    filter_by(source=instrument.source).filter_by(date=instrument.date).\
                    filter_by(type=instrument.type).delete()
                db.commit()
                succeed_instruments.append(db_instrument)
        except Exception as e:
            db.rollback()
            failed_instruments.append(instrument)

    return succeed_instruments, failed_instruments
