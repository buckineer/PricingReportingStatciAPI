from fastapi import Depends, Security, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jwt import ExpiredSignatureError

import security
from schemas.auth import Auth, AuthType
from config import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=config.AUTH_LOGIN_URL, auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)

def authenticate(token=Depends(oauth2_scheme), api_key = Security(api_key_scheme)) -> Auth:
    if (token):
        try:
            decoded_payload = security.verify_token(token)
            return Auth(
                type=AuthType.user,
                username=decoded_payload["username"],
                orgname=decoded_payload["orgname"],
                is_admin=decoded_payload["is_admin"]
            )
        except ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    elif (api_key):
        try:
            decoded_payload = security.verify_api_key(api_key)
            type: AuthType = decoded_payload["key_type"]
            if type == AuthType.user:
                return Auth(
                    type=type,
                    username=decoded_payload["sub"],
                    is_admin=decoded_payload["permissions"]["is_admin"]
                )
            else:
                return Auth(
                    type=type,
                    orgname=decoded_payload["sub"],
                    is_admin=decoded_payload["permissions"]["is_admin"]
                )
        except ExpiredSignatureError:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "API key expired")
        except Exception:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "API key is invalid")
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

def authorize_is_admin(auth: Auth=Depends(authenticate)):
    if not auth.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access is forbidden")