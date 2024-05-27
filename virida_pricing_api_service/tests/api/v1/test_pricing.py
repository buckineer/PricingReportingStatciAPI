from typing import List
from fastapi import status
from fastapi.testclient import TestClient

from conftest import reinit
from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])

PRICING_ROUTE = f"{config.API_V1_BASE_ROUTE}/valuation"


@reinit("limit")
def test_calculate_valid_pricing(client: TestClient, valid_project_pricings: List[dict], authorization_header: dict):
    project_pricings: List[dict] = [{"project": pricing["project"], "horizon": pricing["horizon"]} for pricing in valid_project_pricings]
    response = client.post(f"{PRICING_ROUTE}/model_v7", json=project_pricings, headers=authorization_header)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(project_pricings)
    for index, pricing in enumerate(response.json()):
        assert pricing["project"] == valid_project_pricings[index]["project"]
        assert pricing["horizon"] == valid_project_pricings[index]["horizon"]
        assert pricing["status"] == valid_project_pricings[index]["status"]
        assert pricing["description"] == valid_project_pricings[index]["description"]
        # assert pricing["formula"] == valid_project_pricings[index]["formula"]
        # assert pricing["sigma"] == valid_project_pricings[index]["sigma"]
        # assert pricing["beta"] == valid_project_pricings[index]["beta"]
        # assert pricing["mid"] == valid_project_pricings[index]["mid"]
        assert pricing["bid"] == valid_project_pricings[index]["bid"]
        assert pricing["ask"] == valid_project_pricings[index]["ask"]
        # assert pricing["vintage_discount_factor"] == valid_project_pricings[index]["vintage_discount_factor"]
        # assert pricing["eua"] == valid_project_pricings[index]["eua"]
        # assert pricing["model_id"] == valid_project_pricings[index]["model_id"]


@reinit("limit")
def test_calculate_invalid_pricing(client: TestClient, invalid_project_pricings: List[dict], authorization_header: dict):
    project_pricings: List[dict] = [{"project": pricing["project"], "horizon": pricing["horizon"]} for pricing in invalid_project_pricings]
    response = client.post(f"{PRICING_ROUTE}/model_v7", json=project_pricings, headers=authorization_header)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()) == len(project_pricings)
    for index, pricing in enumerate(response.json()):
        assert pricing["project"] == invalid_project_pricings[index]["project"]
        # assert pricing["horizon"] == invalid_project_pricings[index]["horizon"]
        assert pricing["status"] == invalid_project_pricings[index]["status"]
        assert pricing["description"] == invalid_project_pricings[index]["description"]
        # assert pricing["formula"] == invalid_project_pricings[index]["formula"]
        # assert pricing["sigma"] == invalid_project_pricings[index]["sigma"]
        # assert pricing["beta"] == invalid_project_pricings[index]["beta"]
        # assert pricing["mid"] == invalid_project_pricings[index]["mid"]
        # assert pricing["bid"] == invalid_project_pricings[index]["bid"]
        # assert pricing["ask"] == invalid_project_pricings[index]["ask"]
        # assert pricing["vintage_discount_factor"] == invalid_project_pricings[index]["vintage_discount_factor"]
        # assert pricing["model_id"] == invalid_project_pricings[index]["model_id"]


@reinit("limit")
def test_calculate_valid_and_invalid_pricing(client: TestClient, valid_and_invalid_project_pricings: List[dict], authorization_header: dict):
    project_pricings: List[dict] = [{"project": pricing["project"], "horizon": pricing["horizon"]} for pricing in valid_and_invalid_project_pricings]
    response = client.post(f"{PRICING_ROUTE}/model_v7", json=project_pricings, headers=authorization_header)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(project_pricings)
    for index, pricing in enumerate(response.json()):
        assert pricing["project"] == valid_and_invalid_project_pricings[index]["project"]
        assert pricing["horizon"] == valid_and_invalid_project_pricings[index]["horizon"]
        assert pricing["status"] == valid_and_invalid_project_pricings[index]["status"]
        assert pricing["description"] == valid_and_invalid_project_pricings[index]["description"]
        # assert pricing["formula"] == valid_and_invalid_project_pricings[index]["formula"]
        # assert pricing["sigma"] == valid_and_invalid_project_pricings[index]["sigma"]
        # assert pricing["beta"] == valid_and_invalid_project_pricings[index]["beta"]
        # assert pricing["mid"] == valid_and_invalid_project_pricings[index]["mid"]
        assert pricing["bid"] == valid_and_invalid_project_pricings[index]["bid"]
        assert pricing["ask"] == valid_and_invalid_project_pricings[index]["ask"]
        # assert pricing["vintage_discount_factor"] == valid_and_invalid_project_pricings[index]["vintage_discount_factor"]
        # assert pricing["model_id"] == valid_and_invalid_project_pricings[index]["model_id"]


@reinit("limit")
def test_calculate_limit_expired_pricing(client: TestClient, valid_project_pricings: List[dict], authorization_header: dict):
    project_pricings: List[dict] = [{"project": pricing["project"], "horizon": pricing["horizon"]} for pricing in valid_project_pricings + valid_project_pricings]
    response = client.post(f"{PRICING_ROUTE}/model_v5", json=project_pricings, headers=authorization_header)
    assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
