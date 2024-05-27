from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.interest_rate import InterestRate
from schemas.permission import Permission
from api.helpers import Authorize

import crud
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/latest", response_model=List[InterestRate], dependencies=[Depends(Authorize(Permission.ADVANCED))], tags=["interest_rate"])
def get_latest_interest_rates(db: Session = Depends(get_db)):
    return crud.interest_rate.read_latest_interest_rates(db=db)
