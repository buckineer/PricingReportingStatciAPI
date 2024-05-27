from pydantic import BaseModel, constr
from datetime import datetime
from datetime import date


class ForexCreate(BaseModel):
    date: date
    currency: constr(max_length=3)
    close: float
    timestamp: datetime


class Forex(ForexCreate):
    class Config:
        orm_mode = True
