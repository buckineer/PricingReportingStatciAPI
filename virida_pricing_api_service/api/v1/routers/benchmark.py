import datetime as dt
from typing import List

from fastapi import APIRouter, Depends
from schemas.benchmark import Benchmark, BenchmarkCreate, BenchmarkUpdate, BenchmarkDelete, BenchmarkMetric, BenchmarkCreateResponse, BenchmarkUpdateResponse, BenchmarkDeleteResponse
from schemas.permission import Permission
from api.helpers import Authorize

import crud
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()
permissions = [Permission.BENCHMARK]


@router.get("/latest", response_model=List[Benchmark], dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def get_latest_benchmarks(db: Session = Depends(get_db)):
    return crud.benchmark.read_latest_benchmarks(db=db)


@router.get("/metrics", response_model=List[BenchmarkMetric], dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def get_latest_metrics(db: Session = Depends(get_db)):
    return crud.benchmark.fetch_latest_metrics(db=db)


@router.get("/all/{start_date}/{end_date}", response_model=List[Benchmark], dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def get_benchmarks(start_date: dt.date, end_date: dt.date, db: Session=Depends(get_db)):
    return crud.benchmark.read(db, start_date, end_date)


@router.post("", response_model=BenchmarkCreateResponse, dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def create_benchmarks(benchmarks: List[BenchmarkCreate], db: Session=Depends(get_db)):
    response = BenchmarkCreateResponse(success=[], error=[])
    for benchmark in benchmarks:
        created_benchmark = crud.benchmark.create(db, benchmark)
        if created_benchmark:
            response.success.append(created_benchmark)
        else:
            response.error.append(benchmark)
    return response


@router.patch("", response_model=BenchmarkUpdateResponse, dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def update_benchmarks(benchmarks: List[BenchmarkUpdate], db: Session=Depends(get_db)):
    response = BenchmarkUpdateResponse(success=[], error=[])
    for benchmark in benchmarks:
        updated_benchmark = crud.benchmark.update(db, benchmark)
        if updated_benchmark:
            response.success.append(updated_benchmark)
        else:
            response.error.append(benchmark)
    return response


@router.delete("", response_model=BenchmarkDeleteResponse, dependencies=[Depends(Authorize(permissions))], tags=["benchmark"])
def delete_benchmarks(benchmarks: List[BenchmarkDelete], db: Session=Depends(get_db)):
    response = BenchmarkDeleteResponse(success=[], error=[])
    for benchmark in benchmarks:
        if crud.benchmark.delete(db, benchmark):
            response.success.append(benchmark)
        else:
            response.error.append(benchmark)
    return response
