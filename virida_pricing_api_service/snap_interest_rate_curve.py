import os
import pprint
import datetime as dt

import sqlalchemy
from fredapi import Fred
from google.cloud import error_reporting

import crud
import email_client
from schemas.interest_rate import InterestRateCreate
from helpers import alert
from database import get_db
from config import import_class

config_type = os.environ["APP_SETTINGS"]
config = import_class(config_type)
version = config_type.replace("config.", "").replace("Config", "").lower()

def snap_interest_rate_curve():
    # https://pypi.org/project/fredapi/
    # https://fred.stlouisfed.org/series/DGS6MO

    error_client = error_reporting.Client(service="snap_brent_europe", version=version)

    try:
        datetime = dt.datetime.now()
        if config_type == "config.LocalConfig":
            datetime = datetime - dt.timedelta(days=4) # for local testing

        db = next(get_db())

        series_names = {
            "1M": "DGS1MO",
            "3M": "DGS3MO",
            "6M": "DGS6MO",
            "1Y": "DGS1",
            "1Y": "DGS1",
            "1Y": "DGS1",
            "2Y": "DGS2",
            "3Y": "DGS3",
            "5Y": "DGS5",
            "7Y": "DGS7",
            "10Y": "DGS10",
            "20Y": "DGS20",
            "30Y": "DGS30" 
        }

        fred_client = Fred(api_key=config.INTEREST_RATE_API_KEY)

        data = []
        for tenor, series_name in series_names.items():
            df = fred_client.get_series(series_name).reset_index()
            df.columns = ["date", "rate"]
            df["rate"] /= 100.  # we want to store interest rates in decimals

            item = dict()
            item["date"] = df.iloc[-1]["date"]
            item["currency"] = "USD"
            item["tenor"] = tenor
            item["rate"] = float(df.iloc[-1]["rate"]) if df.iloc[-1]["rate"] == df.iloc[-1]["rate"] else None
            data.append(item)

        print("[+] USD interest rate data:")
        pprint.pprint(data)

        for item in data:
            if item["rate"] is None:
                continue

            latest = crud.interest_rate.read_latest_interest_rates(db=db)
            if not latest or latest[0].date < item['date']:
                crud.interest_rate.create(
                    db=db,
                    interest_rate=InterestRateCreate(
                        date=item["date"].date(),
                        currency=item["currency"],
                        tenor=item["tenor"],
                        rate=item["rate"],
                        timestamp=datetime
                    )
                )

        print("[+] USD interest rates successfully snapped for ", datetime.strftime("%Y-%m-%d"))
    except Exception as ex:
        print("[-] Error snapping Interest Rate Curve - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_interest_rate_curve()
