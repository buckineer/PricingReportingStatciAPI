import datetime as dt
from pydantic import BaseModel


class ModelConfigBase(BaseModel):
    date: dt.date
    model_name: str
    model_version: str


class ModelConfigDelete(ModelConfigBase):
    pass

class ModelConfig(ModelConfigBase):
    config: dict

    class Config:
        orm_mode = True

