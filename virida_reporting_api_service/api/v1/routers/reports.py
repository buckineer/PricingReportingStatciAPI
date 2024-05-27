from typing import List
from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlalchemy.orm import Session

from schemas.report import Report, ReportCreate, ReportUpdate
from schemas.auth import Auth, AuthType
from database import get_db
from api.helpers import authenticate, authorize_is_admin
import crud

ACCESS_FORBIDDEN = "Report access is forbidden"
UNAUTHORIZED = "Wrong form of authentication used. Make sure to use authentication that permits reading user reports"
DOES_NOT_EXIST = "Report does not exist"

router = APIRouter()

@router.get("/all", response_model=List[Report], dependencies=[Depends(authorize_is_admin)])
def get_all_reports(db: Session=Depends(get_db)):
    return crud.report.read_all(db=db)

@router.get("/user/{username}", response_model=List[Report])
def get_owner_reports(username: str, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    if not auth.is_admin:
        if auth.type == AuthType.organization:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
        if auth.username != username:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
    return crud.report.read_by_owner(db=db, owner=username, owner_type=AuthType.user)

@router.get("/organization/{orgname}", response_model=List[Report])
def get_owner_reports(orgname: str, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    if not auth.is_admin:
        if auth.type == AuthType.user and auth.orgname != orgname:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
        if auth.type == AuthType.organization and auth.name != orgname:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
    return crud.report.read_by_owner(db=db, owner=orgname, owner_type=AuthType.organization)

@router.post("/", response_model=Report)
def create_report(report: ReportCreate, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    if not auth.is_admin:
        if auth.type != report.owner_type:
            if auth.type == AuthType.organization:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
            elif auth.orgname != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
        else:
            if auth.type == AuthType.organization:
                if auth.orgname != report.owner:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
            elif auth.username != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
    return crud.report.create(db=db, report=report)

@router.patch("/{id}", response_model=Report)
def update_report(id: int, report: ReportUpdate, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    db_report: Report = crud.report.read(db=db, id=id)

    if not auth.is_admin:
        if db_report == None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

        if auth.type != db_report.owner_type:
            if auth.type == AuthType.organization:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
            elif auth.orgname != report.owner or auth.orgname != db_report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
        else:
            if auth.type == AuthType.organization:
                if auth.orgname != report.owner or auth.orgname != db_report.owner:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
            elif auth.username != report.owner or auth.username != db_report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

    if db_report == None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, DOES_NOT_EXIST)

    return crud.report.update(db=db, id=id, report=report)
    
@router.get("/{id}/deactivate", response_model=Report)
def deactivate_report(id: int, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    report: Report = crud.report.read(db=db, id=id)

    if not auth.is_admin:
        if report == None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

        if auth.type != report.owner_type:
            if auth.type == AuthType.organization:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
            elif auth.orgname != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
        else:
            if auth.type == AuthType.organization:
                if auth.orgname != report.owner:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
            elif auth.username != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

    if report == None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, DOES_NOT_EXIST)

    return crud.report.deactivate(db=db, id=id)

@router.delete("/{id}")
def delete_report(response: Response, id: int, db: Session=Depends(get_db), auth: Auth=Depends(authenticate)):
    report: Report = crud.report.read(db=db, id=id)

    if not auth.is_admin:
        if report == None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

        if auth.type != report.owner_type:
            if auth.type == AuthType.organization:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, UNAUTHORIZED)
            elif auth.orgname != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
        else:
            if auth.type == AuthType.organization:
                if auth.orgname != report.owner:
                    raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)
            elif auth.username != report.owner:
                raise HTTPException(status.HTTP_403_FORBIDDEN, ACCESS_FORBIDDEN)

    if report == None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, DOES_NOT_EXIST)

    crud.report.delete(db=db, id=id)

    response.status_code = status.HTTP_204_NO_CONTENT
    return response