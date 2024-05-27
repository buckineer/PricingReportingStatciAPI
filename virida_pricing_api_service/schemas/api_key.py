from enum import Enum
from typing import Tuple

from pydantic import BaseModel, constr


class APIKeyType(str, Enum):
    USER_KEY: str = "user"
    ORGANIZATION_KEY: str = "organization"


class AuthType(str, Enum):
    ACCESS_TOKEN: str = 'token'
    API_KEY: str = 'api_key'


class AuthDetail(BaseModel):
    type: AuthType
    value: str
    decoded: dict

    def get(self, key: str):
        """
        Get attribute value of the decoded payload dictionary
        """
        if key == "username":
            if self.type == AuthType.ACCESS_TOKEN:
                return self.decoded["username"]
            elif self.type == AuthType.API_KEY and self.decoded["key_type"] == APIKeyType.USER_KEY:
                return self.decoded["sub"]
            else:
                return None
        elif key == "orgname":
            if self.type == AuthType.API_KEY and self.decoded["key_type"] == APIKeyType.ORGANIZATION_KEY:
                return self.decoded["sub"]
            return None
        else:
            return self.decoded[key]


class BlockedAPIKeyCreate(BaseModel):
    api_key: constr(max_length=1024)


class BlockedAPIKey(BaseModel):
    id: int
    api_key: str

    class Config:
        orm_mode = True
