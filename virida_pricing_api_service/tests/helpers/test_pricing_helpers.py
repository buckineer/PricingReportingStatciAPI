from typing import List
from aiohttp import ClientSession
from fastapi import status
from pydantic import parse_obj_as
import pytest

from helpers.pricing import get_mappings
from schemas.project import ProjectPricing
from schemas.api_key import AuthDetail, AuthType


@pytest.mark.asyncio
async def test_get_mappings_for_valid_pricings(aiohttp_session: ClientSession, api_key: str, valid_project_pricings: List[dict]):
    auth_detail_object: AuthDetail = AuthDetail(
        type=AuthType.API_KEY,
        value=api_key,
        decoded={}
    )

    parsed_pricings: List[ProjectPricing] = parse_obj_as(List[ProjectPricing], valid_project_pricings)
    status_code, response_data = await get_mappings(
        aiohttp_session=aiohttp_session,
        auth_detail=auth_detail_object,
        project_pricings=parsed_pricings
    )
    assert status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_mappings_for_invalid_pricings(aiohttp_session: ClientSession, api_key: str, invalid_project_pricings: List[dict]):
    auth_detail_object: AuthDetail = AuthDetail(
        type=AuthType.API_KEY,
        value=api_key,
        decoded={}
    )

    parsed_pricings: List[ProjectPricing] = parse_obj_as(List[ProjectPricing], invalid_project_pricings)
    status_code, response_data = await get_mappings(
        aiohttp_session=aiohttp_session,
        auth_detail=auth_detail_object,
        project_pricings=parsed_pricings
    )
    assert status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_mappings_for_valid_and_invalid_pricings(aiohttp_session: ClientSession, api_key: str, valid_and_invalid_project_pricings: List[dict]):
    auth_detail_object: AuthDetail = AuthDetail(
        type="api_key",
        value=api_key,
        decoded={}
    )

    parsed_pricings: List[ProjectPricing] = parse_obj_as(List[ProjectPricing], valid_and_invalid_project_pricings)
    status_code, response_data = await get_mappings(
        aiohttp_session=aiohttp_session,
        auth_detail=auth_detail_object,
        project_pricings=parsed_pricings
    )
    assert status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
