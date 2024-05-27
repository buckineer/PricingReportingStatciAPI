from typing import List
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.helpers import authenticate
from database import get_db
from schemas.project import Project, ProjectValidation, ProjectMapping
from route_classes import ProjectValidationRoute
from helpers import map_project
import crud
from core.static import DEFAULT_MAPPING_VERSION

router = APIRouter()
router.route_class = ProjectValidationRoute


@router.get("/attributes/{attribute}", response_model=List[str], dependencies=[Depends(authenticate)], tags=["static"])
def get_attributes(attribute: str, version: Optional[int] = DEFAULT_MAPPING_VERSION, db: Session = Depends(get_db)):
    attributes = crud.static.read(db, attribute, version)
    if not attributes:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attribute does not exist")

    if attribute == "vintage":
        year = datetime.now().year
        return [year - int(vintage.property) for vintage in attributes]

    return [value.property for value in attributes]


@router.post("/projects/validate", response_model=List[ProjectValidation], dependencies=[Depends(authenticate)], tags=["static"])
async def validate_projects(projects: List[Project]):
    return [ProjectValidation(project=project, status="OK", description="") for project in projects]


@router.post("/projects/map", response_model=List[ProjectMapping], dependencies=[Depends(authenticate)], tags=["static"])
async def map_projects(projects: List[Project]):
    validated_projects: List[ProjectValidation] = [ProjectValidation(project=project, status="OK", description="") for project in projects]
    mappings: List[ProjectMapping] = []

    for validated_project in validated_projects:
        mapping = map_project(validated_project=validated_project.dict(exclude_unset=False))
        mappings.append(ProjectMapping(
            project=validated_project.project,
            status=validated_project.status,
            description=validated_project.description,
            mapping=mapping
        ))

    return mappings
