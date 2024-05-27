from typing import List
from sqlalchemy.orm import Session
from models import BlockedAPIKey
from schemas.api_key import BlockedAPIKeyCreate


def refresh_apikey_blacklist(db: Session, apikey_blacklist: List[BlockedAPIKeyCreate]):
    db.query(BlockedAPIKey).delete()
    db_apikey_blacklist = []
    for blocked_apikey in apikey_blacklist:
        db_blocked_api_key = BlockedAPIKey(**blocked_apikey.dict())
        db.add(db_blocked_api_key)
        db.commit()
        db.refresh(db_blocked_api_key)
        db_apikey_blacklist.append(db_blocked_api_key)
    db.commit()
    return db_apikey_blacklist


def is_apikey_blocked(db: Session, api_key: str) -> bool:
    db_api_key = db.query(BlockedAPIKey).filter_by(api_key=api_key).first()
    return db_api_key is not None
