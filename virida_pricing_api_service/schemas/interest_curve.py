from pydantic import BaseModel, constr
import datetime as dt


class InterestCurve(BaseModel):
    date: dt.date
    curve: constr(max_length=20)
    value: dict
