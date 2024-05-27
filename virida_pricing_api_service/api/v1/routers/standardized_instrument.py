from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.exceptions import HTTPException

import crud
from api.helpers import Authorize
from core.static import API_RESPONSE_ERROR_CODE_STRING, API_RESPONSE_ERROR_MESSAGE_STRING, \
    get_error_string_by_error_code, INSTRUMENT_KEY_CONFLICT
from database import get_db
from schemas.standardized_instrument import StandardizedInstrument, StandardizedInstrumentCreate, StandardizedInstrumentUpdateResponse, InstrumentDeleteResponse, \
    StandardizedInstrumentCreateResponse
from schemas.permission import Permission

router = APIRouter()
permissions = [Permission.ADVANCED]


@router.get("", response_model=List[StandardizedInstrument], dependencies=[Depends(Authorize(permissions))],
            tags=["standardized_instrument"])
def get_instrument(start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = Depends(get_db)):
    return crud.standardized_instrument.read_instruments_by_period(start_date=start_date, end_date=end_date, db=db)


@router.post("", response_model=StandardizedInstrumentCreateResponse, dependencies=[Depends(Authorize(permissions))],
             tags=["standardized_instrument"])
def create_instrument(instrument_creates: List[StandardizedInstrumentCreate], db: Session = Depends(get_db)):
    succeed_instrument: List[StandardizedInstrument] = []
    failed_instrument_create: List[StandardizedInstrumentCreate] = []

    for instrument_create in instrument_creates:
        db_instrument: StandardizedInstrument = crud.standardized_instrument.read(instrument_base=instrument_create, db=db)

        if db_instrument is not None:
            failed_instrument_create.append(instrument_create)
        else:
            db_instrument = crud.standardized_instrument.create(instrument_create=instrument_create, db=db)
            if db_instrument is None:
                failed_instrument_create.append(instrument_create)
            else:
                succeed_instrument.append(db_instrument)

    return StandardizedInstrumentCreateResponse(
        success=succeed_instrument,
        error=failed_instrument_create
    )


@router.patch("", response_model=StandardizedInstrumentUpdateResponse, dependencies=[Depends(Authorize(permissions))],
              tags=["standardized_instrument"])
def update_instrument(instruments: List[StandardizedInstrument], db: Session = Depends(get_db)):
    succeed_instruments, failed_instruments = crud.standardized_instrument.update(instruments=instruments, db=db)
    return StandardizedInstrumentUpdateResponse(
        success=succeed_instruments,
        error=failed_instruments
    )


@router.delete("", response_model=InstrumentDeleteResponse, dependencies=[Depends(Authorize(permissions))],
               tags=["standardized_instrument"])
def delete_instrument(instruments: List[StandardizedInstrument], db: Session = Depends(get_db)):
    succeed_instruments, failed_instruments = crud.standardized_instrument.delete(instruments=instruments, db=db)
    return InstrumentDeleteResponse(
        success=succeed_instruments,
        error=failed_instruments
    )
