from datetime import datetime
from sqlalchemy.orm import Session
import crud


def get_user_daily_utilization(db: Session, username: str):
    return crud.request.get_number_of_user_projects_priced(
        db=db,
        username=username,
        datetime=datetime.today().replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
    )


def get_user_monthly_utilization(db: Session, username: str):
    return crud.request.get_number_of_user_projects_priced(
        db=db,
        username=username,
        datetime=datetime.today().replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
    )


def get_user_lifetime_utilization(db: Session, username: str, reset_date: datetime):
    return crud.request.get_number_of_user_projects_priced(
        db=db,
        username=username,
        datetime=reset_date
    )


def get_organization_daily_utilization(db: Session, orgname: str):
    return crud.request.get_number_of_organization_projects_priced(
        db=db,
        orgname=orgname,
        datetime=datetime.today().replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
    )


def get_organization_monthly_utilization(db: Session, orgname: str):
    return crud.request.get_number_of_organization_projects_priced(
        db=db,
        orgname=orgname,
        datetime=datetime.today().replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
    )


def get_organization_lifetime_utilization(db: Session, orgname: str, reset_date: datetime):
    return crud.request.get_number_of_organization_projects_priced(
        db=db,
        orgname=orgname,
        datetime=reset_date
    )
