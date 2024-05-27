from typing import List, Callable, Sequence
import os

from fastapi import status, Request, Response, Depends
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.error_wrappers import ErrorList
from sqlalchemy.orm import Session
from json import JSONDecodeError

from database import get_db, DatabaseContextManager
from helpers import validate_projects, map_project
from config import import_class
config = import_class(os.environ['APP_SETTINGS'])


class ProjectValidationRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        default_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await default_route_handler(request)
            except RequestValidationError as exc:
                projects: List[dict] = []
                try:
                    projects = await request.json()
                except JSONDecodeError as decode_exception:
                    return JSONResponse(
                        {
                            "detail": f"Request body is not valid JSON. {decode_exception}"
                        },
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    )

                errors: Sequence[ErrorList] = exc.errors()
                validated_projects: List[dict] = validate_projects(projects, errors)

                if request.url.path == f"{config.API_V1_BASE_ROUTE}/projects/validate":
                    return self.handle_project_validation_error(validated_projects)
                elif request.url.path == f"{config.API_V1_BASE_ROUTE}/projects/map":
                    return self.handle_mapping_project_validation_error(validated_projects)

        return custom_route_handler

    def handle_project_validation_error(self, validated_projects: List[dict]) -> JSONResponse:
        return JSONResponse(content=validated_projects, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def handle_mapping_project_validation_error(self, validated_projects: List[dict]):
        content = []

        for validated_project in validated_projects:
            if validated_project["status"] == "OK":
                mapping = map_project(validated_project=validated_project)
                validated_project.update({"mapping": mapping})
                content.append(validated_project)
            else:
                validated_project.update({"mapping": None})
                content.append(validated_project)

        return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
