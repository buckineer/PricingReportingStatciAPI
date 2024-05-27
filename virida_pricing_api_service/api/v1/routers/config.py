from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.exceptions import HTTPException

import crud
from api.helpers import Authorize
from core.static import API_RESPONSE_ERROR_CODE_STRING, PRICING_CONFIG_DUPLICATED_KEY, \
    API_RESPONSE_ERROR_MESSAGE_STRING, get_error_string_by_error_code, PRICING_CONFIG_KEY_NOT_EXIST
from database import get_db
from schemas.config import PricingConfig, PricingConfigCreate, PricingConfigUpdate, PricingConfigDelete
from schemas.permission import Permission

router = APIRouter()
permissions = [Permission.ADVANCED]


@router.get("/all", response_model=List[PricingConfig], dependencies=[Depends(Authorize(permissions))],
            tags=["config"])
def read_all_pricing_config(db: Session = Depends(get_db)):
    return crud.config.read_all_pricing_config(db=db)


@router.get("", response_model=PricingConfig, dependencies=[Depends(Authorize(permissions))], tags=["config"])
def read_pricing_config(date: date, key: str, db: Session = Depends(get_db)):
    db_pricing_config = crud.config.read_by_date_key(date=date, key=key, db=db)
    if db_pricing_config is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_KEY_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_KEY_NOT_EXIST)
        })
    return db_pricing_config


@router.post("", response_model=PricingConfig, dependencies=[Depends(Authorize(permissions))], tags=["config"])
def create_pricing_config(pricing_config_create: PricingConfigCreate, db: Session = Depends(get_db)):
    db_pricing_config = crud.config.read_by_date_key(
        date=pricing_config_create.date, key=pricing_config_create.key, db=db)
    # primary key conflict
    if db_pricing_config is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_DUPLICATED_KEY,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_DUPLICATED_KEY)
        })
    return crud.config.create_pricing_config(pricing_config_create=pricing_config_create, db=db)


@router.patch("", response_model=PricingConfig, dependencies=[Depends(Authorize(permissions))], tags=["config"])
def update_pricing_config(pricing_config_update: PricingConfigUpdate, db: Session = Depends(get_db)):
    db_pricing_config = crud.config.read_by_date_key(
        date=pricing_config_update.date, key=pricing_config_update.key, db=db)

    # primary key not exist
    if db_pricing_config is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_KEY_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_KEY_NOT_EXIST)
        })

    return crud.config.update_pricing_config(pricing_config_update=pricing_config_update, db=db)


@router.delete("", response_model=PricingConfig, dependencies=[Depends(Authorize(permissions))], tags=["config"])
def delete_pricing_config(pricing_config_delete: PricingConfigDelete, db: Session = Depends(get_db)):
    db_pricing_config = crud.config.read_by_date_key(
        date=pricing_config_delete.date, key=pricing_config_delete.key, db=db
    )

    # primary key not exist
    if db_pricing_config is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_KEY_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_KEY_NOT_EXIST)
        })

    return crud.config.delete_pricing_config(pricing_config_delete=pricing_config_delete, db=db)
