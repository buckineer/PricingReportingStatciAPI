from pydantic import BaseModel


class Attribute(BaseModel):
    name: str
    property: str
    mapping: str

    class Config:
        orm_mode = True
