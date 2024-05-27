from schemas.api_key import BlockedAPIKeyCreate, BlockedAPIKey
from schemas.permission import Permission

from fastapi import APIRouter, Depends
from typing import List
from api.helpers import Authorize

import crud
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()
permissions = [Permission.USER_ADMINISTRATION]


@router.post("/refresh_blacklist", response_model=List[BlockedAPIKey], dependencies=[Depends(Authorize(permissions))],
             tags=["api_keys"])
def refresh_blacklist(apikey_blacklist: List[BlockedAPIKeyCreate], db: Session = Depends(get_db)):
    return crud.api_key.refresh_apikey_blacklist(db=db, apikey_blacklist=apikey_blacklist)
