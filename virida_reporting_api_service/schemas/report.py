from typing import Optional, List, Union
from enum import IntEnum
from datetime import datetime
from pydantic import BaseModel, Field, validator
from pathvalidate import validate_filename

from schemas.auth import AuthType


fields: dict = {
    "folder": {
        "description": "e.g. john/july-reports",
        "regex": "^([A-Za-z0-9]+-*\/*[A-Za-z0-9]+-*)+$"
    },
    "week_days": {
        "description": "e.g. [1, 2, 3] for Monday, Tuesday, and Thursday respectively",
        "max_items": 7 
    }
}


class WeekDay(IntEnum):
    monday = 1
    tuesday = 2
    wedensday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7


class ReportBase(BaseModel):
    name: str
    filename: str
    folder: str = Field(**fields["folder"])
    owner: str
    owner_type: AuthType

    # SwaggerUI does not support anyOf or oneOf examples:https://github.com/swagger-api/swagger-ui/issues/3803
    definition: Union[List[dict], dict]

    model_endpoint: str
    week_days: List[WeekDay] = Field(**fields["week_days"])
    expiry_date: datetime
    is_active: bool

    @validator('filename')
    def validate_standard(cls, value, values):
        validate_filename(value)
        return value

class ReportCreate(ReportBase):
    pass


class ReportUpdate(ReportBase):
    name: Optional[str] = None
    filename: Optional[str] = None
    folder: Optional[str] = Field(None, **fields["folder"])
    owner: Optional[str] = None
    owner_type: AuthType = None
    definition: Optional[List[dict]] = None
    model_endpoint: Optional[str] = None
    week_days: Optional[List[WeekDay]] = Field(None, **fields["week_days"])
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class Report(ReportBase):
    id: int

    class Config:
        orm_mode = True