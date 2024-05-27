from typing import Optional
from pydantic import BaseModel
from enum import Enum


class AuthType(str, Enum):
    user: str = "user"
    organization: str = "organization"


class Auth(BaseModel):
    type: AuthType
    username: Optional[str] = None
    orgname: Optional[str] = None
    is_admin: bool