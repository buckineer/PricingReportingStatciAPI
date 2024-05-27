from typing import List

from fastapi import status
from fastapi.testclient import TestClient

from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])

ATTRIBUTES_ROUTE = config.API_V1_BASE_ROUTE + "/attributes"


def test_get_attributes(client: TestClient, attribute_name: str, authorization_header: dict):
    response = client.get(f"{ATTRIBUTES_ROUTE}/{attribute_name}", headers=authorization_header)
    response_body = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_body is not None


def test_attribute_not_found(client: TestClient, random_string: str, authorization_header: dict):
    response = client.get(f"{ATTRIBUTES_ROUTE}/{random_string}", headers=authorization_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_validate_projects(client: TestClient, valid_project_validations: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in valid_project_validations]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/validate", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(valid_project_validations)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == valid_project_validations[index]["project"]
        assert validated["status"] == valid_project_validations[index]["status"]
        assert validated["description"] == valid_project_validations[index]["description"]


def test_validate_invalid_projects(client: TestClient, invalid_project_validations: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in invalid_project_validations]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/validate", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()) == len(invalid_project_validations)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == invalid_project_validations[index]["project"]
        assert validated["status"] == invalid_project_validations[index]["status"]
        assert validated["description"] == invalid_project_validations[index]["description"]


def test_validate_valid_and_invalid_projects(client: TestClient, valid_and_invalid_project_validations: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in valid_and_invalid_project_validations]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/validate", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()) == len(valid_and_invalid_project_validations)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == valid_and_invalid_project_validations[index]["project"]
        assert validated["status"] == valid_and_invalid_project_validations[index]["status"]
        assert validated["description"] == valid_and_invalid_project_validations[index]["description"]


def test_map_valid_project(client: TestClient, valid_project_mappings: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in valid_project_mappings]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/map", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(valid_project_mappings)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == valid_project_mappings[index]["project"]
        assert validated["status"] == valid_project_mappings[index]["status"]
        # assert validated["description"] == valid_project_mappings[index]["description"]


def test_map_invalid_project(client: TestClient, invalid_project_mappings: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in invalid_project_mappings]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/map", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()) == len(invalid_project_mappings)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == invalid_project_mappings[index]["project"]
        assert validated["status"] == invalid_project_mappings[index]["status"]
        assert validated["description"] == invalid_project_mappings[index]["description"]
        # assert validated["mapping"] == invalid_project_mappings[index]["mapping"]


def test_map_valid_and_invalid_project(client: TestClient, valid_and_invalid_project_mappings: List[dict], authorization_header: dict):
    projects: List[dict] = [validation["project"] for validation in valid_and_invalid_project_mappings]
    response = client.post(f"{config.API_V1_BASE_ROUTE}/projects/map", json=projects, headers=authorization_header)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response.json()) == len(valid_and_invalid_project_mappings)
    for index, validated in enumerate(response.json()):
        assert validated["project"] == valid_and_invalid_project_mappings[index]["project"]
        assert validated["status"] == valid_and_invalid_project_mappings[index]["status"]
        assert validated["description"] == valid_and_invalid_project_mappings[index]["description"]
        # assert validated["mapping"] == valid_and_invalid_project_mappings[index]["mapping"]
