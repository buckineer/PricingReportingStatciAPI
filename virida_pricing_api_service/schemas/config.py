from datetime import date

from pydantic import BaseModel, constr


class PricingConfigBase(BaseModel):
    date: date
    key: constr(max_length=50)
    value: dict


class PricingConfigCreate(PricingConfigBase):
    pass


class PricingConfig(PricingConfigBase):
    pass

    class Config:
        orm_mode = True


class PricingConfigUpdate(PricingConfigBase):
    pass


class PricingConfigDelete(BaseModel):
    date: date
    key: constr(max_length=50)
