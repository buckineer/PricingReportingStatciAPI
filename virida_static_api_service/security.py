import jwt
from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])

JWT_ALGORITHM = "RS256"


def verify_api_key(api_key: str) -> dict:
    """ Verifies whether the token is valid.

    :returns: Dictionary of the decoded token
    :raises: jwt.ExpiredSignatureError
    :raises: Exception
    """
    try:
        return jwt.decode(api_key, config.API_KEY_PUBLIC_KEY, algorithms=JWT_ALGORITHM)
    except jwt.ExpiredSignatureError as expired_exception:
        raise expired_exception
    except Exception as exception:
        raise exception


def verify_token(token: str) -> dict:
    """ Verifies whether the token is valid.

    :returns: Dictionary of the decoded token
    :raises: jwt.ExpiredSignatureError
    :raises: Exception
    """
    try:
        return jwt.decode(token, config.TOKEN_PUBLIC_KEY, algorithms=JWT_ALGORITHM)
    except jwt.ExpiredSignatureError as expired_exception:
        raise expired_exception
    except Exception as exception:
        raise exception
