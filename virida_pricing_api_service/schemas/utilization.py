from typing import List
from datetime import datetime
from pydantic import BaseModel


class Utilization(BaseModel):
    limit: int
    utilization: int


class UtilizationWithLifetime(Utilization):
    lifetime_reset_date: datetime


class UserPricingUtilization(BaseModel):
    username: str
    daily: Utilization
    monthly: Utilization
    lifetime: UtilizationWithLifetime


class OrganizationPricingUtilization(BaseModel):
    orgname: str
    daily: Utilization
    monthly: Utilization
    lifetime: UtilizationWithLifetime


class PricingUtilizationAll(BaseModel):
    user: List[UserPricingUtilization]
    organization: List[OrganizationPricingUtilization]

    class Config:
        orm_mode = True
