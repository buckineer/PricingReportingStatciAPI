import os
import io
import ftplib
import pprint
import datetime as dt

import pandas as pd
import sqlalchemy
from google.cloud import error_reporting

import crud
import email_client
from schemas.benchmark import BenchmarkCreate
from core.static import MONTH_NUMBERS_TO_CODES
from helpers import alert
from database import get_db
from config import import_class

config_type = os.environ["APP_SETTINGS"]
config = import_class(config_type)
version = config_type.replace("config.", "").replace("Config", "").lower()


def snap_atmospheric_co2():
    error_client = error_reporting.Client(service="snap_eua", version=version)

    try:
        date = dt.datetime.now()
        if config_type == "config.LocalConfig":
            date = date - dt.timedelta(days=1) # for local testing

        db = next(get_db())

        csv_file = io.BytesIO()
        ftp = ftplib.FTP(config.CO2_SERVER_HOST)
        ftp.login()
        ftp.cwd(config.CO2_SERVER_PATH)
        ftp.retrbinary('RETR {0}'.format(config.CO2_SERVER_FILENAME), csv_file.write)
        csv_file.seek(0)
        df = pd.read_csv(csv_file, comment="#")

        data = dict()
        data['date'] = dt.date(int(df.iloc[-1]['year']), int(df.iloc[-1]['month']), int(df.iloc[-1]['day']))
        data['smoothed'] = float(df.iloc[-1]['smoothed'])
        data['trend'] = float(df.iloc[-1]['trend'])

        print('[+] Atmospheric co2 data: ')
        pprint.pprint(data)

        latest = crud.benchmark.read_latest_benchmarks(db=db, name='CO2', type='spot')
        if not latest or latest[0].date < data['date']:
            crud.benchmark.create(
                db=db,
                benchmark=BenchmarkCreate(
                    date=data['date'],
                    name='CO2',
                    type='spot',
                    symbol='CO2' + 'SM',
                    currency='XXX',
                    open=0,
                    high=0,
                    low=0,
                    close=data['smoothed'],
                    volume=0,
                    timestamp=date
                )
            )
            crud.benchmark.create(
                db=db,
                benchmark=BenchmarkCreate(
                    date=data['date'],
                    name='CO2',
                    type='spot',
                    symbol='CO2' + 'TR',
                    currency='XXX',
                    open=0,
                    high=0,
                    low=0,
                    close=data['trend'],
                    volume=0,
                    timestamp=date
                )
            )

        print('[+] Atmospheric co2 data upload completed')
    except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.SQLAlchemyError, Exception) as ex:
        print("[-] Error snapping CO2 - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_atmospheric_co2()
