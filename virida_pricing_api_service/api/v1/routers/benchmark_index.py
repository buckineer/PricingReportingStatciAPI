import datetime as dt
from typing import List

from fastapi import APIRouter, Depends
from schemas.benchmark_index import BenchmarkIndex
from schemas.permission import Permission
from api.helpers import Authorize

import crud
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()
permissions = [Permission.BENCHMARK]

@router.get("/all/{start_date}/{end_date}", response_model=List[BenchmarkIndex], dependencies=[Depends(Authorize(permissions))], tags=["benchmark_index"])
def get_benchmark_indexes(start_date: dt.date, end_date: dt.date, db: Session=Depends(get_db)):
    return crud.benchmark_index.read(db, start_date, end_date)