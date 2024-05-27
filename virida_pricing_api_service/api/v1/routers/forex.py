from fastapi import APIRouter, Depends
from typing import List
from schemas.forex import Forex
from schemas.permission import Permission
from api.helpers import Authorize
import datetime as dt

import crud
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()


@router.get("/latest", response_model=List[Forex], dependencies=[Depends(Authorize(Permission.FOREX))], tags=["forex"])
def get_latest_exchange_rates(db: Session = Depends(get_db)):
    return crud.forex.read_latest_exchange_rates(db=db)

@router.get("/{start_date}/{end_date}", response_model=List[Forex], dependencies=[Depends(Authorize(Permission.FOREX))], tags=["forex"])
def get_exchange_rates(start_date: dt.date, end_date: dt.date, db: Session = Depends(get_db)):
    print("test")
    return crud.forex.read_by_timeframe(start_date=start_date, end_date=end_date, db=db)
