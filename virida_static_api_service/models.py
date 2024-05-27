from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from database import Base


class Attribute(Base):
    __tablename__ = "attribute"

    name = Column(String(50), primary_key=True, index=True)
    property = Column(String(50), primary_key=True, index=True)
    version = Column(Integer, primary_key=True, index=True)
    mapping = Column(String(256), index=True)


class BlockedAPIKey(Base):
    __tablename__ = 'apikey_blacklist'
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(1024))
