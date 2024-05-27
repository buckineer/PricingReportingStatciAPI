from typing import List
from sqlalchemy.orm import Session
from schemas.attribute import Attribute
import crud


def test_read_attribute(db: Session, attribute_name: str):
    attributes_db: List[Attribute] = crud.static.read(db, attribute_name, 2)
    for attribute in attributes_db:
        assert attribute.name == attribute_name
