from typing import List
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Response
from starlette import status
from schemas.model_config import ModelConfig, ModelConfigDelete
from schemas.permission import Permission
from api.helpers import Authorize
from sqlalchemy.orm import Session
from database import get_db
from core import weights
import crud

router = APIRouter()
permissions = [Permission.ADVANCED]


@router.get("", response_model=List[ModelConfig], dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def get_all_model_configs(db: Session=Depends(get_db)):
    return crud.model_config.read(db)


@router.get("/{model_name}/{model_version}", response_model=List[ModelConfig], dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def get_model_configs(model_name: str, model_version: str, db: Session=Depends(get_db)):
    return crud.model_config.read(db, model_name=model_name, model_version=model_version)


@router.get("/{model_name}/{model_version}/{date}", response_model=ModelConfig, dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def get_model_config(model_name: str, model_version: str, date: dt.date, db: Session=Depends(get_db)):
    configs = crud.model_config.read(db, model_name=model_name, model_version=model_version, date=date)
    if not configs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model config does not exist")
    return configs[0]


@router.post("", response_model=ModelConfig, dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def create_model_config(model_config: ModelConfig, db: Session=Depends(get_db)):
    if crud.model_config.read(db, model_name=model_config.model_name, model_version=model_config.model_version, date=model_config.date):
        raise HTTPException(status.HTTP_409_CONFLICT, "A Model config with name and version for the specified date already exists")
    new_config = crud.model_config.create(db, model_config)
    if new_config:
        weights.reload()
    return new_config


@router.put("", response_model=ModelConfig, dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def update_model_config(model_config: ModelConfig, db: Session=Depends(get_db)):
    if not crud.model_config.read(db, model_name=model_config.model_name, model_version=model_config.model_version, date=model_config.date):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model config does not exist")
    updated_config = crud.model_config.update(db, model_config)
    if updated_config:
        weights.reload()
    return updated_config


@router.delete("", dependencies=[Depends(Authorize(permissions))], tags=["model_config"])
def delete_model_config(response: Response, model_config: ModelConfigDelete, db: Session=Depends(get_db)):
    if not crud.model_config.read(db, **model_config.dict()):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model config does not exist")
    deleted = crud.model_config.delete(db, model_config)
    if deleted:
        weights.reload()
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
