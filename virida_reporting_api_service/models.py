from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from database import Base

class Report(Base):
    __tablename__ = "report"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    filename = Column(String(50))
    folder = Column(String(50))
    owner = Column(String(50))
    owner_type=Column(String(50))
    definition = Column(MEDIUMTEXT)
    model_endpoint = Column(String(512))
    week_days = Column(String(25))
    expiry_date = Column(DateTime())
    is_active = Column(Boolean)