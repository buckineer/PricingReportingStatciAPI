from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, constr


class InstrumentType(str, Enum):
    BID: str = "BID"
    ASK: str = "ASK"
    TRADE: str = "TRADE"
    MID: str = "MID"


class CurrencyType(str, Enum):
    USD: str = "USD"


class StandardizedInstrumentBase(BaseModel):
    instrument: constr(max_length=50)
    source: constr(max_length=50)
    date: date
    type: InstrumentType
    timestamp: Optional[datetime] = None
    currency: Optional[CurrencyType] = CurrencyType.USD
    price: Optional[float] = None
    volume: Optional[int] = None


class StandardizedInstrumentCreate(StandardizedInstrumentBase):
    pass


class StandardizedInstrument(StandardizedInstrumentBase):
    pass

    class Config:
        orm_mode = True


class StandardizedInstrumentCreateResponse(BaseModel):
    success: List[StandardizedInstrument]
    error: List[StandardizedInstrumentCreate]


class StandardizedInstrumentUpdateResponse(BaseModel):
    success: List[StandardizedInstrument]
    error: List[StandardizedInstrument]


class InstrumentDeleteResponse(BaseModel):
    success: List[StandardizedInstrument]
    error: List[StandardizedInstrument]
