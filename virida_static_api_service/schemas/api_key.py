from enum import Enum

from pydantic import BaseModel, constr


class AuthType(str, Enum):
    ACCESS_TOKEN: str = 'token'
    API_KEY: str = 'api_key'


class AuthDetail(BaseModel):
    type: AuthType
    value: str
    decoded: dict


class BlockedAPIKeyCreate(BaseModel):
    api_key: constr(max_length=1024)


class BlockedAPIKey(BaseModel):
    id: int
    api_key: str

    class Config:
        orm_mode = True
