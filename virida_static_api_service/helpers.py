from typing import List, Sequence
from datetime import datetime

import numpy as np
from pydantic.error_wrappers import ErrorList

from schemas.project import Project
from attributes import attributes
import crud


def validate_projects(projects: List[dict], errors: Sequence[ErrorList]) -> List[dict]:
    content = []

    for index, project in enumerate(projects):
        project_errors = [error for error in errors if error["loc"][1] == index]

        if not project_errors:
            content.append({
                "project": project,
                "status": "OK",
                "description": ""
            })
            continue

        description = ""
        for error in project_errors:
            attribute = error["loc"][2]

            if attribute == "__root__":
                description += error["msg"]
                continue

            if error["type"] == "value_error.missing":
                description += f"{attribute} field is required. "
                continue
            elif error["type"] == "type_error.list":
                description += f"{attribute} must be a list of values. "
                continue

            description += f"{attribute} {error['msg']}. "

        description = description.rstrip()
        content.append({
            "project": project,
            "status": "NOK",
            "description": description
        })

    return content


def map_project(validated_project: dict):
    output: dict = {}
    version = validated_project['project']['version']

    for attribute_name, attribute_value in validated_project["project"].items():
        # list of attributes that won't be mapped as onehot
        if attribute_name in ["version", "vintage", "corsia"]:
            continue

        # if some of these not populated, we don't try to map them
        # making sure we have at least one of them is the role of validation not mapping
        if attribute_name in ['country', 'region', 'subregion']:
            if attribute_value is None:
                continue

        attribute_length = len(attributes[attribute_name][version][0].mapping)
        attribute_mapping = np.array([0] * attribute_length, dtype=int)

        if type(attribute_value) is not list:
            if attribute_name == "vintage":
                # assigning value to '0' as tensor_flow considers it as a role but its not using it.
                # year = datetime.now().year
                # attribute_value = str(year - int(attribute_value))
                attribute_value = "0"

            mapping_string = next(attribute.mapping for attribute in attributes[attribute_name][version] if attribute.property == attribute_value)
            attribute_mapping = np.array([mapping_digit for mapping_digit in mapping_string], dtype=int)
            output[attribute_name] = attribute_mapping.tolist()
            continue

        for value in attribute_value:
            mapping_string = next(attribute.mapping for attribute in attributes[attribute_name][version] if attribute.property == value)
            mapping = np.array([mapping_digit for mapping_digit in mapping_string], dtype=int)
            attribute_mapping += mapping

        output[attribute_name] = attribute_mapping.tolist()

    return output
