from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.helpers import authorize_limit_delete, Authorize
from core.static import API_RESPONSE_ERROR_MESSAGE_STRING, API_RESPONSE_ERROR_CODE_STRING, \
    ORGANIZATION_LIMIT_ALREADY_EXIST, get_error_string_by_error_code, USER_LIMIT_ALREADY_EXIST, ORGANIZATION_REQUIRED, \
    USERNAME_REQUIRED, USER_LIMIT_NOT_EXIST, ORGANIZATION_LIMIT_NOT_EXIST, LIMITED_DELETED
from schemas.permission import Permission
from schemas.limit import Limit, LimitCreate, LimitUpdate, LimitType, LimitAll, OrganizationLimit, LimitDelete, \
    StatusAndDescription
from database import get_db
import crud

router = APIRouter()
permissions = [Permission.USER_ADMINISTRATION]


@router.get("/all", response_model=LimitAll, dependencies=[Depends(Authorize(permissions))], tags=["limit"])
def get_all_limits(db: Session = Depends(get_db)):
    """
    return all of the user/organization limit
    :param db: database session
    :return: all of the user/organization limit
    """
    return LimitAll(user=crud.limit.read_all_user_limit(db),
                    organization=crud.limit.read_all_organization_limit(db))


@router.get("/user/{username}", response_model=Limit, dependencies=[Depends(Authorize(permissions, allowed_params=["username"]))], tags=["limit"])
def get_user_limit(username: str, db: Session = Depends(get_db)):
    """
    :param username: username of the user to get limit
    :param db: database session
    :return: limit of the user
    """
    # get the limit of the specified user
    limit = crud.limit.read_by_username(db=db, username=username)
    # if the limit of the specified user does not exist, raise 404 exception
    if not limit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: USER_LIMIT_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USER_LIMIT_NOT_EXIST)
        })
    return limit


@router.get("/organization/{orgname}", response_model=Limit, dependencies=[Depends(Authorize(permissions, allowed_params=["orgname"]))], tags=["limit"])
def get_organization_limit(orgname: str, db: Session = Depends(get_db)):
    """
    get limit of organization which specified with orge
    :param orgname: name of the organization to get limit
    :param db: database session
    :return: limit of the organization if the token/api_key has permission, otherwise raise exception
    """
    # get the organization limit from the database
    limit = crud.limit.read_by_orgname(db=db, orgname=orgname)
    # if the organization limit does not exist, raise 404 exception
    if not limit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: OrganizationLimit,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(OrganizationLimit)
        })
    # return organization limit
    return limit


@router.patch("/", response_model=Limit, dependencies=[Depends(Authorize(permissions))], tags=["limit"])
def update_limit(limit: LimitUpdate, db: Session = Depends(get_db)):
    """
    update user/organization limit
    :param limit: all infos to be required to update user/organization limit
    :param db: database session
    :return: updated user/organization limit if succeed, otherwise raise httpexception
    """
    # if the limit type is `user` and `username` is not specified
    if limit.limit_type == LimitType.USER_LIMIT and limit.username is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, {
            API_RESPONSE_ERROR_CODE_STRING: USERNAME_REQUIRED,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USERNAME_REQUIRED)
        })
    # if the limit type is `organization` and `orgname` is not specified
    if limit.limit_type == LimitType.ORGANIZATION_LIMIT and limit.orgname is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, {
            API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_REQUIRED,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_REQUIRED)
        })

    # update the database
    db_limit = crud.limit.update(db=db, limit=limit)
    # if the specified user/organization limit does not exist
    if db_limit is None:
        # if the limit type is `user`, raise 403 exception
        if limit.limit_type == LimitType.USER_LIMIT:
            raise HTTPException(status.HTTP_404_NOT_FOUND, {
                API_RESPONSE_ERROR_CODE_STRING: USER_LIMIT_NOT_EXIST,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USER_LIMIT_NOT_EXIST)
            })
        # if the limit type is `organization`, raise 403 exception
        elif limit.limit_type == LimitType.ORGANIZATION_LIMIT:
            raise HTTPException(status.HTTP_404_NOT_FOUND, {
                API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_LIMIT_NOT_EXIST,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_LIMIT_NOT_EXIST)
            })
    # return updated user/organization limit
    return db_limit


@router.delete("/", response_model=StatusAndDescription,
               dependencies=[Depends(Authorize(permissions)), Depends(authorize_limit_delete)], tags=["limit"])
def delete_limit(limit_delete: LimitDelete, db: Session = Depends(get_db)):
    if limit_delete.limit_type == LimitType.USER_LIMIT:
        crud.limit.delete_by_username(db=db, username=limit_delete.username)
    elif limit_delete.limit_type == LimitType.ORGANIZATION_LIMIT:
        crud.limit.delete_by_orgname(db=db, orgname=limit_delete.orgname)

    return StatusAndDescription(status=LIMITED_DELETED,
                                description=get_error_string_by_error_code(LIMITED_DELETED))


@router.post("/", response_model=Limit, dependencies=[Depends(Authorize(permissions))], tags=["limit"])
def create_limit(limit: LimitCreate, db: Session = Depends(get_db)):
    """
    :param limit: Limit of user/org to be created
    :param db: db session
    :return: Limit of user/org created
    """
    # if the limit type is user
    if limit.limit_type == LimitType.USER_LIMIT:
        # if the username is not specified
        if not limit.username:
            raise HTTPException(status.HTTP_409_CONFLICT, {
                API_RESPONSE_ERROR_CODE_STRING: USERNAME_REQUIRED,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USERNAME_REQUIRED)
            })
        # if the username is already exist in the database
        if crud.limit.read_by_username(db=db, username=limit.username):
            raise HTTPException(status.HTTP_409_CONFLICT, {
                API_RESPONSE_ERROR_CODE_STRING: USER_LIMIT_ALREADY_EXIST,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USER_LIMIT_ALREADY_EXIST)
            })
    # if the limit type is organization
    elif limit.limit_type == LimitType.ORGANIZATION_LIMIT:
        # if the orgname is not given
        if not limit.orgname:
            raise HTTPException(status.HTTP_409_CONFLICT, {
                API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_REQUIRED,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_REQUIRED)
            })
        # if the orgname is already exist
        if crud.limit.read_by_orgname(db=db, orgname=limit.orgname):
            raise HTTPException(status.HTTP_409_CONFLICT, {
                API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_LIMIT_ALREADY_EXIST,
                API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_LIMIT_ALREADY_EXIST)
            })
    return crud.limit.create(db=db, limit=limit)
