import re
import datetime as dt
from typing import List, Optional, Union

from pydantic import BaseModel, validator

DEFAULT_MAPPING_VERSION = 3


class Project(BaseModel):
    version: Optional[int] = DEFAULT_MAPPING_VERSION  # default mapping version set to version 2 (mapping used for model v7). version 1 was used for model v5/v6
    standard: Optional[List[str]] = None
    project: Optional[List[str]] = None
    sdg: Optional[List[str]] = None
    vintage: Optional[str] = None
    corsia: Optional[int] = 0  # if corsia flag not provided, default to zero
    country: Optional[List[str]] = None
    region: Optional[List[str]] = None
    subregion: Optional[List[str]] = None
    index: Optional[str] = None # TODO: Add validator for value to be between 1-6

    @validator("sdg")
    def validate_sdg(cls, value):
        if "13" not in value:
            value.append("13")
        return value

    @validator("index")
    def validate_index(cls, value):
        if int(value) not in range(1, 7):
            raise ValueError(f"index value: '{value}' is wrong")
        return value


class ProjectValidation(BaseModel):
    project: Project
    status: str
    description: str


class ProjectMapping(ProjectValidation):
    mapping: Optional[dict] = None


class ProjectPricing(BaseModel):
    project: Project
    horizon: Optional[Union[dt.date, str]] = None
    
    @validator('horizon')
    def validate_horizon(cls, value):
        if value == "spot":
            return value
        else:
            if not re.search("^dec[0-9]{4}$", value):
                raise ValueError(f"horizon value '{value}' is wrong. Make sure to use 'spot' or the 'decYYYY' pattern.")
            
            year = int(value[-4:])
            date = dt.date(year=year, month=12, day=1)

            today = dt.date.today() 
            if date <= today:
                raise ValueError(f"horizon value '{value}' is wrong. As of now, 'decYYYY' value must be later or equal" 
                                 + f" to dec{today.year + 1 if today.month == 12 else today.year}")

        return value


class HistoricalPricing(BaseModel):
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    scenarios: List[ProjectPricing]
