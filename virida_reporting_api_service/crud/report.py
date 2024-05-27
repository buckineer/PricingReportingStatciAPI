from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from models import Report
from schemas.report import ReportBase, ReportCreate, ReportUpdate
from schemas.auth import AuthType

import copy
import json

def _report_deserializer(func):
    """Decorator that makes possible serializing and deserializing the Report fields
    that have different representation in the database from the standard
    representation defined in pydantic schema

    On start, this function automatically checks whether Report serialization is necessary
    and then it deserializes the DB result to make it parsable in pydantic schema

    :param func: The function to be decorated
    """

    def inner(*args, **kwargs):
        def serialize():
            report: ReportBase = kwargs["report"]
            if report.week_days != None:
                report.week_days = ",".join(str(day.value) for day in report.week_days)
            if report.definition != None:
                report.definition = json.dumps(report.definition)
            kwargs["report"] = report

        def parse(report: Report):
            if report == None:
                return report
            
            if report.week_days != None:
                report.week_days = [int(day) for day in report.week_days.split(",") if day.isnumeric()]
            if report.definition != None:
                report.definition = json.loads(report.definition)

            report_copy = copy.copy(report)

            if "db" in kwargs:
                # Clear any changes to the sqlalchemy report object made while parsing
                # so that they don't get saved with the other changes to the database
                kwargs["db"].refresh(report) 

            return report_copy

        def wrapper():
            is_serialization_necessary = "report" in kwargs and isinstance(kwargs["report"], ReportBase)
            if is_serialization_necessary:
                serialize()
            
            db_result = func(*args, **kwargs)
            if isinstance(db_result, list):
                return [parse(report) for report in db_result]
            else:
                return parse(db_result)
        return wrapper()
    return inner


@_report_deserializer
def read(db: Session, id: int):
    return db.query(Report).filter_by(id=id).first()

@_report_deserializer
def read_by_owner(db: Session, owner: str, owner_type: AuthType):
    return db.query(Report).filter_by(owner=owner, owner_type=owner_type).all()

@_report_deserializer
def read_reports_scheduled_for_today(db: Session):
    week_day: int = datetime.now().weekday() + 1
    return (
        db
        .query(Report)
        .filter(Report.week_days.contains(str(week_day)))
        .filter(Report.expiry_date > datetime.now())
        .filter(Report.is_active == True)
        .all()
    )

@_report_deserializer
def read_all(db: Session):
    return db.query(Report).all()

@_report_deserializer
def create(db: Session, report: ReportCreate):
    db_report = Report(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@_report_deserializer
def update(db: Session, id: int, report: ReportUpdate):
    db_report = db.query(Report).filter_by(id=id).first()
    for key, value in report.dict(exclude_unset=True).items(): setattr(db_report, key, value)
    db.commit()
    return db_report

@_report_deserializer
def deactivate(db: Session, id: int):
    report = db.query(Report).filter_by(id=id).first()
    report.is_active = False
    db.commit()
    return report

def delete(db: Session, id: int):
    db.query(Report).filter_by(id=id).delete()
    db.commit()