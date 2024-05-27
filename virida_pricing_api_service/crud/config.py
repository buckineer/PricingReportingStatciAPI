from datetime import date

from sqlalchemy import desc
from sqlalchemy.orm import Session
from starlette import status
from starlette.exceptions import HTTPException

from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    PRICING_CONFIG_DB_CREATE_ERROR, get_error_string_by_error_code, PRICING_CONFIG_DB_UPDATE_ERROR, \
    PRICING_CONFIG_DB_DELETE_ERROR
from models import PricingConfig
from schemas.config import PricingConfigCreate, PricingConfigUpdate, PricingConfigDelete


def read_all_pricing_config(db: Session):
    return db.query(PricingConfig).all()


def read_by_date_key(date: date, key: str, db: Session):
    return db.query(PricingConfig).filter_by(date=date).filter_by(key=key).first()


def read_latest_corsia(db: Session):
    db_corsia = db.query(PricingConfig.value).filter_by(key="CORSIA").order_by(desc(PricingConfig.date)).first()
    if db_corsia is None:
        return None
    return db_corsia[0]


def read_latest_vre_model_drift(db: Session):
    db_vre_model_drift = db.query(PricingConfig.value).filter_by(key="VRE_MODEL_DRIFT").\
        order_by(desc(PricingConfig.date)).first()
    if db_vre_model_drift is None:
        return None
    return db_vre_model_drift[0]


def create_pricing_config(pricing_config_create: PricingConfigCreate, db: Session):
    try:
        db_pricing_config = PricingConfig(**pricing_config_create.dict())
        db.add(db_pricing_config)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_DB_CREATE_ERROR,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_DB_CREATE_ERROR)
        })

    return db_pricing_config


def update_pricing_config(pricing_config_update: PricingConfigUpdate, db: Session):
    try:
        db_pricing_config = read_by_date_key(date=pricing_config_update.date, key=pricing_config_update.key, db=db)
        db_pricing_config.value = pricing_config_update.value
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_DB_UPDATE_ERROR,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_DB_UPDATE_ERROR)
        })

    return db_pricing_config


def delete_pricing_config(pricing_config_delete: PricingConfigDelete, db: Session):
    try:
        db_pricing_config = read_by_date_key(date=pricing_config_delete.date, key=pricing_config_delete.key, db=db)
        db.query(PricingConfig).filter_by(date=pricing_config_delete.date)\
            .filter_by(key=pricing_config_delete.key).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, {
            API_RESPONSE_ERROR_CODE_STRING: PRICING_CONFIG_DB_DELETE_ERROR,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(PRICING_CONFIG_DB_DELETE_ERROR)
        })

    return db_pricing_config
