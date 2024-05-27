from sqlalchemy.orm import Session

from models import Attribute


def read(db: Session, name: str, version: int) -> [Attribute]:
    return db.query(Attribute).filter_by(name=name).filter_by(version=version).all()


def get_all_versions(db: Session) -> [int]:
    results = db.query(Attribute.version).distinct().all()
    return [r[0] for r in results]
