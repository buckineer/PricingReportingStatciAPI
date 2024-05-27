from typing import List
import datetime as dt

from sqlalchemy.orm import Session

import crud
from models import Forex, Benchmark
from core.static import MONTH_CODES_TO_NUMBERS, INDEX_REFERENCE_DATE, CO2_INDEX_LOOKBACK
from crud.benchmark import fetch_benchmark_dataframe
import numpy as np


def get_market_data_v5_v62(db: Session, date: dt.date):
    try:
        forex: Forex = crud.forex.read_euro_exchange_rate_by_date(db=db, date=date)
        euro_to_usd_forex = 1. / forex.close
        benchmarks: List[Benchmark] = crud.benchmark.read_benchmarks(db=db, date=date, name='EUA', type='forward')
        benchmarks = sorted(benchmarks, key=lambda k: k.expiry_date)

        market_data = {
            "spot": benchmarks[0].close * euro_to_usd_forex
        }

        for benchmark in benchmarks:
            key = benchmark.expiry_date.strftime('%b%Y').lower()
            market_data[key] = benchmark.close * euro_to_usd_forex

        return market_data

    except Exception as ex:
        print("[-] Exception while reading the market data - {0}".format(str(ex)))
        euro_to_usd_forex = 1.19864
        market_data = {'spot': 24.66 * euro_to_usd_forex, 'dec2020': 24.73 * euro_to_usd_forex,
                       'dec2021': 25.05 * euro_to_usd_forex, 'dec2022': 25.46 * euro_to_usd_forex}

        return market_data


def get_market_data_v5_v6(db: Session):
    try:
        forex: Forex = crud.forex.read_latest_euro_exchange_rate(db=db)
        euro_to_usd_forex = 1. / forex.close
        benchmarks: List[Benchmark] = crud.benchmark.read_latest_benchmarks(db=db, name='EUA', type='forward')
        benchmarks = sorted(benchmarks, key=lambda k: k.expiry_date)

        market_data = {
            "spot": benchmarks[0].close * euro_to_usd_forex
        }

        for benchmark in benchmarks:
            key = benchmark.expiry_date.strftime('%b%Y').lower()
            market_data[key] = benchmark.close * euro_to_usd_forex

        return market_data
    except Exception as ex:
        print("[-] Exception while reading the market data - {0}".format(str(ex)))
        euro_to_usd_forex = 1.19864
        market_data = {'spot': 24.66 * euro_to_usd_forex, 'dec2020': 24.73 * euro_to_usd_forex,
                       'dec2021': 25.05 * euro_to_usd_forex, 'dec2022': 25.46 * euro_to_usd_forex}

        return market_data


from datetime import timedelta
def get_market_data2(db: Session, date: dt.date):
    try:
        market_data = dict()

        # EUA
        # x['price'] = x['eua_spot'] / x['fx_usdeur']
        # k = x['date']==index_date
        # x['index'] = x['price']/x['price'][k].values[0]
        eua_df = fetch_benchmark_dataframe(db, name='EUA', symbol='CKSPT', type='spot', start_date=INDEX_REFERENCE_DATE, frequency='B', ccy_convert=True)
        eua_last_date_price = eua_df.iloc[-1]['value']
        eua_index_ref_date_price_usd = eua_df.iloc[0]['value_usd']
        eua_last_date_price_usd = eua_df.iloc[-1]['value_usd']
        eua_last_date = eua_df.index[-1]
        eua_currency = eua_df.iloc[0]['currency']
        eua_index = eua_last_date_price_usd / eua_index_ref_date_price_usd

        # EUA forward
        eua_forward = crud.benchmark.read_benchmarks(db, date=date, name='EUA', type='forward')

        # CO2
        # x(t): co2 level in ppm (cycle, smoothed column)
        # y(t) = x(t) / x(t-365)
        # index(t) =  exp(100.0 * (y(t) - y(t0))
        # t0: 2020-01-01
        co2_df = fetch_benchmark_dataframe(db, name='CO2', symbol='CO2SM', type='spot', start_date=(INDEX_REFERENCE_DATE - timedelta(days=370)), frequency='D')
        co2_df['roc'] = co2_df['value'].pct_change(periods=CO2_INDEX_LOOKBACK)
        co2_ref_date_roc = co2_df[co2_df.index >= INDEX_REFERENCE_DATE].iloc[0]['roc']
        co2_last_date_roc = co2_df.iloc[-1]['roc']
        co2_last_date_price = co2_df.iloc[-1]['value']
        co2_last_date = co2_df.index[-1]
        co2_currency = co2_df.iloc[0]['currency']
        co2_index = co2_last_date_roc / co2_ref_date_roc

        # Brent Europe
        # k = x['date']==index_date
        # x['index'] = x['price']/x['price'][k].values[0]
        brent_df = fetch_benchmark_dataframe(db, name='BRENTEU', symbol='BRENTEU', type='spot', start_date=INDEX_REFERENCE_DATE, frequency='B')
        brent_ref_date_price = brent_df.iloc[0]['value']
        brent_last_date_price = brent_df.iloc[-1]['value']
        brent_last_date = brent_df.index[-1]
        brent_currency = brent_df.iloc[0]['currency']
        brent_index = brent_last_date_price / brent_ref_date_price

        # US Treasury Curve Slope (10Y minus 3M)
        # dt = 10.-1/4
        # x['slope'] = x['10y3m']/dt
        # k = x['date']==index_date
        # x['index'] = np.exp(x['slope']-x['slope'][k].values[0])
        treasury_df = fetch_benchmark_dataframe(db, name='T10Y3M', symbol='T10Y3M', type='spot',
                                                start_date=INDEX_REFERENCE_DATE, frequency='B')
        dt = 10. - 0.25
        treasury_df['slope'] = treasury_df['value'] / dt
        treasury_ref_date_slope = treasury_df.iloc[0]['slope']
        treasury_last_date_slope = treasury_df.iloc[-1]['slope']
        treasury_last_date_price = treasury_df.iloc[-1]['value']
        treasury_last_date = treasury_df.index[-1]
        treasury_currency = treasury_df.iloc[0]['currency']
        treasury_index = np.exp(treasury_last_date_slope - treasury_ref_date_slope)

        # USD interest rates
        interest_rate_data = crud.interest_rate.read(db, date=date)

        # indices
        market_data['indices'] = dict()
        market_data['indices']['eua'] = {'value': float(eua_index), 'date': eua_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['co2'] = {'value': float(co2_index), 'date': co2_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['brent'] = {'value': float(brent_index), 'date': brent_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['treasury'] = {'value': float(treasury_index), 'date': treasury_last_date.to_pydatetime().strftime('%Y-%m-%d')}

        # prices
        market_data['prices'] = dict()
        market_data['prices']['spot'] = dict()
        market_data['prices']['spot']['eua'] = {'value': float(eua_last_date_price), 'currency': eua_currency, 'date': eua_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['co2'] = {'value': float(co2_last_date_price), 'currency': co2_currency, 'date': co2_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['brent'] = {'value': float(brent_last_date_price), 'currency': brent_currency, 'date': brent_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['treasury'] = {'value': float(treasury_last_date_price), 'currency': treasury_currency, 'date': treasury_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['forward'] = dict()
        market_data['prices']['forward']['eua'] = dict()
        for contract in eua_forward:
            market_data['prices']['forward']['eua'][contract.expiry_date.strftime('%b%Y').lower()] = {
                'value': float(contract.close),
                'currency': contract.currency,
                'date': contract.date.strftime('%Y-%m-%d'),
                'expiry_date': contract.expiry_date.strftime('%Y-%m-%d')
            }

        # interest rates
        market_data['interest_rates'] = []
        for item in interest_rate_data:
            market_data['interest_rates'].append({
                'date': item.date.strftime('%Y-%m-%d'),
                'currency': item.currency,
                'tenor': item.tenor,
                'rate': item.rate})

        return market_data
    except Exception as ex:
        print("[-] Exception while reading the market data - {0}".format(str(ex)))
        market_data = dict()
        market_data['indices'] = dict()
        market_data['indices']['eua'] = {'value': 1.5152121389105802, 'date': '0001-01-01'}
        market_data['indices']['co2'] = {'value': 0.8082728770529001, 'date': '0001-01-01'}
        market_data['indices']['brent'] = {'value': 0.8295580483424855, 'date': '0001-01-01'}
        market_data['indices']['treasury'] = {'value': 1.0713003652157234, 'date': '0001-01-01'}

        return market_data

def get_market_data(db: Session):
    try:
        market_data = dict()

        # EUA
        # x['price'] = x['eua_spot'] / x['fx_usdeur']
        # k = x['date']==index_date
        # x['index'] = x['price']/x['price'][k].values[0]
        eua_df = fetch_benchmark_dataframe(db, name='EUA', symbol='CKSPT', type='spot', start_date=INDEX_REFERENCE_DATE, frequency='B', ccy_convert=True)
        eua_last_date_price = eua_df.iloc[-1]['value']
        eua_index_ref_date_price_usd = eua_df.iloc[0]['value_usd']
        eua_last_date_price_usd = eua_df.iloc[-1]['value_usd']
        eua_last_date = eua_df.index[-1]
        eua_currency = eua_df.iloc[0]['currency']
        eua_index = eua_last_date_price_usd / eua_index_ref_date_price_usd

        # EUA forward
        eua_forward = crud.benchmark.read_latest_benchmarks(db, name='EUA', type='forward')

        # CO2
        # x(t): co2 level in ppm (cycle, smoothed column)
        # y(t) = x(t) / x(t-365)
        # index(t) =  exp(100.0 * (y(t) - y(t0))
        # t0: 2020-01-01
        co2_df = fetch_benchmark_dataframe(db, name='CO2', symbol='CO2SM', type='spot', start_date=(INDEX_REFERENCE_DATE - timedelta(days=370)), frequency='D')
        co2_df['roc'] = co2_df['value'].pct_change(periods=CO2_INDEX_LOOKBACK)
        co2_ref_date_roc = co2_df[co2_df.index >= INDEX_REFERENCE_DATE].iloc[0]['roc']
        co2_last_date_roc = co2_df.iloc[-1]['roc']
        co2_last_date_price = co2_df.iloc[-1]['value']
        co2_last_date = co2_df.index[-1]
        co2_currency = co2_df.iloc[0]['currency']
        co2_index = np.exp(100. * (co2_last_date_roc - co2_ref_date_roc))

        # Brent Europe
        # k = x['date']==index_date
        # x['index'] = x['price']/x['price'][k].values[0]
        brent_df = fetch_benchmark_dataframe(db, name='BRENTEU', symbol='BRENTEU', type='spot', start_date=INDEX_REFERENCE_DATE, frequency='B')
        brent_ref_date_price = brent_df.iloc[0]['value']
        brent_last_date_price = brent_df.iloc[-1]['value']
        brent_last_date = brent_df.index[-1]
        brent_currency = brent_df.iloc[0]['currency']
        brent_index = brent_last_date_price / brent_ref_date_price

        # US Treasury Curve Slope (10Y minus 3M)
        # dt = 10.-1/4
        # x['slope'] = x['10y3m']/dt
        # k = x['date']==index_date
        # x['index'] = np.exp(x['slope']-x['slope'][k].values[0])
        treasury_df = fetch_benchmark_dataframe(db, name='T10Y3M', symbol='T10Y3M', type='spot',
                                                start_date=INDEX_REFERENCE_DATE, frequency='B')
        dt = 10. - 0.25
        treasury_df['slope'] = treasury_df['value'] / dt
        treasury_ref_date_slope = treasury_df.iloc[0]['slope']
        treasury_last_date_slope = treasury_df.iloc[-1]['slope']
        treasury_last_date_price = treasury_df.iloc[-1]['value']
        treasury_last_date = treasury_df.index[-1]
        treasury_currency = treasury_df.iloc[0]['currency']
        treasury_index = np.exp(treasury_last_date_slope - treasury_ref_date_slope)

        # USD interest rates
        interest_rate_data = crud.interest_rate.read_latest_interest_rates(db)

        # indices
        market_data['indices'] = dict()
        market_data['indices']['eua'] = {'value': float(eua_index), 'date': eua_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['co2'] = {'value': float(co2_index), 'date': co2_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['brent'] = {'value': float(brent_index), 'date': brent_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['indices']['treasury'] = {'value': float(treasury_index), 'date': treasury_last_date.to_pydatetime().strftime('%Y-%m-%d')}

        # prices
        market_data['prices'] = dict()
        market_data['prices']['spot'] = dict()
        market_data['prices']['spot']['eua'] = {'value': float(eua_last_date_price), 'currency': eua_currency, 'date': eua_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['co2'] = {'value': float(co2_last_date_price), 'currency': co2_currency, 'date': co2_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['brent'] = {'value': float(brent_last_date_price), 'currency': brent_currency, 'date': brent_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['spot']['treasury'] = {'value': float(treasury_last_date_price), 'currency': treasury_currency, 'date': treasury_last_date.to_pydatetime().strftime('%Y-%m-%d')}
        market_data['prices']['forward'] = dict()
        market_data['prices']['forward']['eua'] = dict()
        for contract in eua_forward:
            market_data['prices']['forward']['eua'][contract.expiry_date.strftime('%b%Y').lower()] = {
                'value': float(contract.close),
                'currency': contract.currency,
                'date': contract.date.strftime('%Y-%m-%d'),
                'expiry_date': contract.expiry_date.strftime('%Y-%m-%d')
            }

        # interest rates
        market_data['interest_rates'] = []
        for item in interest_rate_data:
            market_data['interest_rates'].append({
                'date': item.date.strftime('%Y-%m-%d'),
                'currency': item.currency,
                'tenor': item.tenor,
                'rate': item.rate})

        return market_data
    except Exception as ex:
        print("[-] Exception while reading the market data - {0}".format(str(ex)))
        market_data = dict()
        market_data['indices'] = dict()
        market_data['indices']['eua'] = {'value': 1.5152121389105802, 'date': '0001-01-01'}
        market_data['indices']['co2'] = {'value': 0.8082728770529001, 'date': '0001-01-01'}
        market_data['indices']['brent'] = {'value': 0.8295580483424855, 'date': '0001-01-01'}
        market_data['indices']['treasury'] = {'value': 1.0713003652157234, 'date': '0001-01-01'}

        return market_data
