from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Request
from schemas.request import RequestCreate


def create(db: Session, request: RequestCreate):
    db_request = Request(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def delete_by_username(db: Session, username: str):
    db.query(Request).filter_by(username=username).delete()
    db.commit()


def delete_by_orgname(db: Session, orgname: str):
    db.query(Request).filter_by(orgname=orgname).delete()
    db.commit()


def get_number_of_user_projects_priced(db: Session, username: str, datetime: datetime):
    return (
        db
        .query(func.sum(Request.projects_priced_count))
        .filter(Request.username == username, Request.time >= datetime)
        .scalar() or 0
    )


def get_number_of_organization_projects_priced(db: Session, orgname: str, datetime: datetime):
    return (
        db
        .query(func.sum(Request.projects_priced_count))
        .filter(Request.orgname == orgname, Request.time >= datetime)
        .scalar() or 0
    )
