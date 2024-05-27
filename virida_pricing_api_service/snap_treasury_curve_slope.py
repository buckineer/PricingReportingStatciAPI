import os
import pprint
import datetime as dt

import sqlalchemy
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


def snap_treasury_curve_slope():
    # https://pypi.org/project/fredapi/
    # slope = fred.get_series("T10Y3M").reset_index()
    # slope.columns = ["date", "10y3m"]
    # slope

    error_client = error_reporting.Client(service="snap_treasury_curve_slope", version=version)

    try:
        datetime = dt.datetime.now()
        if config_type == "config.LocalConfig":
            datetime = datetime - dt.timedelta(days=4) # for local testing

        db = next(get_db())

        fred_client = Fred(api_key=config.TREASURY_API_KEY)
        treasury_curve_slope_df = fred_client.get_series(config.TREASURY_SERIES_NAME).reset_index()
        treasury_curve_slope_df.columns = ["date", "10y3m"]

        print(treasury_curve_slope_df.tail(n=20))

        data = dict()
        data["date"] = treasury_curve_slope_df.iloc[-1]["date"]
        data["10y3m"] = float(treasury_curve_slope_df.iloc[-1]["10y3m"])

        print("[+] Treasury curve slope data:")
        pprint.pprint(data)

        latest = crud.benchmark.read_latest_benchmarks(db=db, name="T10Y3M", type="spot")
        if not latest or latest[0].date < data["date"]:
            crud.benchmark.create(
                db=db,
                benchmark=BenchmarkCreate(
                    date=data["date"].date(),
                    name="T10Y3M",
                    type="spot",
                    symbol="T10Y3M",
                    currency="XXX",
                    open=0,
                    high=0,
                    low=0,
                    close=data["10y3m"],
                    volume=0,
                    timestamp=datetime
                )
            )

        print("[+] Treasury curve slope data upload completed")
    except (sqlalchemy.exc.IntegrityError, Exception) as ex:
        print("[-] Error snapping Treasury Curve Slope - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_treasury_curve_slope()