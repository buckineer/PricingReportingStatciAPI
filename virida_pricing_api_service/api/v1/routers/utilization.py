from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.helpers import Authorize
from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    get_error_string_by_error_code, ORGANIZATION_LIMIT_NOT_EXIST, USER_LIMIT_NOT_EXIST
from schemas.limit import UserLimit, OrganizationLimit
from schemas.utilization import Utilization, UtilizationWithLifetime, PricingUtilizationAll, UserPricingUtilization, \
    OrganizationPricingUtilization
from schemas.permission import Permission
from database import get_db
from helpers.database import get_user_daily_utilization, get_user_lifetime_utilization, get_user_monthly_utilization, \
    get_organization_daily_utilization, get_organization_monthly_utilization, get_organization_lifetime_utilization
import crud

router = APIRouter()
permissions = [Permission.USER_ADMINISTRATION]


@router.get("/all", response_model=PricingUtilizationAll, dependencies=[Depends(Authorize(permissions))], tags=["utilization"])
def get_all_utilization(db: Session = Depends(get_db)):
    user_pricing_utilization: List[UserPricingUtilization] = [
        UserPricingUtilization(username=limit.username,
                               daily=Utilization(
                                   limit=limit.daily,
                                   utilization=get_user_daily_utilization(db=db, username=limit.username)
                               ),
                               monthly=Utilization(
                                   limit=limit.monthly,
                                   utilization=get_user_monthly_utilization(db=db, username=limit.username)
                               ),
                               lifetime=UtilizationWithLifetime(
                                   limit=limit.lifetime,
                                   utilization=get_user_lifetime_utilization(db=db, username=limit.username,
                                                                             reset_date=limit.lifetime_reset_date),
                                   lifetime_reset_date=limit.lifetime_reset_date))
        for limit in crud.limit.read_all_user_limit(db=db)
    ]

    organization_pricing_utilization: List[OrganizationPricingUtilization] = [
        OrganizationPricingUtilization(orgname=limit.orgname,
                                       daily=Utilization(
                                           limit=limit.daily,
                                           utilization=get_organization_daily_utilization(
                                               db=db, orgname=limit.orgname)
                                       ),
                                       monthly=Utilization(
                                           limit=limit.monthly,
                                           utilization=get_organization_monthly_utilization(
                                               db=db, orgname=limit.orgname)
                                       ),
                                       lifetime=UtilizationWithLifetime(
                                           limit=limit.lifetime,
                                           utilization=get_organization_lifetime_utilization(
                                               db=db, orgname=limit.orgname, reset_date=limit.lifetime_reset_date),
                                           lifetime_reset_date=limit.lifetime_reset_date
                                       ))

        for limit in crud.limit.read_all_organization_limit(db=db)
    ]

    return PricingUtilizationAll(user=user_pricing_utilization, organization=organization_pricing_utilization)


@router.get("/user/{username}", response_model=UserPricingUtilization, dependencies=[Depends(Authorize(permissions, allowed_params=["username"]))], tags=["utilization"])
def get_user_utilization(username: str, db: Session = Depends(get_db)):
    limit: UserLimit = crud.limit.read_by_username(db=db, username=username)
    if not limit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: USER_LIMIT_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(USER_LIMIT_NOT_EXIST)
        })

    return UserPricingUtilization(
        username=limit.username,
        daily=Utilization(
            limit=limit.daily,
            utilization=get_user_daily_utilization(db=db, username=limit.username)
        ),
        monthly=Utilization(
            limit=limit.monthly,
            utilization=get_user_monthly_utilization(db=db, username=limit.username)
        ),
        lifetime=UtilizationWithLifetime(
            limit=limit.lifetime,
            utilization=get_user_lifetime_utilization(db=db, username=limit.username,
                                                      reset_date=limit.lifetime_reset_date),
            lifetime_reset_date=limit.lifetime_reset_date
        )
    )


@router.get("/organization/{orgname}", response_model=OrganizationPricingUtilization, dependencies=[Depends(Authorize([], allowed_params=["orgname"]))], tags=["utilization"])
def get_organization_utilization(orgname: str, db: Session = Depends(get_db)):
    limit: OrganizationLimit = crud.limit.read_by_orgname(db=db, orgname=orgname)
    if not limit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {
            API_RESPONSE_ERROR_CODE_STRING: ORGANIZATION_LIMIT_NOT_EXIST,
            API_RESPONSE_ERROR_MESSAGE_STRING: get_error_string_by_error_code(ORGANIZATION_LIMIT_NOT_EXIST)
        })

    return OrganizationPricingUtilization(
        orgname=limit.orgname,
        daily=Utilization(
            limit=limit.daily,
            utilization=get_organization_daily_utilization(db=db, orgname=limit.orgname)
        ),
        monthly=Utilization(
            limit=limit.monthly,
            utilization=get_organization_monthly_utilization(db=db, orgname=limit.orgname)
        ),
        lifetime=UtilizationWithLifetime(
            limit=limit.lifetime,
            utilization=get_organization_lifetime_utilization(db=db, orgname=limit.orgname,
                                                              reset_date=limit.lifetime_reset_date),
            lifetime_reset_date=limit.lifetime_reset_date
        )
    )
