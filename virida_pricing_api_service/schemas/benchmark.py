import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, constr


class BenchmarkCreate(BaseModel):
    date: dt.date
    name: constr(max_length=20)
    type: constr(max_length=20)
    symbol: constr(max_length=20)
    expiry_date: Optional[dt.date] = None  # set None as default value
    currency: constr(max_length=3)
    open: Optional[float] = None
    high: Optional[float]  = None
    low: Optional[float] = None
    close: float
    volume: Optional[int] = None
    timestamp: dt.datetime


class BenchmarkUpdate(BaseModel):
    date: Optional[dt.date] = None
    name: Optional[constr(max_length=20)] = None
    type: Optional[constr(max_length=20)] = None
    symbol: Optional[constr(max_length=20)] = None
    expiry_date: Optional[dt.date] = None
    currency: Optional[constr(max_length=3)] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    timestamp: Optional[dt.datetime] = None


class BenchmarkDelete(BaseModel):
    date: dt.date
    name: constr(max_length=20)
    type: constr(max_length=20)
    symbol: constr(max_length=20)


class Benchmark(BenchmarkCreate):
    class Config:
        orm_mode = True


class BenchmarkMetricCreate(BaseModel):
    date: dt.date
    name: constr(max_length=20)
    value: float


class BenchmarkMetric(BenchmarkMetricCreate):
    class Config:
        orm_mode = True


class BenchmarkCreateResponse(BaseModel):
    success: List[Benchmark]
    error: List[BenchmarkCreate]


class BenchmarkUpdateResponse(BaseModel):
    success: List[Benchmark]
    error: List[BenchmarkUpdate]


class BenchmarkDeleteResponse(BaseModel):
    success: List[BenchmarkDelete]
    error: List[BenchmarkDelete]
