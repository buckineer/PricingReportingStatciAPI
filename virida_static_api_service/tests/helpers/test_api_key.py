import jwt
import pytest
from security import verify_api_key


def test_verify_api_key(authorization_header: dict):
    api_key = authorization_header["X-API-KEY"]
    assert verify_api_key(api_key)


def test_verify_expired_api_key(expired_api_key: str):
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_api_key(expired_api_key)


def test_verify_invalid_api_key():
    with pytest.raises(Exception):
        verify_api_key("invalid-key-example")
