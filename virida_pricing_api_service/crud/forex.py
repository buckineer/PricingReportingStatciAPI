import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import func
from schemas.forex import ForexCreate
from models import Forex
import pandas as pd

def read_euro_exchange_rate_by_date(db: Session, date: dt.date):
    return db.query(Forex).filter(Forex.date <= date).filter(Forex.currency == "EUR").order_by(Forex.date.desc()).first()

def read_latest_euro_exchange_rate(db: Session):
    max_date = db.query(func.max(Forex.date))
    return db.query(Forex).filter(Forex.date == max_date).filter(Forex.currency == "EUR").one()

def read_latest_exchange_rates(db: Session):
    max_date = db.query(func.max(Forex.date))
    return db.query(Forex).filter(Forex.date == max_date).all()

def read_by_timeframe(start_date: dt.date, end_date: dt.date, db: Session):
    return db.query(Forex).filter(Forex.date >= start_date).filter(Forex.date <= end_date).all()

def fetch_forex_data(db: Session, currency=None, start_date=None):
    query = db.query(Forex.date, Forex.close).filter(Forex.currency == currency).filter(Forex.date >= start_date.strftime('%Y-%m-%d'))

    # ordering
    query = query.order_by(Forex.date)

    # get data
    data = query.all()

    # dataframe creation
    df = pd.DataFrame.from_records(data, index='date', columns=['date', 'fx_rate'])

    # fill the gaps and fill forward
    df = df.reindex(pd.date_range(df.index[0], df.index[-1], freq='D'))
    df.fillna(method="pad", inplace=True)  # forward fill

    return df


def create(db: Session, forex: ForexCreate):
    db_forex = Forex(**forex.dict())
    db.add(db_forex)
    db.commit()
    db.refresh(db_forex)
    return db_forex
