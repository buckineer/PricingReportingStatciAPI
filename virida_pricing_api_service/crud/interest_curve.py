from typing import Optional, Union
import datetime as dt

import pandas as pd
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from models import InterestCurve


class InterestCurveException(Exception):
    pass


def read(db: Session, start_date: Optional[dt.date] = None, end_date: Optional[dt.date] = None, curve: Optional[str] = "eua_curve") -> Union[list, InterestCurve]:
    query = db.query(InterestCurve).filter(InterestCurve.curve == curve)
    if start_date:
        query = query.filter(InterestCurve.date >= start_date)
    if end_date:
        query = query.filter(InterestCurve.date <= end_date)
    return query.all()


def _read_date(db: Session, first_date: bool=True):
    if first_date:
        result = db.query(func.min(InterestCurve.date)).first()
        if not result:
            return None
        return result[0]
    else:
        result = db.query(func.max(InterestCurve.date)).first()
        if not result:
            return None
        return result[0]

def _create_df(curves: list, start_date, end_date) -> pd.DataFrame:
    df = pd.DataFrame([{"date": curve.date, curve.curve: curve.value} for curve in curves]).groupby("date").apply(lambda value: value)
    df.set_index("date", inplace=True)
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
        raise InterestCurveException("There is no data in instrument_curve table")
    if end_date < first_date:
        return _create_df(read(db, first_date, first_date), start_date, end_date)
    if start_date > last_date:
        return _create_df(read(db, last_date, last_date), start_date, end_date)

    curves = read(db, start_date, end_date)
    if not curves:
        raise InterestCurveException(f"There is no data in the interest_curve table between {start_date} and {end_date}")

    return _create_df(curves, start_date, end_date)


def create(db: Session, interest_curve: InterestCurve):
    db_interest_curve = InterestCurve(**interest_curve.dict())
    db.add(db_interest_curve)
    db.commit()
    db.refresh(db_interest_curve)
    return db_interest_curve
