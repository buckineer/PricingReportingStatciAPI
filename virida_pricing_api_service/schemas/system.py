import datetime as dt
from pydantic import BaseModel


class System(BaseModel):
    date: dt.date

    class Config:
        orm_mode = True
