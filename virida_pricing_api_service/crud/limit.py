from typing import List

from sqlalchemy.orm import Session

from models import Limit
from schemas.limit import LimitCreate, LimitUpdate, LimitType, OrganizationLimit, UserLimit


def read_by_username(db: Session, username: str):
    return db.query(Limit).filter_by(username=username).first()


def read_by_orgname(db: Session, orgname: str):
    return db.query(Limit).filter_by(orgname=orgname).first()


def read_all(db: Session):
    return db.query(Limit).all()


def read_all_user_limit(db: Session) -> List[UserLimit]:
    return db.query(Limit).filter_by(limit_type=LimitType.USER_LIMIT).all()


def read_all_organization_limit(db: Session) -> List[OrganizationLimit]:
    return db.query(Limit).filter_by(limit_type=LimitType.ORGANIZATION_LIMIT).all()


def create(db: Session, limit: LimitCreate):
    db_limit = Limit(**limit.dict())
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    return db_limit


def update(db: Session, limit: LimitUpdate):
    if limit.limit_type == LimitType.USER_LIMIT:
        db_limit: Limit = db.query(Limit).filter_by(username=limit.username).first()
    elif limit.limit_type == LimitType.ORGANIZATION_LIMIT:
        db_limit: Limit = db.query(Limit).filter_by(orgname=limit.orgname).first()
    else:
        return None

    if db_limit is None:
        return None

    for key, value in limit.dict(exclude_unset=True).items():
        setattr(db_limit, key, value)
    db.commit()

    return db_limit


def delete_by_username(db: Session, username: str):
    db.query(Limit).filter_by(username=username).delete()
    db.commit()


def delete_by_orgname(db: Session, orgname: str):
    db.query(Limit).filter_by(orgname=orgname).delete()
    db.commit()
