import json
from typing import List

import numpy as np
from scipy.stats import norm
import math
import random
import tensorflow as tf
import datetime as dt
import asyncio
import aiohttp
from aiohttp import ClientSession
from fastapi import HTTPException, status

import crud
from schemas.project import  ProjectMapping, ProjectPricing
from config import import_class
import os

from core.ratecurve import RatesCurve
from sqlalchemy.orm import Session

import httpclient
from schemas.api_key import AuthDetail, AuthType

from core.helpers import get_market_data_v5_v6, get_market_data
from core.static import VINTAGE_DISCOUNT_FACTORS, VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS, \
    VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS_LEGACY, EUA_SPOT_REFERENCE_USD, SCALING_STD, SCALING_INTERCEPT, \
    BIDASK_SIGMA_PCT, BIDASK_SPREAD, BIDASK_ADDON_SPREAD, CORSIA_MIN_YEAR, API_RESPONSE_ERROR_CODE_STRING, \
    INSTRUMENT_NO_BID_OR_ASK, API_RESPONSE_ERROR_MESSAGE_STRING, get_error_string_by_error_code, \
    PRICING_CONFIG_CORSIA_MISSING, PRICING_CONFIG_VRE_MODEL_DRIFT_MISSING

config = import_class(os.environ['APP_SETTINGS'])


async def get_mappings(aiohttp_session: ClientSession, auth_detail: AuthDetail, project_pricings: List[ProjectPricing]) -> tuple:
    projects_json = [project_pricing.project.dict(exclude_unset=True) for project_pricing in project_pricings]

    if auth_detail.type == AuthType.API_KEY:
        headers = {"X-API-KEY": auth_detail.value}
    else:
        headers = {"Authorization": f"Bearer {auth_detail.value}"}

    try:
        response = await httpclient.post(session=aiohttp_session, url=config.STATIC_MAPPING_URL, json=projects_json, headers=headers)
    except (aiohttp.ClientConnectionError, asyncio.TimeoutError, aiohttp.ClientPayloadError, Exception) as exception:
        print("[-] Exception occured while getting the mapping values: ", exception)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Service is unavailable right now")

    (status_code, response_data) = response
    if (status_code != status.HTTP_200_OK and status_code != status.HTTP_422_UNPROCESSABLE_ENTITY):
        raise HTTPException(status_code, response_data["detail"])
    return (status_code, response_data)


def get_platts_mappings(indexes: list) -> list:
    mappings = {
        "1": [1, 0, 0, 0, 0, 0],
        "2": [0, 1, 0, 0, 0, 0],
        "3": [0, 0, 1, 0, 0, 0],
        "4": [0, 0, 0, 1, 0, 0],
        "5": [0, 0, 0, 0, 1, 0],
        "6": [0, 0, 0, 0, 0, 1]
    }
    return [mappings[index] if index in mappings else None for index in indexes]


def _gbm_expectation(t, mu):
    return np.exp(mu * t)


def _corsia(x, c1, c2, c3):
    return x * (1. + c1 * norm.pdf(math.log(c2 * x), loc=0., scale=c3))


def validate(project_mappings: List[ProjectMapping]):
    for index, project_mapping in enumerate(project_mappings):
        rules_breaches = []

        standard_count = len(project_mapping.project.standard)
        projectclass_count = len(project_mapping.project.project)
        country_count = len(project_mapping.project.country)
        region_count = 0 if project_mapping.project.region is None else len(project_mapping.project.region)
        subregion_count = 0 if project_mapping.project.subregion is None else len(project_mapping.project.subregion)

        if standard_count > 1:
            rules_breaches.append('only one value allowed for standard ({0} value(s) provided)'.format(standard_count))

        if projectclass_count > 1:
            rules_breaches.append(
                'only one value allowed for project ({0} value(s) provided)'.format(projectclass_count))

        if country_count > 1:
            rules_breaches.append('only one value allowed for country ({0} value(s) provided)'.format(country_count))

        if region_count > 0 or subregion_count > 0:
            rules_breaches.append('region and sub-region are not allowed, kindly use country only')

        if len(rules_breaches) > 0:
            project_mapping.mapping = None
            project_mapping.description = ', '.join(rules_breaches)
            project_mapping.status = 'NOK'

    return project_mappings


def get_valid_indexes(project_mappings: List[ProjectMapping]) -> list:
    indexes = []
    for index, project_mapping in enumerate(project_mappings):
        if project_mapping.mapping:
            indexes.append(index)
    return indexes


def run_model(
    project_mappings: List[ProjectMapping],
    tensorflow_model: object,
):
    geographies: list = []
    standards: list = []
    projects: list = []
    sdgs: list = []

    for index, project_mapping in enumerate(project_mappings):
        mapping: dict = project_mapping.mapping
        if mapping is None:
            continue

        country = np.array(mapping.get("country")) if mapping.get("country") is not None else [0]
        region = np.array(mapping.get("region")) if mapping.get("region") is not None else [0]
        subregion = np.array(mapping.get("subregion")) if mapping.get("subregion") is not None else [0]
        geography = np.bitwise_or(np.bitwise_or(country, region), subregion)
        geographies.append(geography)

        standards.append(mapping["standard"])
        projects.append(mapping["project"])
        sdgs.append(mapping["sdg"])
    
    if not standards or not geographies or not projects or not sdgs:
        return None

    return tensorflow_model({
        "standard": np.array(standards, dtype=np.float32),
        "geography": np.array(geographies, dtype=np.float32),
        "project": np.array(projects, dtype=np.float32),
        "sdg": np.array(sdgs, dtype=np.float32)
    })


def run_platts_model(scenarios: List[List[int]], model: object):
    return model({"index": np.array(scenarios)})


def calculate(db: Session, project_pricings: List[ProjectPricing], project_mappings: List[ProjectMapping], config_data: dict, verbose=False) -> tuple:
    CORSIA = crud.config.read_latest_corsia(db=db)
    if CORSIA is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_CORSIA_MISSING,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_CORSIA_MISSING)
        })
    CORSIA_C1: int = CORSIA["C1"]
    CORSIA_C2: int = CORSIA["C2"]
    CORSIA_C3: int = CORSIA["C3"]
    CORSIA_ENABLED: bool = CORSIA["ENABLED"]
    VRE_MODEL_DRIFT = crud.config.read_latest_vre_model_drift(db=db)
    if VRE_MODEL_DRIFT is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_VRE_MODEL_DRIFT_MISSING,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_VRE_MODEL_DRIFT_MISSING)
        })
    pricings: list = []
    valid_indexes: list = []

    formula: int = config_data["formula"]
    model_id: str = config_data["model_id"]
    is_model_5or6: bool = model_id in ["800-8x800-2_v5b_weights", "800-8x800-2_v6b_weights", "800-8x800-2_v6c_weights", "800-8x800-2_v6d_weights"]
    market_data: dict = get_market_data_v5_v6(db=db) if is_model_5or6 else get_market_data(db=db)
    tensorflow_model = config_data["model"]

    geographies: list = []
    standards: list = []
    projects: list = []
    sdgs: list = []

    for index, project_mapping in enumerate(project_mappings):
        mapping: dict = project_mapping.mapping
        if mapping is None:
            project_pricing: ProjectPricing = project_pricings[index]
            pricings.append({
                "project": project_pricing.project,
                "horizon": project_pricing.horizon,
                "status": project_mapping.status,
                "description": project_mapping.description,
                "formula": None,
                "sigma": None,
                "beta": None,
                "mid": None,
                "bid": None,
                "ask": None,
                "vintage_discount_factor": None,
                "eua_forward": None,
                "model_id": None
            })
            continue

        valid_indexes.append(index)

        country = np.array(mapping.get("country")) if mapping.get("country") is not None else [0]
        region = np.array(mapping.get("region")) if mapping.get("region") is not None else [0]
        subregion = np.array(mapping.get("subregion")) if mapping.get("subregion") is not None else [0]
        geography = np.bitwise_or(np.bitwise_or(country, region), subregion)
        geographies.append(geography)

        standards.append(mapping["standard"])
        projects.append(mapping["project"])
        sdgs.append(mapping["sdg"])
    
    tensorflow_output = tensorflow_model({
        "standard": np.array(standards, dtype=np.float32),
        "geography": np.array(geographies, dtype=np.float32),
        "project": np.array(projects, dtype=np.float32),
        "sdg": np.array(sdgs, dtype=np.float32)
    })

    projects_priced_count: int = 0

    for index, valid_index in enumerate(valid_indexes):
        project_pricing: ProjectPricing = project_pricings[valid_index]
        project_mapping: ProjectMapping = project_mappings[valid_index]

        if is_model_5or6:
            eua_forward = market_data[project_pricing.horizon]  # forward EUA in USD, not that if horizon is spot, eua_forward = eua_spot
            eua_spot = market_data["spot"]  # spot EUA in USD

            # project category based approach for vintage
            if model_id in ["800-8x800-2_v6c_weights", "800-8x800-2_v6d_weights"]:
                project_category_list = [int(int(x) / 10) for x in project_pricing.project.project]
                t = (dt.datetime.now() - dt.datetime(year=int(project_pricing.project.vintage),
                                                     month=12, day=31, hour=23, minute=59, second=0)).days / 365
                vintage_discount_factors = [_gbm_expectation(t, VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS_LEGACY[x]) for x in project_category_list]
                vintage_discount_factor = np.average(vintage_discount_factors)
            # legacy logic for vintage
            else:
                vintage_discount_factor = VINTAGE_DISCOUNT_FACTORS[project_pricing.project.vintage]
        else:
            # project category based approach for vintage
            project_category_list = [x.split('.')[0] for x in project_pricing.project.project]
            t = (dt.datetime.now() - dt.datetime(year=int(project_pricing.project.vintage),
                                                    month=12, day=31, hour=23, minute=59, second=0)).days / 365
            vintage_discount_factors = [_gbm_expectation(t, VINTAGE_PROJECT_CATEGORY_DISCOUNT_FACTORS[x]) for x in project_category_list]
            vintage_discount_factor = np.average(vintage_discount_factors)

        if formula == 1:
            beta = float(tf.keras.backend.eval(tensorflow_output['beta'])[index][0])
            sigma = float(np.exp(tf.keras.backend.eval(tensorflow_output['log_sigma'])[index][0]))
            mid = vintage_discount_factor * np.exp(beta * np.log(eua_forward))
            bid = vintage_discount_factor * np.exp(beta * np.log(eua_forward) - BIDASK_SIGMA_PCT * sigma)
            ask = vintage_discount_factor * np.exp(beta * np.log(eua_forward) + BIDASK_SIGMA_PCT * sigma)

            pricings.insert(valid_index, {
                "project": project_pricing.project,
                "horizon": project_pricing.horizon,
                "status": project_mapping.status,
                "description": project_mapping.description,
                "formula": formula,
                "sigma": sigma,
                "beta": beta,
                "mid": mid,
                "bid": bid,
                "ask": ask,
                "vintage_discount_factor": vintage_discount_factor,
                "eua": eua_forward,
                "model_id": model_id
            })
        elif formula == 2:
            beta = float(tf.keras.backend.eval(tensorflow_output['beta'])[index][0])
            sigma = float(np.exp(tf.keras.backend.eval(tensorflow_output['log_sigma'])[index][0]))
            mid = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma) * eua_forward
            bid = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma - BIDASK_SIGMA_PCT * sigma) * eua_forward
            ask = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma + BIDASK_SIGMA_PCT * sigma) * eua_forward

            pricings.insert(valid_index, {
                "project": project_pricing.project,
                "horizon": project_pricing.horizon,
                "status": project_mapping.status,
                "description": project_mapping.description,
                "formula": formula,
                "sigma": sigma,
                "beta": beta,
                "mid": mid,
                "bid": bid,
                "ask": ask,
                "vintage_discount_factor": vintage_discount_factor,
                "eua": eua_forward,
                "model_id": model_id

            })
        elif formula == 3:
            # steps to compute scaler:
            # 0a. calculate eua_forward reference (if spot, take EUA_SPOT_REFERENCE_USD, otherwise eua_reference = EUA_SPOT_REFERENCE_USD * eua_forward / eua_spot)
            # 0b. calculate eua_forward current (if spot, take eua_spot, otherwise taken eua_forward [i.e eua_forward]
            # 1. calculate project price with EUA reference [price_ref]
            # 2. calculate project price with EUA current [price_current]
            # 3. x = log(price_ref/price_current)
            # 4. scaler = norm.cdf(x,loc=0.,scale=std)+0.5 [std defined in core static]
            # 5. compute price as per formula 2 and multiply by scaler
            beta = float(tf.keras.backend.eval(tensorflow_output['beta'])[index][0])
            sigma = float(np.exp(tf.keras.backend.eval(tensorflow_output['log_sigma'])[index][0]))

            # scaler calculation:

            if project_pricing.horizon == 'spot':
                eua_reference = EUA_SPOT_REFERENCE_USD
                eua_current = eua_spot
            else:
                eua_reference = EUA_SPOT_REFERENCE_USD * eua_forward / eua_spot
                eua_current = eua_forward

            price_mid_with_ref = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma) * eua_reference
            price_mid_with_current = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma) * eua_current
            x = math.log(price_mid_with_ref / price_mid_with_current)
            scaler = norm.cdf(x, loc=0., scale=SCALING_STD) + SCALING_INTERCEPT

            # project pricing with scaler
            mid = vintage_discount_factor * np.exp(beta - 0.5 * sigma * sigma) * eua_forward * scaler
            seed = (dt.datetime.now() - dt.datetime(1970, 1, 1)).days
            random.seed(seed)
            add_on_spread = random.uniform(-BIDASK_ADDON_SPREAD, BIDASK_ADDON_SPREAD)
            all_in_spread = BIDASK_SPREAD + add_on_spread
            bid = mid * (1. - all_in_spread)
            ask = mid * (1. + all_in_spread)

            if verbose:
                pricings.insert(valid_index, {
                    "project": project_pricing.project,
                    "horizon": project_pricing.horizon,
                    "status": project_mapping.status,
                    "description": project_mapping.description,
                    "formula": formula,
                    "scaler": scaler,
                    "sigma": sigma,
                    "beta": beta,
                    "mid": mid,
                    "bid": bid,
                    "ask": ask,
                    "spread": all_in_spread,
                    "vintage_discount_factor": vintage_discount_factor,
                    "eua_spot_usd": eua_spot,
                    "eua_forward_usd": eua_forward,
                    "model_id": model_id
                })
            else:
                pricings.insert(valid_index, {
                    "project": project_pricing.project,
                    "horizon": project_pricing.horizon,
                    "status": project_mapping.status,
                    "description": project_mapping.description,
                    "bid": bid,
                    "ask": ask,
                })
        elif formula == 4:
            # get beta and sigma (tf already returns exp() of beta/sigma)
            beta = tensorflow_output['beta'].numpy()[index]
            sigma = tensorflow_output['sigma'].numpy()[index][0]

            # benchmarks ('eua', 'co2', 'brent', 'treasury')
            benchmarks = np.array([
                market_data['indices']['eua']['value'],
                market_data['indices']['co2']['value'],
                market_data['indices']['brent']['value'],
                market_data['indices']['treasury']['value']])

            # sequence:
            # spot / forward
            # vintage
            # corsia
            # bid-ask

            # spot pricing
            if project_pricing.horizon == 'spot':
                S = np.exp((sigma ** 2.) / 2.)
                B = np.sum(np.multiply(beta, benchmarks))
                project_drift = np.mean([VRE_MODEL_DRIFT['project'][x] for x in project_pricing.project.project]) 
                sdg_drift = np.prod([VRE_MODEL_DRIFT['sdg'][sdg] for sdg in project_pricing.project.sdg]) 
                model_drift = project_drift * sdg_drift
                mid = vintage_discount_factor * S * B * model_drift
            # forward pricing
            else:
                usd_rate_curve = RatesCurve(valuation_date=dt.datetime.now(),
                                            currency='USD',
                                            tenor=[x['tenor'] for x in market_data['interest_rates']],
                                            rate=[x['rate'] for x in market_data['interest_rates']])

                # 1. get spot and forward
                # 2. calculate rc from rate_curve for expiry date
                # 3. c = rc-math.log(future/spot)
                # 4 adjust all benchmarks with
                # x[key] = math.exp(rc-c)*benchmarks[key]

                eua_spot_eur = market_data['prices']['spot']['eua']['value']
                eua_forward_eur = market_data['prices']['forward']['eua'][project_pricing.horizon]['value']
                expiry_date = dt.datetime.strptime(market_data['prices']['forward']['eua'][project_pricing.horizon]['expiry_date'], '%Y-%m-%d')
                rate = usd_rate_curve.get_rate(expiry_date)
                convenience_yield = rate - math.log(eua_forward_eur / eua_spot_eur)

                # we compute benchmarks forward for EUA and for brent
                # eua, c02, brent, treasury
                benchmarks[0] = benchmarks[0] * np.exp(rate - convenience_yield)  # eua
                benchmarks[2] = benchmarks[2] * np.exp(rate - convenience_yield)  # brent
                S = np.exp((sigma ** 2.) / 2.)
                B = np.sum(np.multiply(beta, benchmarks))
                project_drift = np.mean([VRE_MODEL_DRIFT['project'][x] for x in project_pricing.project.project]) 
                sdg_drift = np.prod([VRE_MODEL_DRIFT['sdg'][sdg] for sdg in project_pricing.project.sdg]) 
                model_drift = project_drift * sdg_drift
                mid = vintage_discount_factor * S * B * model_drift

            # CORSIA modelling enabled
            if CORSIA_ENABLED:
                # check CORSIA eligibility
                if project_pricing.project.corsia == 1 and int(project_pricing.project.vintage) >= CORSIA_MIN_YEAR:
                    # mid computed previouly is replaced
                    corsia_mid = _corsia(mid, CORSIA_C1, CORSIA_C2, CORSIA_C3)

                    # if model mid is lower than CORSIA model mid
                    if mid < corsia_mid:
                        mid = corsia_mid

                # bid-ask spread (common logic for CORSIA eligible assets and non CORSIA eligible assets)
                if abs(BIDASK_SPREAD) > 0:
                    bid_mult = 1 - (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                    ask_mult = 1 + (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                    bid = bid_mult * mid
                    ask = ask_mult * mid
                else:
                    bid, ask = mid, mid
            # CORSIA modelling disabled (i.e. we get price from transaction price stored in standardized_instrument  instead of modelling price)
            else:
                corsia_date, corsia_ask, corsia_date = None, None, None
                if project_pricing.project.corsia == 1 and int(project_pricing.project.vintage) >= CORSIA_MIN_YEAR:
                    # retrieve latest bid/ask from standardized_instrument table
                    corsia_bid, corsia_ask, corsia_date = crud.standardized_instrument.read_latest_bid_ask(db=db)
                    if corsia_bid is None or corsia_ask is None:
                        raise HTTPException(status.HTTP_404_NOT_FOUND, {
                            API_RESPONSE_ERROR_CODE_STRING: INSTRUMENT_NO_BID_OR_ASK,
                            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(INSTRUMENT_NO_BID_OR_ASK)
                        })
                    corsia_mid = 0.5 * (corsia_bid + corsia_ask)

                    # if model mid is lower than CORSIA standardized instrument mid, replace bid/ask/mid with standardized instrument
                    if mid < corsia_mid:
                        bid, ask, mid = corsia_bid, corsia_ask, corsia_mid
                    # if model mid is higher or equal than CORSIA standardized instrument mid, we keep the model mid
                    else:
                        corsia_date = None
                        # bid-ask spread (common logic for non CORSIA eligible assets)
                        if abs(BIDASK_SPREAD) > 0:
                            bid_mult = 1 - (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                            ask_mult = 1 + (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                            bid = bid_mult * mid
                            ask = ask_mult * mid
                        else:
                            bid, ask = mid, mid
                else:
                    # bid-ask spread (common logic for non CORSIA eligible assets)
                    if abs(BIDASK_SPREAD) > 0:
                        bid_mult = 1 - (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                        ask_mult = 1 + (BIDASK_SPREAD / 2.) * (np.exp(sigma ** 2.) - 1) ** 0.5
                        bid = bid_mult * mid
                        ask = ask_mult * mid
                    else:
                        bid, ask = mid, mid


            if verbose:
                if CORSIA_ENABLED:
                    corsia_diagnostic = {
                        "C1": CORSIA_C1,
                        "C2": CORSIA_C2,
                        "C3": CORSIA_C3
                    }
                else:
                    corsia_diagnostic = {
                        "date": corsia_date.strftime("%Y-%m-%d") if corsia_date is not None else ''
                    }
                pricings.insert(valid_index, {
                    "project": project_pricing.project,
                    "horizon": project_pricing.horizon,
                    "status": project_mapping.status,
                    "description": project_mapping.description,
                    "formula": formula,
                    "market_data": market_data,
                    "model_id": model_id,
                    "vintage_discount_factor": vintage_discount_factor,
                    "benchmarks": benchmarks.tolist(),
                    "exp_beta": beta.tolist(),
                    "exp_sigma": float(sigma),
                    "mid": float(mid),
                    "bid": float(bid),
                    "ask": float(ask),
                    "project_drift": project_drift,
                    "sdg_drift": sdg_drift,
                    "CORSIA": corsia_diagnostic
                })
            else:
                pricings.insert(valid_index, {
                    "project": project_pricing.project,
                    "horizon": project_pricing.horizon,
                    "status": project_mapping.status,
                    "description": project_mapping.description,
                    "bid": float(bid),
                    "ask": float(ask),
                })
        else:
            pricings.insert(valid_index, {
                "project": project_pricing.project,
                "horizon": project_pricing.horizon,
                "status": project_mapping.status,
                "description": project_mapping.description,
                "message": f"pricing formula {formula} not found"
            })
        
        projects_priced_count = projects_priced_count + 1
    return (pricings, projects_priced_count)
