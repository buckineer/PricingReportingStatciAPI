import os
import datetime as dt
import paramiko
import pprint

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from fastapi import status
from google.cloud import error_reporting

import crud
from schemas.benchmark import BenchmarkCreate
from core.static import MONTH_NUMBERS_TO_CODES
from helpers import alert
from database import get_db
from config import import_class
import email_client

config_type = os.environ["APP_SETTINGS"]
config = import_class(config_type)
version = config_type.replace("config.", "").replace("Config", "").lower()


class SpotDataError(Exception):
    pass


class SnapFileError(Exception):
    pass


def get_float(number_as_str, decimal_sep=",", thousands_sep="."):
    aux = number_as_str.replace(decimal_sep, "[").replace(thousands_sep, "]")
    aux = aux.replace("[", ".").replace("]", "")
    return float(aux)


def get_file_as_lines(sftp_client, remote_fullpath) -> list:
    lines = []
    with sftp_client.open(remote_fullpath) as file:
        for line in file:
            if line != "":
                lines.append(line.replace("\n", "").replace("\r", ""))

    if len(lines) > 0:
        return lines
    else:
        raise SnapFileError("Downloaded file is empty")


def parse_eua_spot_file(lines: list): 
    # 1. check line count
    # 2. check that there is a line PR with EU Allowance
    # 3. that this line as the right number of fields
    sep = ";"
    # defined on 24-02-2021 after BLN found out that file format has changed
    # since may 2021, only maturity 2029-12 is traded
    # info given by EEX Support
    # 7-may-2021: Therefore from now on our files will only have entries for the 2029-12 maturity (until phase 5..).
    maturity = "2029-12"
    # in any case, basis between the 2 is not high
    # e.g. on 2021-02-23, we have 38.58 EUR/tCO2 [for 2029-12] and 38.61 EUR/tCO2 [for 2021-12]

    number_of_lines_is_correct = len(lines) == int(lines[-1].split(sep)[1])
    if not number_of_lines_is_correct:
        raise SnapFileError("Incorrect number of lines in file")

    data_fields = None

    for line in lines:
        fields = line.split(sep)
        if (fields[0] == "PR" and
            fields[1] == "EU" and
            fields[2] == "SEME" and
            fields[3] == maturity and
            fields[4] == "EEX EUA Spot"):
            data_fields = fields

    if data_fields is None:
        raise SpotDataError("Spot data line not found file")

    if len(data_fields) != 20:
        raise SpotDataError("Incorrect format for Spot data line")

    """
    Data type(PR); Market Area; Product; Maturity; Long Name; Open Price;
    Timestamp Open Price; High Price; Timestamp High Price; Low Price; Timestamp Low Price;
    Last Price; Timestamp Last Price; Settlement Price; Unit of Prices; Lot Size; Traded Lots;
    Number of Trades; Traded Volume; Unit of Volumes
    """
    return {
        "open": get_float(data_fields[5]) if data_fields[5] != "" else None,
        "high": get_float(data_fields[7]) if data_fields[7] != "" else None,
        "low": get_float(data_fields[9]) if data_fields[9] != "" else None,
        "close": get_float(data_fields[11]) if data_fields[11] != "" else None,
        "settlement": get_float(data_fields[13]) if data_fields[13] != "" else None,
        "volume": get_float(data_fields[18]) if data_fields[18] != "" else None
    }


def parse_eua_futures_file(lines):
    # 1. check line count
    # 2. check that there is a line PR with EU Allowance
    # 3. that this line as the right number of fields
    sep = ";"

    number_of_lines_is_correct = len(lines) == int(lines[-1].split(sep)[1])
    if not number_of_lines_is_correct:
        raise SnapFileError("Incorrect number of lines in file")

    data = []
    for line in lines:
        fields = line.split(sep)
        if fields[0] == "PR" and fields[1] == "FEUA" and len(fields) == 23:
            data.append({
                "contract": fields[3],
                "expiry": dt.datetime.strptime(fields[3], "%Y-%m"),
                "open": get_float(fields[6]) if fields[6] != "" else None,
                "high": get_float(fields[8]) if fields[8] != "" else None,
                "low": get_float(fields[10]) if fields[10] != "" else None,
                "close": get_float(fields[12]) if fields[12] != "" else None,
                "settlement": get_float(fields[14]) if fields[14] != "" else None,
                "volume": int(fields[19]) if fields[19] != "" else None,
                "oi": int(fields[21]) if fields[21] != "" else None
            })
    return data


def spot(db: Session, sftp: paramiko.SFTPClient, filename: str, datetime: dt.datetime) -> dict:
    data = parse_eua_spot_file(get_file_as_lines(sftp, filename))
    latest = crud.benchmark.read_latest_benchmarks(db=db, name='EUA', type='spot')
    if not latest or latest[0].date < datetime.date():
        crud.benchmark.create(
            db=db,
            benchmark=BenchmarkCreate(
                date=datetime.date(),
                name="EUA",
                type="spot",
                symbol="CK" + "SPT",
                currency="EUR",
                open=0,
                high=0,
                low=0,
                close=data["settlement"],
                volume=0,
                timestamp=datetime
            )
        )
    return data


def future(db: Session, sftp: paramiko.SFTPClient, filename: str, datetime: dt.datetime) -> dict:
    data = parse_eua_futures_file(get_file_as_lines(sftp, filename))
    latest = crud.benchmark.read_latest_benchmarks(db=db, name='EUA', type='forward')
    if not latest or latest[0].date < datetime.date():
        for contract in data:
            expiry_date = contract["expiry"]
            settlement = contract["settlement"]

            if settlement is None:
                continue
            try:
                crud.benchmark.create(
                    db=db,
                    benchmark=BenchmarkCreate(
                        date=datetime.date(),
                        name="EUA",
                        type="forward",
                        symbol="CK" + MONTH_NUMBERS_TO_CODES[expiry_date.month] + expiry_date.strftime("%y"),
                        expiry_date=expiry_date,
                        currency="EUR",
                        open=0,
                        high=0,
                        low=0,
                        close=settlement,
                        volume=0,
                        timestamp=datetime
                    )
                )
            except Exception as ex:
                print("[-] Error creating row - ", ex)
                error_client = error_reporting.Client(service="snap_eua_future_function", version=version)
                email_client.send_alert_email(alert.get_object())
                error_client.report_exception()          
    return data


def snap_eua():
    error_client = error_reporting.Client(service="snap_eua", version=version)

    try:
        datetime = dt.datetime.now()
        if config_type == "config.LocalConfig":
            datetime = datetime - dt.timedelta(days=1) # for local testing

        transport = paramiko.Transport((config.EUA_SERVER_HOST, config.EUA_SERVER_PORT))
        transport.connect(username=config.EUA_SERVER_USERNAME, password=config.EUA_SERVER_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        db = next(get_db())

        spot_filename = config.EUA_SPOT_TEMPLATE.format(datetime.strftime("%Y"), datetime.strftime("%Y%m%d"))
        future_filename = config.EUA_FUTURE_TEMPLATE.format(datetime.strftime("%Y"), datetime.strftime("%Y%m%d"))

        spot_data = spot(db=db, sftp=sftp, filename=spot_filename, datetime=datetime)
        print("[+] Spot data: ")
        pprint.pprint(spot_data)

        future_data = future(db=db, sftp=sftp, filename=future_filename, datetime=datetime)
        print("[+] Future data: ")
        pprint.pprint(future_data)
    except (SnapFileError,
            SpotDataError,
            IntegrityError,
            SQLAlchemyError,
            Exception) as ex:
        print("[-] Error snapping EUA - ", ex)
        email_client.send_alert_email(alert.get_object())
        error_client.report_exception()


if __name__ == "__main__":
    snap_eua()
