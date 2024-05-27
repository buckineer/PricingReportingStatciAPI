import os
import sys
import datetime as dt
import math
from typing import Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from pydantic import parse_obj_as

import crud
import email_client
from crud.benchmark import fetch_benchmark_dataframe
from core.static import CO2_INDEX_LOOKBACK, INDEX_HISTORY_REFERENCE_DATE, FILL_FORWARD_LOOKBACK
from schemas.benchmark_index import BenchmarkIndex
from schemas.email import BenchmarkIndexEmailTemplate
from schemas.system import System
from schemas.interest_curve import InterestCurve
from database import DatabaseContextManager

from config import import_class
import os

config = import_class(os.environ['APP_SETTINGS'])
ENV = os.environ["APP_SETTINGS"].replace("config.", "").replace("Config", "").lower()



def get_indexes(db: Session, end_date: dt.date) -> Tuple[pd.DataFrame, dict]:
    market_data = dict()
    start_date = INDEX_HISTORY_REFERENCE_DATE - dt.timedelta(days=FILL_FORWARD_LOOKBACK)
    benchmarks_df = pd.DataFrame(columns=["date"]).set_index("date")

    try:
        eua_df = fetch_benchmark_dataframe(db, name='EUA', symbol='CKSPT', type='spot', start_date=start_date, end_date=end_date, frequency='B', ccy_convert=True)
        eua_index_ref_date_price_usd = eua_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value_usd']
        eua_last_date_price_usd = eua_df.iloc[-1]['value_usd']
        eua_index = eua_last_date_price_usd / eua_index_ref_date_price_usd
        market_data["eua"] = float(eua_index)
        benchmarks_df = pd.concat([benchmarks_df, eua_df["value_usd"].rename("eua")], axis=1)
    except Exception as ex:
        print(ex)
        market_data["eua"] = -1.0

    try:
        co2_df = fetch_benchmark_dataframe(db, name='CO2', symbol='CO2SM', type='spot', start_date=(start_date - dt.timedelta(days=370)), end_date=end_date, frequency='D')
        co2_df['roc'] = co2_df['value'].pct_change(periods=CO2_INDEX_LOOKBACK)
        co2_ref_date_roc = co2_df[co2_df.index >= INDEX_HISTORY_REFERENCE_DATE].loc[INDEX_HISTORY_REFERENCE_DATE]['roc']
        co2_last_date_roc = co2_df.iloc[-1]['roc']
        co2_index = co2_last_date_roc / co2_ref_date_roc
        co2_index = np.exp(100. * (co2_last_date_roc - co2_ref_date_roc))
        market_data["co2"] = float(co2_index)
        benchmarks_df = pd.concat([benchmarks_df, co2_df["value_usd"].rename("co2")], axis=1)
    except Exception as ex:
        print(ex)
        market_data["co2"] = -1.0

    try:
        brent_df = fetch_benchmark_dataframe(db, name='BRENTEU', symbol='BRENTEU', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        brent_ref_date_price = brent_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        brent_last_date_price = brent_df.iloc[-1]['value']
        brent_index = brent_last_date_price / brent_ref_date_price
        market_data["brent"] = float(brent_index)
        benchmarks_df = pd.concat([benchmarks_df, brent_df["value_usd"].rename("brent")], axis=1)
    except Exception as ex:
        print(ex)
        market_data["brent"] = -1.0


    try:
        treasury_df = fetch_benchmark_dataframe(db, name='T10Y3M', symbol='T10Y3M', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        change = 10. - 0.25
        treasury_df['slope'] = treasury_df['value'] / change
        treasury_ref_date_slope = treasury_df.loc[INDEX_HISTORY_REFERENCE_DATE]['slope']
        treasury_last_date_slope = treasury_df.iloc[-1]['slope']
        treasury_index = np.exp(treasury_last_date_slope - treasury_ref_date_slope)
        market_data["treasury"] = float(treasury_index)
        benchmarks_df = pd.concat([benchmarks_df, treasury_df["value_usd"].rename("treasury")], axis=1)
    except Exception as ex:
        print(ex)
        market_data["treasury"] = -1.0


    try:
        oil_df = fetch_benchmark_dataframe(db, name='oil', symbol='PDB', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        oil_ref_date_price = oil_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        oil_last_date_price = oil_df.iloc[-1]['value']
        oil_index = oil_last_date_price / oil_ref_date_price
        market_data["oil"] = float(oil_index)
        benchmarks_df = pd.concat([benchmarks_df, oil_df["value_usd"].rename("oil")], axis=1)
        print("---------OIL-----------")
        print("REF_DATE_PRICE: ", oil_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", oil_last_date_price)
        print("INDEX: ", market_data["oil"])
    except Exception as ex:
        print(ex)
        market_data["oil"] = -1.0


    try:
        coal_df = fetch_benchmark_dataframe(db, name='coal', symbol='PTCWCI', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        coal_ref_date_price = coal_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        coal_last_date_price = coal_df.iloc[-1]['value']
        coal_index = coal_last_date_price / coal_ref_date_price
        market_data["coal"] = float(coal_index)
        benchmarks_df = pd.concat([benchmarks_df, coal_df["value_usd"].rename("coal")], axis=1)
        print("\n---------COAL-----------")
        print("REF_DATE_PRICE: ", coal_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", coal_last_date_price)
        print("INDEX: ", market_data["coal"])
    except Exception as ex:
        print(ex)
        market_data["coal"] = -1.0


    try:
        gas_df = fetch_benchmark_dataframe(db, name='gas', symbol='PTTFM1', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        gas_ref_date_price = gas_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        gas_last_date_price = gas_df.iloc[-1]['value']
        gas_index = gas_last_date_price / gas_ref_date_price
        market_data["gas"] = float(gas_index)
        benchmarks_df = pd.concat([benchmarks_df, gas_df["value_usd"].rename("gas")], axis=1)
        print("\n---------GAS-----------")
        print("REF_DATE_PRICE: ", gas_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", gas_last_date_price)
        print("INDEX: ", market_data["gas"])
    except Exception as ex:
        print(ex)
        market_data["gas"] = -1.0


    try:
        carbon_df = fetch_benchmark_dataframe(db, name='carbon', symbol='PCEC', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        carbon_ref_date_price = carbon_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        carbon_last_date_price = carbon_df.iloc[-1]['value']
        carbon_index = carbon_last_date_price / carbon_ref_date_price
        market_data["carbon"] = float(carbon_index)
        benchmarks_df = pd.concat([benchmarks_df, carbon_df["value_usd"].rename("carbon")], axis=1)
        print("\n---------CARBON-----------")
        print("REF_DATE_PRICE: ", carbon_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", carbon_last_date_price)
        print("INDEX: ", market_data["carbon"])
    except Exception as ex:
        print(ex)
        market_data["carbon"] = -1.0


    try:
        equity_df = fetch_benchmark_dataframe(db, name='equity', symbol='DJESG', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        equity_ref_date_price = equity_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        equity_last_date_price = equity_df.iloc[-1]['value']
        equity_index = equity_last_date_price / equity_ref_date_price
        market_data["equity"] = float(equity_index)
        benchmarks_df = pd.concat([benchmarks_df, equity_df["value_usd"].rename("equity")], axis=1)
        print("\n---------EQUITY-----------")
        print("REF_DATE_PRICE: ", equity_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", equity_last_date_price)
        print("INDEX: ", market_data["equity"])
    except Exception as ex:
        print(ex)
        market_data["equity"] = -1.0
    

    try:
        credit_df = fetch_benchmark_dataframe(db, name='credit', symbol='SNPGBI', type='spot', start_date=start_date, end_date=end_date, frequency='B')
        credit_ref_date_price = credit_df.loc[INDEX_HISTORY_REFERENCE_DATE]['value']
        credit_last_date_price = credit_df.iloc[-1]['value']
        credit_index = credit_last_date_price / credit_ref_date_price
        market_data["credit"] = float(credit_index)
        benchmarks_df = pd.concat([benchmarks_df, credit_df["value_usd"].rename("credit")], axis=1)
        print("\n---------CREDIT-----------")
        print("REF_DATE_PRICE: ", credit_ref_date_price)
        print("REF_LAST_DATE_PRICE: ", credit_last_date_price)
        print("INDEX: ", market_data["credit"])
    except Exception as ex:
        print(ex)
        market_data["credit"] = -1.0
    
    benchmarks_df.fillna(method="pad", inplace=True)
    benchmarks_df.fillna(method="backfill", inplace=True)
    benchmarks_df = benchmarks_df[(benchmarks_df.index >= INDEX_HISTORY_REFERENCE_DATE.date()) & (benchmarks_df.index <= end_date)] 
    return benchmarks_df, market_data


def difference(new: float, previous: float) -> str:
    percentage = (new / previous - 1.0) * 100
    if percentage == 0: # check for -0.00 cases
        percentage = 0.0
    return "{:.2f}".format(percentage)


def stale(new: float, previous: float) -> bool:
    return abs(new / previous - 1.0) < 10**(config.BENCHMARK_INDEX_STALE_THRESHOLD)


def str_value(value: float) -> str:
    return "{:.6f}".format(value)


def html(indexes: str):
    head = """
    <div style="width: 100%; overflow-x: scroll;">
        <table border="1" style="border-collapse: collapse; font-family: Helvetica; width: 100%; white-space: nowrap;">
            <tr>
                <th>Index</th>
                <th>New value</th>
                <th>Previous value</th>
                <th>Change</th>
                <th>Stale</th>
            </tr>
    """

    body = ""
    for index in indexes:
        body = body + f"""
        <tr>
            <td>{index["benchmark"]}</td>
            <td>{str_value(index["new"])}</td>
            <td>{str_value(index["previous"])}</td>
            <td>{difference(index["new"], index["previous"])}%</td>
            <td>{stale(index["new"], index["previous"])}</td>
        </tr>
        """
    
    footer = """</table></div>"""
    return head + body + footer


def shift_system_date(db: Session) -> dt.date:
    system: System = parse_obj_as(System, crud.system.read(db))
    if system is None:
        system = System(date=dt.date.today())
    else:
        system.date = system.date + dt.timedelta(days=1)
    return crud.system.update(db, system).date


def get_system_date(db: Session) -> dt.date:
    return crud.system.read(db).date


def get_previous_indexes(db: Session) -> list:
    date = get_system_date(db) - dt.timedelta(days=1)
    return crud.benchmark_index.read_dataframe(db, date, date).to_dict("index")[date]


def formatted_exception() -> tuple:
    err_info: tuple = sys.exc_info()
    err_module: str = err_info[0].__module__
    err_name: str = err_info[0].__name__
    err_type: str = err_name if err_module == "__main__" else f"{err_module}.{err_name}"
    err_file = os.path.split(err_info[2].tb_frame.f_code.co_filename)[1]
    err_line = err_info[2].tb_lineno
    err_message: str = str(sys.exc_info()[1])
    return (err_type, err_message, f"{err_file}:{err_line}")


def benchmarks_table_html(df: pd.DataFrame):
    df = pd.concat([df.head(), df.tail()])

    head = """
    <div style="width: 100%; overflow-x: scroll;">
        <table border="1" style="border-collapse: collapse; font-family: Helvetica; width: 100%; white-space: nowrap;">
    """

    head_row = f"""<tr>
    <th>Date</th>
    <th>EUA</th>
    <th>CO2</th>
    <th>Brent</th>
    <th>Treasury</th>
    <th>Oil</th>
    <th>Coal</th>
    <th>Gas</th>
    <th>Carbon</th>
    <th>Equity</th>
    <th>Credit</th>
    </tr>
    """

    head = head + head_row

    df["html_row"] = df.apply(lambda row: f"""
    <td>{row.name.date()}</td>
    <td>{round(row['eua'], 6)}</td>
    <td>{round(row['co2'], 6)}</td>
    <td>{round(row['brent'], 6)}</td>
    <td>{round(row['treasury'], 6)}</td>
    <td>{round(row['oil'], 6)}</td>
    <td>{round(row['coal'], 6)}</td>
    <td>{round(row['gas'], 6)}</td>
    <td>{round(row['carbon'], 6)}</td>
    <td>{round(row['equity'], 6)}</td>
    <td>{round(row['credit'], 6)}</td>
    """, axis=1)

    body = ""
    for date, row in df.iterrows():
        body = body + f"<tr>{row['html_row']}</tr>"
    
    footer = "</table></div>"

    return head + body + footer

def interest_curve_table_html(db: Session, date: dt.date):
    start_date = date - dt.timedelta(days=5)
    end_date = date

    benchmarks = []
    for day in range((end_date - start_date).days):
        benchmarks = benchmarks + crud.benchmark.read_benchmarks(db, date - dt.timedelta(days=day), "EUA", "forward")

    expiry_dates = sorted(set([benchmark.expiry_date for benchmark in benchmarks]))

    head = """
    <br/>
    <br/>
    <p>Interest Rate</p>
    <div style="width: 100%; overflow-x: scroll;">
        <table border="1" style="border-collapse: collapse; font-family: Helvetica; width: 100%; white-space: nowrap;">
    """

    expiry_dates_html = ""
    for date in expiry_dates:
        expiry_dates_html = expiry_dates_html + f"<th>{date.strftime('%Y-%m-%d')}</th>"
    
    head_row = f"<tr><th>Date</th>{expiry_dates_html}</tr>"
    head = head + head_row
    body = ""

    curves = crud.interest_curve.read(db, start_date, end_date)
    for curve in curves:
        row = f"<td>{curve.date}</td>"
        for expiry_date in expiry_dates:
            try:
                index = curve.value["times"].index((expiry_date - curve.date).days / 365)
                value = round(curve.value["rates"][index], 6)
            except ValueError as ex:
                value = "N/A"
            row = row + f"<td>{value}</td>"
        body = body + f"<tr>{row}</tr>"
    body = body + "</table></div>"

    return head + body


def interest_curve(db: Session, date: dt.date):
    benchmarks = crud.benchmark.read_benchmarks(db, date, "EUA", "forward")
    benchmarks = sorted(benchmarks, key=lambda benchmark: benchmark.expiry_date)

    spot_benchmark = crud.benchmark.read_benchmarks(db, date, "EUA", "spot")[0]

    value = {"times": [], "rates": []}
    for benchmark in benchmarks:
        if benchmark.expiry_date < date:
            continue

        value["times"].append((benchmark.expiry_date - date).days / 365)
        value["rates"].append(benchmark.close / spot_benchmark.close - 1)

    crud.interest_curve.create(
        db=db,
        interest_curve=InterestCurve(date=date, curve="eua_curve", value=value)
    )


def main(db: Session):
    try:
        current_system_date = get_system_date(db)
        benchmarks_df, indexes = get_indexes(db, current_system_date)
        previous_indexes = get_previous_indexes(db)

        errors = []
        benchmarks = indexes.keys()
        for benchmark in benchmarks:
            try:
                crud.benchmark_index.create(db, BenchmarkIndex(
                    date=current_system_date,
                    benchmark=benchmark,
                    value=indexes[benchmark]
                ))
            except Exception:
                errors.append({f"Error trying to insert new '{benchmark}' index": formatted_exception()})
        
        interest_curve(db, current_system_date)

        shifted_date = shift_system_date(db)
        status = "Failed" if errors else "Completed"

        email_client.send_indexes_email(BenchmarkIndexEmailTemplate(
            date=str(shifted_date),
            subject=f"EOD {current_system_date} - {status} [{ENV}]",
            benchmarks_table=benchmarks_table_html(benchmarks_df) + interest_curve_table_html(db, current_system_date),
            table=html([
                {
                    "benchmark": benchmark,
                    "new": indexes[benchmark],
                    "previous": previous_indexes[benchmark] if benchmark in previous_indexes else math.nan,
                } for benchmark in benchmarks]
            ),
            errors=str(errors)
        ))
    except Exception:
        email_client.send_indexes_email(BenchmarkIndexEmailTemplate(
            date=str(get_system_date(db)),
            benchmarks_table="",
            table="",
            subject=f"EOD {get_system_date(db)} - Failed [{ENV}]",
            errors=str(formatted_exception())
        ))


if __name__ == "__main__":
    with DatabaseContextManager() as db:
        main(db)
