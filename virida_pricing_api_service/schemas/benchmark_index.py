from pydantic import BaseModel 
from datetime import date

class BenchmarkIndex(BaseModel):
    date: date
    benchmark: str
    value: float

    class Config:
        orm_mode = True
