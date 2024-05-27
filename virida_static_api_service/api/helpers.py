from typing import Optional, List

from fastapi import Depends, Security, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jwt import ExpiredSignatureError

import crud
import security
from config import import_class
import os

from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, LIMITED_ACCESS, \
    get_error_string_by_error_code
from database import DatabaseContextManager
from schemas.api_key import AuthDetail, AuthType

config = import_class(os.environ['APP_SETTINGS'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=config.AUTH_LOGIN_URL, auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


def authenticate(token=Depends(oauth2_scheme), api_key=Security(api_key_scheme)) -> AuthDetail:
    if (token):
        try:
            decoded_payload = security.verify_token(token)

            return AuthDetail(
                type="token",
                value=token,
                decoded=decoded_payload
            )
        except ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    elif (api_key):
        try:
            decoded_payload = security.verify_api_key(api_key)

            with DatabaseContextManager() as db:
                if crud.api_key.is_apikey_blocked(db=db, api_key=api_key):
                    raise HTTPException(status.HTTP_403_FORBIDDEN, "API key is blocked")

            return AuthDetail(
                type="api_key",
                value=api_key,
                decoded=decoded_payload
            )
        except ExpiredSignatureError:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "API key expired")
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "API key is invalid")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")


class Authorize:
    def __init__(self, permissions: Optional[List[str]]=None):
        self.permissions = permissions

    def __call__(self, auth_detail: AuthDetail=Depends(authenticate)):
        if not set(self.permissions).issubset(auth_detail.decoded["permissions"]):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Access frobidden")


def is_admin(auth_detail: AuthDetail) -> bool:
    """
    check if the token or API key is for admin
    :param auth_detail: token or API key
    :return: true if the token or API key is for admin, otherwise False
    """
    # if the API key is given
    if auth_detail.type == AuthType.API_KEY and auth_detail.decoded["permissions"]["is_admin"]:
        return True

    # is the token is given
    if auth_detail.type == AuthType.ACCESS_TOKEN and auth_detail.decoded["is_admin"]:
        return True

    return False
