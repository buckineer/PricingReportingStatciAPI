import os
from typing import List

from starlette import status
from starlette.testclient import TestClient

from schemas.api_key import BlockedAPIKeyCreate
from tests.conftest import reinit

from config import import_class
config = import_class(os.environ['APP_SETTINGS'])

ROUTE = f"{config.API_V1_BASE_ROUTE}/api_keys/refresh_blacklist"


@reinit("apikey_blacklist")
def test_refresh_apikey_blacklist(client: TestClient,
                                  apikey_blacklist_one: List[BlockedAPIKeyCreate],
                                  apikey_blacklist_two: List[BlockedAPIKeyCreate],
                                  admin_auth_header: dict, token_auth_header: dict):
    apikey_blacklist_one_dict_list: List[dict] = [blocked_api_key.dict() for blocked_api_key in apikey_blacklist_one]
    response = client.post(ROUTE, json=apikey_blacklist_one_dict_list, headers=token_auth_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    apikey_blacklist_two_dict_list: List[dict] = [blocked_api_key.dict() for blocked_api_key in apikey_blacklist_two]
    response = client.post(ROUTE, json=apikey_blacklist_two_dict_list, headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(apikey_blacklist_two)

    response = client.post(ROUTE, json=apikey_blacklist_two_dict_list, headers=admin_auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(apikey_blacklist_two)
