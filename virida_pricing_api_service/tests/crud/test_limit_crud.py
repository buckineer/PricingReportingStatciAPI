from datetime import datetime
from sqlalchemy.orm import Session

from schemas.limit import LimitCreate, LimitUpdate, LimitType
from conftest import reinit
from utils_for_testing import random_string
import crud


@reinit("limit")
def test_read_user_limit(db: Session, user_limit: LimitCreate):
    limit_db = crud.limit.read_by_username(db=db, username=user_limit.username)
    assert limit_db
    assert limit_db.username == user_limit.username


@reinit("limit")
def test_read_organization_limit(db: Session, organization_limit: LimitCreate):
    limit_db = crud.limit.read_by_orgname(db=db, orgname=organization_limit.orgname)
    assert limit_db
    assert limit_db.orgname == organization_limit.orgname


def test_read_all_limit(db: Session):
    limits = crud.limit.read_all(db=db)
    assert limits
    assert isinstance(limits, list)


def test_create_limit(db: Session, user_limit: LimitCreate):
    user_limit.username = random_string()
    limit_db = crud.limit.create(db=db, limit=user_limit)
    assert limit_db
    assert limit_db.username == user_limit.username
    assert limit_db.daily == user_limit.daily
    assert limit_db.monthly == user_limit.monthly
    assert limit_db.lifetime == user_limit.lifetime
    assert limit_db.lifetime_reset_date == user_limit.lifetime_reset_date


@reinit("limit")
def test_update_limit(db: Session, username: str):
    limit = LimitUpdate(
        limit_type=LimitType.USER_LIMIT,
        username=username,
        daily=1,
        monthly=1,
        lifetime=1,
        lifetime_reset_date=datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    )
    limit_db = crud.limit.update(db=db, limit=limit)
    assert limit_db
    assert limit_db.username == username
    assert limit_db.daily == limit.daily
    assert limit_db.monthly == limit.monthly
    assert limit_db.lifetime == limit.lifetime
    assert limit_db.lifetime_reset_date == limit.lifetime_reset_date


@reinit("limit")
def test_delete_limit(db: Session, username: str):
    crud.limit.delete_by_username(db=db, username=username)
    assert crud.limit.read_by_username(db=db, username=username) is None
