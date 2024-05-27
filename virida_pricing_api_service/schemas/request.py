from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RequestType(str, Enum):
    USER_REQUEST: str = "user"
    ORGANIZATION_REQUEST: str = "organization"


class RequestCreate(BaseModel):
    request_type: RequestType
    model_name: str
    username: Optional[str] = None
    orgname: Optional[str] = None
    body: str
    response: str
    time: datetime
    projects_requested_count: int
    projects_priced_count: int


class Request(RequestCreate):
    class Config:
        orm_mode = True
