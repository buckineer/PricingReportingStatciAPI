from attributes import attributes
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator, root_validator
from config import import_class
from core.static import DEFAULT_MAPPING_VERSION
import os
config = import_class(os.environ['APP_SETTINGS'])


visit_message = "Visit " + config.EXTERNAL_BASE_URL + config.API_V1_BASE_ROUTE +\
                "/attributes/{} to see the correct values"
value_error_message = "value: '{}' is wrong"


class Project(BaseModel):
    # default mapping version set to version 3 (mapping used for model v7, after Marcelo decided to review taxonomy in April 2021). version 1 was used for model v5/v6
    version: int = DEFAULT_MAPPING_VERSION
    standard: List[str]
    project: List[str]
    sdg: List[str]
    vintage: str
    corsia: int = 0  # if corsia flag not provided, default to zero
    country: Optional[List[str]] = None
    region: Optional[List[str]] = None
    subregion: Optional[List[str]] = None

    @validator('standard', each_item=True)
    def validate_standard(cls, value, values):
        print(attributes.standard)
        print(values['version'])
        if value not in [attribute.property for attribute in attributes.standard[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator('corsia')
    def validate_corsia(cls, value, values):
        if int(value) not in [0, 1]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator('vintage')
    def validate_vintage(cls, value, values):
        # current_year = datetime.now().year
        # years = [current_year - int(vintage.property) for vintage in attributes.vintage[values['version']]]
        # if int(value) not in years:
        if not (str(value) or '').isnumeric():
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator('project', each_item=True)
    def validate_project(cls, value, values):
        if value not in [attribute.property for attribute in attributes.project[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator("sdg", each_item=True)
    def validate_sdg(cls, value, values):
        if value not in [attribute.property for attribute in attributes.sdg[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator("country", each_item=True)
    def validate_country(cls, value, values):
        if not value:
            return value

        if value not in [attribute.property for attribute in attributes.country[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator("region", each_item=True)
    def validate_region(cls, value, values):
        if not value:
            return value

        if value not in [attribute.property for attribute in attributes.region[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @validator("subregion", each_item=True)
    def validate_subregion(cls, value, values):
        if not value:
            return value

        if value not in [attribute.property for attribute in attributes.subregion[values['version']]]:
            msg = value_error_message.format(value)
            raise ValueError(msg)

        return value

    @root_validator
    def validate_geography_fields(cls, values: dict):
        if len(values.keys()) < 3:
            return values

        geography_fields = []
        for key in values.keys():
            if key == "country" or key == "region" or key == "subregion":
                geography_fields.append(key)

        if len(geography_fields) != 3:
            return values

        country = values.get("country")
        region = values.get("region")
        subregion = values.get("subregion")

        if not country and not region and not subregion:
            raise ValueError("country, region, or subregion must be provided")

        return values

# Project.validate = Project.__post_init__
# Project.__post_init__ = lambda _: None


class ProjectValidation(BaseModel):
    project: Project
    status: str
    description: str


class ProjectMapping(ProjectValidation):
    mapping: dict
