import os
from typing import List
import asyncio
import aiohttp
import re
from pathlib import Path
import datetime as dt
import calendar
import sys

from fastapi import status
import pandas as pd

from schemas.report import Report
from schemas.email import ReportsEmailTemplate
from database import DatabaseContextManager
import httpclient
from config import config
import crud
import email_client

ERROR_MESSAGE = "[-] For the report named '{}', the Pricing Service responded with status {}, and body {}"
BASE_URL = f"{config.PRICING_URL}"
ENV = os.environ["APP_SETTINGS"].replace("config.", "").replace("Config", "").lower()
DATE_TIME = dt.datetime.now()

INDEX_NAMES = {
    "1": "Household Devices CARBEX",
    "2": "Soil CARBEX",
    "3": "Eco Create CARBEX",
    "4": "Eco Create CARBEX Biodiverse",
    "5": "Eco Protect CARBEX",
    "6": "Eco Protect CARBEX Social"
}

class PricingException(Exception):
    pass


def get_current_time():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(message):
    print(f"[+] {get_current_time()} {message}")


def error(*messages):
    print(f"[-] {get_current_time()} {messages}")


def create_directory(directory: str):
    log(f"Creating {directory} directory if it doesn't exist...")
    Path(directory).mkdir(parents=True, exist_ok=True)


def reports() -> List[Report]:
    log("Fetching reports from the database...")
    with DatabaseContextManager() as db:
        return crud.report.read_reports_scheduled_for_today(db=db)


async def get_pricings(report: Report) -> List[dict]:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.HTTP_CLIENT_TIMEOUT_SECONDS)) as aiohttp_session:
        log(f"Getting pricings for report: '{report.name}'...")
        try:
            status_code, response = await httpclient.post(
                session=aiohttp_session,
                url=f"{BASE_URL}{report.model_endpoint}",
                json=report.definition,
                headers = {"X-API-KEY": config.API_KEY} 
            )

            if status_code != status.HTTP_200_OK:
                raise PricingException(ERROR_MESSAGE.format(report.name, status_code, response))
            
            return response
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError, aiohttp.ClientPayloadError, Exception) as exception:
            raise PricingException("[-] Exception occured while pricing the report definition: ", exception)


def format_filename(filename: str):
    log(f"Checking filename '{filename}' for datetime placeholders...")

    pattern = "%[A-Za-z]"
    match = re.search(pattern, filename)
    while match is not None:
        filename = re.sub(pattern, DATE_TIME.strftime(match.group()), filename, 1)
        match = re.search(pattern, filename)
    return filename


def is_historical_pricing_report(report: Report):
    if not report:
        return False
    return type(report.definition) == dict


def is_platts_report(report: Report):
    if not report:
        return False
    return "index" in report.definition["scenarios"][0]["project"]


def generate_csv(report: Report, pricings: List[dict]):
    log(f"Generating CSV with filename '{report.filename}' in folder '{report.folder}'...")

    filename = format_filename(report.filename)
    filepath = f"{config.REPORTS_DIRECTORY}/{report.folder}/{filename}"

    create_directory(f"{config.REPORTS_DIRECTORY}/{report.folder}")

    data = []
    for pricing in pricings:
        project: dict = pricing["project"]

        if is_historical_pricing_report(report):
            if is_platts_report(report):
                data.append({
                    "date": pricing["history"][0]["date"],
                    "index": project["index"],
                    "name": INDEX_NAMES[project["index"]],
                    "price": round(pricing["history"][0]["price"], 2)
                })
            else:
                data.append({
                    "standard": project["standard"][0],
                    "project_class": project["project"][0],
                    "country": project["country"][0] if project["country"] else None,
                    "region": project["region"][0] if project["region"] else None,
                    "subregion": project["subregion"][0] if project["subregion"] else None,
                    "sdg": project["sdg"][0],
                    "vintage": project["vintage"],
                    "horizon": pricing["horizon"],
                    "price": pricing["history"][0]["price"]
                })
        else:
            data.append({
                "standard": project["standard"][0],
                "project_class": project["project"][0],
                "country": project["country"][0] if project["country"] else None,
                "region": project["region"][0] if project["region"] else None,
                "subregion": project["subregion"][0] if project["subregion"] else None,
                "sdg": project["sdg"][0],
                "vintage": project["vintage"],
                "horizon": pricing["horizon"],
                "bid": pricing["bid"],
                "ask": pricing["ask"]
            })

    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, header=True)
    log(f"CSV with filename '{filename}' generated successfully...")


def html(errors: list) -> str:
    head = """
    <table border="1" style="border-collapse: collapse; font-family: Helvetica; width: 100%;">
        <tr>
            <th>Report</th>
            <th>Owner</th>
            <th>Endpoint</th>
            <th>Completed</th>
        </tr>
    """

    body = ""
    for report in reports():
        body = body + f"""
        <tr>
            <td>{format_filename(report.filename)}</td>
            <td>{report.owner}</td>
            <td>{report.model_endpoint}</td>
            <td>{report.id not in [error["report_id"] for error in errors]}</td>
        </tr>
        """
    
    footer = """</table>"""
    return head + body + footer


def formatted_exception() -> tuple:
    err_info: tuple = sys.exc_info()
    err_module: str = err_info[0].__module__
    err_name: str = err_info[0].__name__
    err_type: str = err_name if err_module == "__main__" else f"{err_module}.{err_name}"
    err_file = os.path.split(err_info[2].tb_frame.f_code.co_filename)[1]
    err_message: str = str(sys.exc_info()[1])
    return (err_type, err_message, err_file)


def send_email(errors: list):
    status = "Failed" if errors else "Completed"
    subject=f"Daily Report Generation Script {dt.date.today()} - {status} [{ENV}]"
    date = dt.date.today()
    day = list(calendar.day_name)[date.weekday()]

    email_client.send_email(ReportsEmailTemplate(
        date=str(dt.date.today()),
        subject=str(subject),
        day=day,
        reports_html=html(errors),
        errors=str(errors)
    ))


async def main():
    log("Script started...")
    create_directory(config.REPORTS_DIRECTORY)

    errors = []
    for report in reports():
        try:
            pricings = await get_pricings(report)
            generate_csv(report=report, pricings=pricings)
        except Exception as exception:
            errors.append({"report_id": report.id, "exception": formatted_exception()})
            error(exception)
    
    send_email(errors)
    log("Script ended...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
