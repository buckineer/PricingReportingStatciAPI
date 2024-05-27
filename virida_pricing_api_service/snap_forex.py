import os
import requests
import json
import datetime as dt

from sqlalchemy.exc import IntegrityError
from google.cloud import error_reporting

import crud
import email_client
from database import get_db
from schemas.forex import ForexCreate
from helpers import alert
from config import import_class

config_type = os.environ['APP_SETTINGS']
config = import_class(config_type)
version = config_type.replace("config.", "").replace("Config", "").lower()


def snap_exchange_rates():
    db = next(get_db())
    error_client = error_reporting.Client(service="snap_forex", version=version)
    datetime = dt.datetime.now()

    try:
        # snap EUR crosses (i.e. base=EUR). Other base currency not included in free plan of api.exchangeratesapi.io
        response = requests.get(config.FX_API_REST_URL)
        data = json.loads(response.text)
        fx_eur_usd = float(data['rates']['USD']) # EUR/USD

        latest_date: dt.date = dt.datetime.strptime(data['date'], '%Y-%m-%d').date()
        latest = crud.forex.read_latest_exchange_rates(db=db)
        if not latest or latest[0].date < latest_date:
            for currency in data['rates']:
                fx_eur_ccy = float(data['rates'][currency])
                fx_usd_ccy = fx_eur_ccy / fx_eur_usd

                crud.forex.create(
                    db=db,
                    forex=ForexCreate(
                    date=datetime.date(),
                    currency=currency,
                    close=fx_usd_ccy,
                    timestamp=datetime
                    )
                )

        print('[+] Exchange rates successfully snapped for {0}'.format(datetime.strftime('%Y-%m-%d')))
    except (IntegrityError, Exception) as ex:
        print("[-] Error snapping forex - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_exchange_rates()
