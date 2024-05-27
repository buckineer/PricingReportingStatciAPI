import os
from fastapi import status
from fastapi.testclient import TestClient
from conftest import reinit

from config import import_class
config = import_class(os.environ['APP_SETTINGS'])

ROUTE = f"{config.API_V1_BASE_ROUTE}/utilization"


@reinit("limit")
def test_get_all_utilization(client: TestClient, admin_auth_header: dict):
    response = client.get(ROUTE + "/all", headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), dict)


@reinit("limit")
def test_get_user_utilization(client: TestClient, token_auth_header: dict, username: str):
    response = client.get(ROUTE + "/user/" + username, headers=token_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == username


@reinit("limit")
def test_get_organization_utilization(client: TestClient, admin_auth_header: dict, orgname: str):
    response = client.get(ROUTE + "/organization/" + orgname, headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["orgname"] == orgname
