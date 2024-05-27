import os
import pprint
import datetime as dt
from pydantic.typing import is_new_type

import sqlalchemy
import pandas as pd
from fredapi import Fred
from google.cloud import error_reporting

import crud
import email_client
from schemas.benchmark import BenchmarkCreate
from helpers import alert
from database import get_db
from config import import_class

config_type = os.environ["APP_SETTINGS"]
config = import_class(config_type)
version = config_type.replace("config.", "").replace("Config", "").lower()


def snap_brent_europe():
    error_client = error_reporting.Client(service="snap_brent_europe", version=version)

    try:
        date = dt.datetime.now()
        if config_type == "config.LocalConfig":
            date = date - dt.timedelta(days=4) # for local testing

        db = next(get_db())

        fred_client = Fred(api_key=config.BRENT_API_KEY)
        brent_europe_df = fred_client.get_series(config.BRENT_SERIES_NAME).reset_index()
        brent_europe_df.columns = ['date', 'price']

        data = dict()
        data['date'] = (brent_europe_df.iloc[-1]['date']).replace(hour=0, minute=0, second=0, microsecond=0)
        data['price'] = float(brent_europe_df.iloc[-1]['price'])

        print('[+] Brent data: ')
        pprint.pprint(data)

        latest = crud.benchmark.read_latest_benchmarks(db=db, name='BRENTEU', type='spot')
        if not latest or latest[0].date < data['date']:
            crud.benchmark.create(
                db=db,
                benchmark=BenchmarkCreate(
                    date=data['date'],
                    name='BRENTEU',
                    type='spot',
                    symbol='BRENTEU',
                    currency='USD',
                    open=0,
                    high=0,
                    low=0,
                    close=data['price'],
                    volume=0,
                    timestamp=date
                )
            )

        print('[+] Brent europe data upload completed')
    except (sqlalchemy.exc.IntegrityError, Exception) as ex:
        print("[-] Error snapping Brent - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_brent_europe()
