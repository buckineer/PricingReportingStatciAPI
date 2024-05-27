from pydantic import BaseModel, constr
from datetime import datetime
from datetime import date


class InterestRateCreate(BaseModel):
    date: date
    currency: constr(max_length=3)
    tenor: constr(max_length=3)
    rate: float
    timestamp: datetime


class InterestRate(InterestRateCreate):
    class Config:
        orm_mode = True
