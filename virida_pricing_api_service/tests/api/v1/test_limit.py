import os
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient

from schemas.limit import LimitCreate, LimitUpdate, LimitType, LimitDelete
from conftest import reinit

from config import import_class
config = import_class(os.environ['APP_SETTINGS'])

ROUTE = f"{config.API_V1_BASE_ROUTE}/limit"


@reinit("limit")
def test_get_all_limits(client: TestClient, admin_auth_header: dict):
    response = client.get(ROUTE + "/all", headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)


def test_get_user_limit(client: TestClient, token_auth_header: dict, username: str):
    response = client.get(ROUTE + "/user/" + username, headers=token_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == username


def test_get_organization_limit(client: TestClient, admin_auth_header: dict, orgname: str):
    response = client.get(ROUTE + "/organization/" + orgname, headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["orgname"] == orgname


@reinit("limit")
def test_update_limit(client: TestClient, admin_auth_header: dict, username: str):
    data = LimitUpdate(
        limit_type=LimitType.USER_LIMIT,
        username=username,
        daily=1,
        monthly=1,
        lifetime=1,
        lifetime_reset_date=datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
    )
    response = client.patch(ROUTE + "/", data=data.json(), headers=admin_auth_header)
    response_body = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_body["daily"] == data.daily
    assert response_body["monthly"] == data.monthly
    assert response_body["lifetime"] == data.lifetime
    assert response_body["lifetime_reset_date"] == data.lifetime_reset_date.strftime("%Y-%m-%dT%H:%M:%S")


@reinit("limit")
def test_delete_limit(client: TestClient, admin_auth_header: dict, username: str):
    data = LimitDelete(
        limit_type=LimitType.USER_LIMIT,
        username=username
    )
    response = client.delete(ROUTE + "/", data=data.json(), headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK


def test_create_limit(client: TestClient, admin_auth_header: dict, user_limit: LimitCreate):
    data = LimitCreate(
        limit_type=LimitType.USER_LIMIT,
        username="test1",
        daily=user_limit.daily,
        monthly=user_limit.monthly,
        lifetime=user_limit.lifetime,
        lifetime_reset_date=user_limit.lifetime_reset_date
    )
    response = client.post(ROUTE + "/", data=data.json(), headers=admin_auth_header)
    response_body = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_body["username"] == data.username
    assert response_body["daily"] == data.daily
    assert response_body["monthly"] == data.monthly
    assert response_body["lifetime"] == data.lifetime
    assert response_body["lifetime_reset_date"] == data.lifetime_reset_date.strftime("%Y-%m-%dT%H:%M:%S")
