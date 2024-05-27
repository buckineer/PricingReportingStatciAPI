from typing import List, Optional, Type, Any, Sequence, Callable
import datetime as dt
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt


from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute
from fastapi.exceptions import HTTPException
from starlette.routing import BaseRoute
from starlette import status
from starlette.types import ASGIApp
from starlette.responses import Response
from pydantic import parse_obj_as
from sqlalchemy.orm import Session
from aiohttp import ClientSession

import crud
from schemas.project import HistoricalPricing, ProjectMapping, ProjectPricing
from schemas.standardized_instrument import InstrumentType
from schemas.request import RequestCreate, RequestType
from schemas.interest_curve import InterestCurve
from schemas.api_key import AuthDetail, AuthType, APIKeyType
from schemas.permission import Permission
from helpers.pricing import get_mappings, get_platts_mappings, validate
from helpers.pricing import run_model, run_platts_model
from helpers.database import get_user_daily_utilization, get_user_monthly_utilization, get_user_lifetime_utilization
from api.helpers import authenticate, Authorize

from database import get_db
from httpclient import aiohttp_session
from core import weights
from core.interpolate import Interpolate
from core.static import API_RESPONSE_ERROR_CODE_STRING, \
    INSTRUMENT_NO_BID_OR_ASK, API_RESPONSE_ERROR_MESSAGE_STRING, get_error_string_by_error_code, \
    API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    USER_SUBSCRIPTION_NOT_EXIST, get_error_string_by_error_code, ORGANIZATION_SUBSCRIPTION_NOT_EXIST, \
    ORGANIZATION_DAILY_LIMIT_EXCEED, USER_DAILY_LIMIT_EXCEED, get_limit_exceed_error_string, USER_MONTHLY_LIMIT_EXCEED, \
    ORGANIZATION_MONTHLY_LIMIT_EXCEED, ORGANIZATION_LIFETIME_LIMIT_EXCEED, USER_LIFETIME_LIMIT_EXCEED


def calculate_platts_price(row: pd.Series, position: int, index: str):
    benchmarks = json.loads(row["outputs"].replace("\'", "\""))["beta"]
    drifts = json.loads(row["drift"].replace("\'", "\""))
    beta_tensor = row["output"]["beta"][position]

    beta = 0.0
    for i in range(len(beta_tensor)):
        if not benchmarks[i] in row._index:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                                "We're unable to price your project(s) due to missing support data")

        benchmark = row[benchmarks[i]]
        beta_benchmark = float(beta_tensor[i])
        beta = beta + (benchmark * beta_benchmark)

    sigma = np.exp((row["output"]["sigma"].numpy()[position] ** 2.) / 2.)
    drift = drifts[index]
    return float(beta * sigma * drift)


def calculate_price(db: Session, row: pd.Series, position: int, project_pricing: ProjectPricing) -> tuple:
    benchmarks = json.loads(row["outputs"].replace("\'", "\""))["beta"]
    drifts = json.loads(row["drift"].replace("\'", "\""))
    beta = row["output"]["beta"][position]
    sigma = row["output"]["sigma"].numpy()[position]

    interest_rate = 0

    if project_pricing.horizon != 'spot':
        pricing_date = row.name
        if project_pricing.horizon < pricing_date:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Horizon date must be greater-than or inside the pricing date range")

        curve = row["eua_curve"]

        times = np.array(curve["times"])
        rates = np.array(curve["rates"])

        try:
            r = Interpolate(times, rates)
        except ValueError as ex:
            print("[-]", ex)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")

        t = (project_pricing.horizon - pricing_date).days / 365

        row[benchmarks[0]] = row[benchmarks[0]] * (1 + r(t))
        row[benchmarks[2]] = row[benchmarks[2]] * (1 + r(t))
        interest_rate = r(t)

    beta_benchmarks = []
    for i in range(len(beta)):
        if not benchmarks[i] in row._index:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")
        beta_benchmarks.append(row[benchmarks[i]])

    B = np.sum(np.multiply(beta, beta_benchmarks))
    S = np.exp((sigma ** 2.) / 2.)

    # project category based approach for vintage
    project_categories = [x.split('.')[0] for x in project_pricing.project.project]
    t = (dt.datetime.now() - dt.datetime(int(project_pricing.project.vintage), 12, 31, 23, 59)).days / 365
    vintage_discount_factor = np.average([_gbm_expectation(t, json.loads(row["vintage_disc_fact"].replace("\'", "\""))[category]) for category in project_categories])

    project_drift = np.mean([drifts["project"][category] for category in project_pricing.project.project])
    sdg_drift = np.prod([drifts["sdg"][sdg] for sdg in project_pricing.project.sdg]) 
    drift = project_drift * sdg_drift

    mid = vintage_discount_factor * B * S * drift

    # CORSIA modelling disabled (i.e. we get price from transaction price stored in standardized_instrument instead of modelling price)
    if project_pricing.project.corsia == 1 and int(project_pricing.project.vintage) >= int(row["corsia_min_year"]):
        # retrieve latest bid, ask, and date from Series
        bid = row[InstrumentType.BID]
        ask = row[InstrumentType.ASK]
        
        if bid is None or ask is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, {
                API_RESPONSE_ERROR_CODE_STRING: INSTRUMENT_NO_BID_OR_ASK,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(INSTRUMENT_NO_BID_OR_ASK)
            })
        mid = 0.5 * (bid + ask)
    else:
        # bid-ask spread (common logic for non CORSIA eligible assets)
        bid_ask_spread = row["bid_ask_spread"]
        if abs(bid_ask_spread) > 0:
            bid_mult = 1 - (bid_ask_spread / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
            ask_mult = 1 + (bid_ask_spread / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
            bid = bid_mult * mid
            ask = ask_mult * mid
        else:
            bid, ask = mid, mid
    return (
        float(mid),
        float(bid),
        float(ask),
        float(vintage_discount_factor),
        float(drift),
        float(project_drift),
        float(sdg_drift),
        float(interest_rate)
    )


def get_platts_pricing_dict(date: dt.date, position: int, index: str, row: pd.Series, verbose: bool = False):
    pricing = {
        "date": date,
        "price": row[f"mid{position}"]
    }
    if verbose:
        benchmarks = json.loads(row["outputs"].replace("\'", "\""))["beta"]
        drifts = json.loads(row["drift"].replace("\'", "\""))
        beta_tensor = row["output"]["beta"][position]
        pricing["indexes"] = row[benchmarks].to_dict()
        pricing["beta"] = {benchmarks[i]: float(beta_tensor[i]) for i in range(len(beta_tensor))}
        pricing["sigma"] = float(row["output"]["sigma"].numpy()[position][0])
        pricing["drift"] = drifts[index]
        pricing["weights"] = row["weights"]
    return pricing


def get_pricing_dict(date: dt.date, position: int, row: pd.Series, corsia: int, verbose: bool = False):
    bid = row[f"bid{position}"]
    ask = row[f"ask{position}"]

    pricing = {
        "date": date,
        "bid": bid if not np.isnan(bid) else None,
        "ask": ask if not np.isnan(ask) else None
    }
    if verbose:
        benchmarks = json.loads(row["outputs"].replace("\'", "\""))["beta"]
        beta_tensor = row["output"]["beta"][position]
        pricing["indexes"] = row[benchmarks].to_dict()
        pricing["beta"] = {benchmarks[i]: float(beta_tensor[i]) for i in range(len(beta_tensor))}
        pricing["sigma"] = float(row["output"]["sigma"].numpy()[position][0])
        pricing["weights"] = row["weights"]

        mid = float(row[f"mid{position}"])
        pricing["mid"] = mid if not np.isnan(mid) else None

        pricing["vintage_discount_factor"] = row[f"vintage_discount_factor{position}"]
        pricing["bid_ask_spread"] = row[f"bid_ask_spread"]
        pricing["drift"] = row[f"drift{position}"]
        pricing["drift_breakdown"] = {"project": row[f"project_drift{position}"], "sdg": row[f"sdg_drift{position}"]}
        pricing["corsia"] = {"date": row["corsia_date"] if corsia else ""}
        pricing["interest_rate"] = row[f"interest_rate{position}"]
    return pricing


def check_limit(db: Session, auth_detail: AuthDetail, project_pricings: List[ProjectPricing]):
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


def log_request(db: Session, auth_detail: AuthDetail, model_name: str, project_pricings: List[ProjectPricing], pricings: list, valid_pricings_count: int):
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

    crud.request.create(db=db, request=RequestCreate(
        request_type=RequestType.USER_REQUEST if check_user_limit else RequestType.ORGANIZATION_REQUEST,
        model_name=model_name,
        username=username,
        orgname=orgname,
        body=json.dumps(project_pricings, default=str),
        response=json.dumps(pricings, default=str),
        time=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        projects_requested_count=len(project_pricings),
        projects_priced_count=valid_pricings_count
    ))


def _gbm_expectation(t, mu):
    return np.exp(mu * t)

                    
class HistoricalPricingRouter(APIRouter):
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
        async def price(
            request: Request,
            response: Response,
            pricing: HistoricalPricing,
            auth_detail: AuthDetail = Depends(authenticate),
            db: Session=Depends(get_db),
            aiohttp_session: ClientSession=Depends(aiohttp_session)
        ) -> dict:
            model_name: str = self.config_data["model_name"]
            model_version: str = self.config_data["model_version"]
            is_platts_request: bool = model_name == "platts"

            authorize: Callable = Authorize(Permission.PLATTS if is_platts_request else Permission.VRE)
            authorize(request, auth_detail)

            if pricing.start_date is None or pricing.end_date is None:
                pricing.start_date = pricing.end_date = crud.system.read(db).date
            
            if not is_platts_request:
               check_limit(db=db, auth_detail=auth_detail, project_pricings=pricing.scenarios)

            mappings = []
            if is_platts_request:
                mappings = get_platts_mappings([scenario.project.index for scenario in pricing.scenarios])
            else:
                status_code, mappings_json = await get_mappings(
                    aiohttp_session=aiohttp_session,
                    auth_detail=auth_detail,
                    project_pricings=pricing.scenarios
                )

                if not Authorize(Permission.ADVANCED, raise_exception=False)(request, auth_detail):
                    mappings_json: List[dict] = validate(project_mappings=parse_obj_as(List[ProjectMapping], mappings_json))

                response.status_code = status_code
                mappings = parse_obj_as(List[ProjectMapping], mappings_json)

            try:
                df = weights.get(db, model_name, model_version, pricing.start_date, pricing.end_date)
            except weights.WeightReadingException as ex:
                print(ex)
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")

            df["output"] = df.apply(lambda row: run_platts_model([mapping for mapping in mappings if mapping is not None], row["model"])
                            if is_platts_request else run_model(mappings, row["model"]), axis=1)

            try:
                indexes_df = crud.benchmark_index.read_dataframe(db, pricing.start_date, pricing.end_date)
                df = pd.concat([df, indexes_df], axis=1).sort_index().fillna(method="pad")
            except crud.benchmark_index.BenchmarkIndexException as ex:
                print(ex)
                raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")

            if not is_platts_request:
                try:
                    bidask_df = crud.standardized_instrument.read_dataframe(db, pricing.start_date, pricing.end_date)
                    df = pd.concat([df, bidask_df], axis=1).sort_index().fillna(method="pad")
                except crud.standardized_instrument.StandardizedInstrumentException as ex:
                    print(ex)
                    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")
                
                try:
                    interest_curve_df = crud.interest_curve.read_dataframe(db, pricing.start_date, pricing.end_date)
                    df = pd.concat([df, interest_curve_df], axis=1).sort_index().fillna(method="pad")
                except crud.interest_curve.InterestCurveException as ex:
                    print(ex)
                    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "We're unable to price your project(s) due to missing support data")

            verbose = True if Authorize(Permission.ADVANCED, raise_exception=False)(request, auth_detail) else False
            pricings = []
            index = 0
            for position, mapping in enumerate(mappings):
                if is_platts_request:
                    project = pricing.scenarios[position].project
                    if not mapping:
                        pricings.append({
                            "project": project.dict(exclude_unset=True),
                            "history": None
                        })
                        continue
                    
                    df[f"mid{index}"] = df.apply(lambda row: calculate_platts_price(row, index, project.index), axis=1)
                    pricings.append({
                        "project": project.dict(exclude_unset=True),
                        "history": [get_platts_pricing_dict(date, position, project.index, row, verbose) for date, row in df.iterrows()]
                    })
                else:
                    project_pricing = pricing.scenarios[position]
                    if not mapping.mapping:
                        pricings.append({
                            "project": project_pricing.project,
                            "horizon": project_pricing.horizon,
                            "status": mapping.status,
                            "description": mapping.description,
                            "history": None
                        })
                        continue

                    (
                        df[f"mid{index}"],
                        df[f"bid{index}"],
                        df[f"ask{index}"],
                        df[f"vintage_discount_factor{index}"],
                        df[f"drift{index}"],
                        df[f"project_drift{index}"],
                        df[f"sdg_drift{index}"],
                        df[f"interest_rate{index}"]
                    ) = zip(*df.apply(lambda row: calculate_price(db, row, index, project_pricing), axis=1))

                    pricings.append({
                        "project": project_pricing.project,
                        "horizon": project_pricing.horizon,
                        "status": mapping.status,
                        "description": mapping.description,
                        "history": [get_pricing_dict(date, position, row, project_pricing.project.corsia, verbose) for date, row in df.iterrows()]
                    })
                index += 1

            valid_pricings_count = 0
            for i in range(0, index):
                length = len(df[~df[f"mid{i}"].isnull()])
                valid_pricings_count = valid_pricings_count + length

            log_request(db=db, auth_detail=auth_detail, model_name=model_name, project_pricings=pricing.scenarios, pricings=pricings, valid_pricings_count=valid_pricings_count)
            return pricings


def router(config_data: dict):
    return HistoricalPricingRouter(config_data=config_data)
