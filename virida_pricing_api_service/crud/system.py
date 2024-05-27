import datetime as dt

from sqlalchemy.orm import Session
from models import System

def read(db: Session) -> System:
    return db.query(System).first()


def update(db: Session, system: System):
    db_system = db.query(System).first()

    if db_system is None:
        return None
    
    for key, value in system.dict(exclude_unset=True).items():
        setattr(db_system, key, value)
    db.commit()

    return db_system

