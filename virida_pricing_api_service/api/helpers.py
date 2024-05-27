from typing import Optional, List, Union

from fastapi import Depends, Security, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jwt import ExpiredSignatureError

import crud.api_key
import security
from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    get_error_string_by_error_code, USERNAME_REQUIRED, ORGANIZATION_REQUIRED
from database import DatabaseContextManager
from schemas.api_key import AuthType, AuthDetail
from config import import_class
import os

from schemas.limit import LimitDelete, LimitType

config = import_class(os.environ['APP_SETTINGS'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=config.AUTH_LOGIN_URL, auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


def authenticate(token=Depends(oauth2_scheme), api_key=Security(api_key_scheme)) -> AuthDetail:
    if (token):
        try:
            decoded_payload = security.verify_token(token)
            return AuthDetail(
                type=AuthType.ACCESS_TOKEN,
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
                type=AuthType.API_KEY,
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
    """
    Class for creating callable objects that accept custom arguments for handling the authorization
    """
    def __init__(
        self,
        permissions: Union[List[str], str] = [],
        allowed_params: Optional[Union[List[str], str]] = None,
        raise_exception: bool = True
    ) -> None:
        """
        Create Authorize callable object

        :param permissions: The list of endpoint permissions
        :param allowed_params: The path parameters to allow authorization for in case they have
        the same value as the ones in AuthDetail (token or api_key)
        :param raise_exception: The boolean indicating whether to raise a 403 HTTPException when authorization fails
        """
        if permissions and type(permissions) is not list:
            permissions = [permissions]
        if allowed_params and type(allowed_params) is not list:
            allowed_params = [allowed_params]
        self.permissions = permissions
        self.allowed_params = allowed_params
        self.raise_exception = raise_exception

    def __call__(
        self,
        request: Request,
        auth_detail: AuthDetail = Depends(authenticate),
    ) -> AuthDetail:
        if not set(self.permissions).issubset(auth_detail.get("permissions")):
            if not self.allowed_params:
                if not self.raise_exception:
                    return None
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Access forbidden")
            
            for param_name in self.allowed_params:
                if auth_detail.get(param_name) != request.path_params[param_name]:
                    if not self.raise_exception:
                        return None
                    raise HTTPException(status.HTTP_403_FORBIDDEN, "Access forbidden")
        return auth_detail


# TODO: Move this to either Authorize class or to a Pydantic validator
def authorize_limit_object(limit_type: LimitType, username: str, orgname: str):
    if limit_type == LimitType.USER_LIMIT and username is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, {
            API_RESPONSE_ERROR_CODE_STRING: USERNAME_REQUIRED,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USERNAME_REQUIRED)
        })
    if limit_type == LimitType.ORGANIZATION_LIMIT and orgname is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, {
            API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_REQUIRED,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_REQUIRED)
        })


# TODO: Move this to either Authorize class or to a Pydantic validator
def authorize_limit_delete(limit_delete: LimitDelete):
    """
    :param limit_delete:
    :return:
    """
    authorize_limit_object(limit_delete.limit_type, limit_delete.username, limit_delete.orgname)
