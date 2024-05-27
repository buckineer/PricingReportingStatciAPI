from typing import Any, Optional, List, Type, Sequence, Callable
from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute
from starlette.types import ASGIApp
from starlette.responses import Response
from sqlalchemy.orm import Session
from aiohttp import ClientSession
from pydantic import parse_obj_as

import crud
from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    USER_SUBSCRIPTION_NOT_EXIST, get_error_string_by_error_code, ORGANIZATION_SUBSCRIPTION_NOT_EXIST, \
    ORGANIZATION_DAILY_LIMIT_EXCEED, USER_DAILY_LIMIT_EXCEED, get_limit_exceed_error_string, USER_MONTHLY_LIMIT_EXCEED, \
    ORGANIZATION_MONTHLY_LIMIT_EXCEED, ORGANIZATION_LIFETIME_LIMIT_EXCEED, USER_LIFETIME_LIMIT_EXCEED

from schemas.project import ProjectPricing, ProjectMapping
from schemas.api_key import APIKeyType, AuthDetail, AuthType
from schemas.request import RequestCreate, RequestType
from schemas.permission import Permission
from helpers.pricing import validate, calculate, get_mappings
from database import get_db
from httpclient import aiohttp_session
from api.helpers import Authorize
from helpers.database import get_user_daily_utilization, get_user_monthly_utilization, \
    get_user_lifetime_utilization

from config import import_class

config = import_class(os.environ['APP_SETTINGS'])


class PricingRouter(APIRouter):
    def __init__(
            self,
            routes: Optional[List[BaseRoute]] = None,
            redirect_slashes: bool = True,
            default: Optional[ASGIApp] = None,
            dependency_overrides_provider: Optional[Any] = None,
            route_class: Type[APIRoute] = APIRoute,
            default_response_class: Optional[Type[Response]] = None,
            on_startup: Optional[Sequence[Callable]] = None,
            on_shutdown: Optional[Sequence[Callable]] = None,
            config_data: dict = None
    ) -> None:
        super().__init__(
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=APIRoute,
            default_response_class=default_response_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
        self.config_data = config_data
        self.__add_routes()

    def __add_routes(self):
        @self.post("")
        async def calculate_pricing(
                request: Request,
                response: Response,
                project_pricings: List[ProjectPricing],
                auth_detail: AuthDetail = Depends(Authorize(Permission.VRE)),
                db: Session = Depends(get_db),
                aiohttp_session: ClientSession = Depends(aiohttp_session)
        ):
            # check if need to check user limit or organization limit
            check_user_limit: bool = \
                (auth_detail.type == AuthType.ACCESS_TOKEN and
                 not auth_detail.decoded["orgname"]) or \
                (auth_detail.type == AuthType.API_KEY and
                 auth_detail.decoded["key_type"] == APIKeyType.USER_KEY)

            # get the username, orgname
            if auth_detail.type == AuthType.ACCESS_TOKEN:
                username = auth_detail.decoded["username"]
                orgname = auth_detail.decoded["orgname"]
            elif auth_detail.decoded["key_type"] == APIKeyType.USER_KEY:
                username = auth_detail.decoded["sub"]
                orgname = None
            else:
                username = None
                orgname = auth_detail.decoded["sub"]

            # get the limit of user or organization
            if check_user_limit:
                limit = crud.limit.read_by_username(db=db, username=username)
            else:
                limit = crud.limit.read_by_orgname(db=db, orgname=orgname)

            # validate limit of user or organization
            if not limit:
                error_code = USER_SUBSCRIPTION_NOT_EXIST if check_user_limit else ORGANIZATION_SUBSCRIPTION_NOT_EXIST
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED,
                    {
                        API_RESPONSE_ERROR_CODE_STRING: error_code,
                        API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(error_code)
                    }
                )

            # get utilization of user/organization
            if check_user_limit:
                daily_utilization = get_user_daily_utilization(db=db, username=username)
                monthly_utilization = get_user_monthly_utilization(db=db, username=username)
                lifetime_utilization = get_user_lifetime_utilization(
                    db=db,
                    username=username,
                    reset_date=limit.lifetime_reset_date
                )
            else:
                daily_utilization = get_user_daily_utilization(db=db, username=username)
                monthly_utilization = get_user_monthly_utilization(db=db, username=username)
                lifetime_utilization = get_user_lifetime_utilization(
                    db=db,
                    username=username,
                    reset_date=limit.lifetime_reset_date
                )

            # check if the user/organization has limit(subscription)
            has_daily_limit = limit.daily != -1
            has_monthly_limit = limit.monthly != -1
            has_lifetime_limit = limit.lifetime != -1

            # check if the user/organization can calculate the number of projects requested
            if has_daily_limit and (daily_utilization >= limit.daily or daily_utilization + len(project_pricings)
                                    > limit.daily):
                error_code = USER_DAILY_LIMIT_EXCEED if check_user_limit else ORGANIZATION_DAILY_LIMIT_EXCEED
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED, {
                        API_RESPONSE_ERROR_CODE_STRING: error_code,
                        API_RESPONSE_ERROR_MESSAGE_STRING: get_limit_exceed_error_string(
                            error_code=error_code,
                            limit=limit.daily,
                            utilization=daily_utilization,
                            projects_requested=len(project_pricings)
                        )
                    }
                )
            elif has_monthly_limit and (monthly_utilization >= limit.monthly or
                                        monthly_utilization + len(project_pricings) > limit.monthly):
                error_code = USER_MONTHLY_LIMIT_EXCEED if check_user_limit else ORGANIZATION_MONTHLY_LIMIT_EXCEED
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED, {
                        API_RESPONSE_ERROR_CODE_STRING: error_code,
                        API_RESPONSE_ERROR_MESSAGE_STRING: get_limit_exceed_error_string(
                            error_code=error_code,
                            limit=limit.monthly,
                            utilization=monthly_utilization,
                            projects_requested=len(project_pricings)
                        )
                    }
                )
            elif has_lifetime_limit and (lifetime_utilization >= limit.lifetime or
                                         lifetime_utilization + len(project_pricings) > limit.lifetime):
                error_code = USER_LIFETIME_LIMIT_EXCEED if check_user_limit else ORGANIZATION_LIFETIME_LIMIT_EXCEED
                raise HTTPException(
                    status.HTTP_402_PAYMENT_REQUIRED, {
                        API_RESPONSE_ERROR_CODE_STRING: error_code,
                        API_RESPONSE_ERROR_MESSAGE_STRING: get_limit_exceed_error_string(
                            error_code=error_code,
                            limit=limit.lifetime,
                            utilization=lifetime_utilization,
                            projects_requested=len(project_pricings)
                        )
                    }
                )

            # include SDG 13 by default (all projects help Climate Action)
            for index, project_pricing in enumerate(project_pricings):
                if "13" not in project_pricing.project.sdg:
                    project_pricing.project.sdg.append("13")


            # get mappings from static service
            status_code, mappings_json = await get_mappings(
                aiohttp_session=aiohttp_session,
                auth_detail=auth_detail,
                project_pricings=project_pricings
            )

            advanced = True if Authorize(Permission.ADVANCED, raise_exception=False)(request, auth_detail) else False
            if not advanced:
                mappings_json: List[dict] = validate(project_mappings=parse_obj_as(List[ProjectMapping], mappings_json))

            pricings, projects_priced_count = calculate(
                db=db,
                project_pricings=project_pricings,
                project_mappings=parse_obj_as(List[ProjectMapping], mappings_json),
                config_data=self.config_data,
                verbose=advanced
            )

            crud.request.create(db=db, request=RequestCreate(
                request_type=RequestType.USER_REQUEST if check_user_limit else RequestType.ORGANIZATION_REQUEST,
                model_name=self.config_data["model_name"],
                username=username,
                orgname=orgname,
                body=json.dumps(project_pricings, default=str),
                response=json.dumps(pricings, default=str),
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                projects_requested_count=len(project_pricings),
                projects_priced_count=projects_priced_count
            ))

            response.status_code = status_code if projects_priced_count == 0 else status.HTTP_200_OK
            return pricings


def router(config_data: dict):
    return PricingRouter(config_data=config_data)
