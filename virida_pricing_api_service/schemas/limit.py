from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, constr


class LimitType(str, Enum):
    USER_LIMIT: str = "user"
    ORGANIZATION_LIMIT: str = "organization"


class LimitBase(BaseModel):
    daily: int
    monthly: int
    lifetime: int
    lifetime_reset_date: datetime


class LimitObject(BaseModel):
    limit_type: LimitType
    username: Optional[constr(max_length=50)] = None
    orgname: Optional[constr(max_length=256)] = None


class LimitCreate(LimitObject, LimitBase):
    pass


class LimitDelete(LimitObject):
    pass


class Limit(LimitCreate):
    class Config:
        orm_mode = True


class UserLimit(LimitBase):
    username: constr(max_length=50)

    class Config:
        orm_mode = True


class OrganizationLimit(LimitBase):
    orgname: constr(max_length=256)

    class Config:
        orm_mode = True


class LimitAll(BaseModel):
    user: List[UserLimit]
    organization: List[OrganizationLimit]

    class Config:
        orm_mode = True


class LimitUpdate(LimitObject):
    daily: Optional[int] = None
    monthly: Optional[int] = None
    lifetime: Optional[int] = None
    lifetime_reset_date: Optional[datetime] = None


class StatusAndDescription(BaseModel):
    status: str
    description: str
