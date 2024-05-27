import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import func
from schemas.interest_rate import InterestRateCreate
from models import InterestRate
import pandas as pd


def read(db: Session, date: dt.date):
    max_date_query = db.query(InterestRate.currency, InterestRate.tenor, func.max(InterestRate.date).label('max_date')).filter(InterestRate.date <= date).group_by(InterestRate.currency, InterestRate.tenor).subquery()

    return db.query(InterestRate).\
        filter(InterestRate.currency == max_date_query.c.currency)\
        .filter(InterestRate.tenor == max_date_query.c.tenor)\
        .filter(InterestRate.date == max_date_query.c.max_date)\
        .all()


def read_latest_interest_rates(db: Session):
    # on subqueries
    # https://stackoverflow.com/questions/14123763/how-can-i-join-two-queries-on-the-same-table-with-python-sqlalchemy

    # query to get max date for each benchmark / type
    max_date_query = db.query(InterestRate.currency, InterestRate.tenor, func.max(InterestRate.date).label('max_date')).group_by(InterestRate.currency, InterestRate.tenor).subquery()

    return db.query(InterestRate).\
        filter(InterestRate.currency == max_date_query.c.currency)\
        .filter(InterestRate.tenor == max_date_query.c.tenor)\
        .filter(InterestRate.date == max_date_query.c.max_date)\
        .all()


def create(db: Session, interest_rate: InterestRateCreate):
    db_interest_rate = InterestRate(**interest_rate.dict())
    db.add(db_interest_rate)
    db.commit()
    db.refresh(db_interest_rate)
    return db_interest_rate
