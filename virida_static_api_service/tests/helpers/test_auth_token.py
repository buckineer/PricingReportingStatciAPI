import jwt
import pytest
from security import verify_token


def test_verify_auth_token(auth_token: dict):
    assert verify_token(auth_token)


def test_verify_expired_auth_token(expired_auth_token: str):
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(expired_auth_token)


def test_verify_invalid_auth_token():
    with pytest.raises(Exception):
        verify_token("invalid-token-example")
