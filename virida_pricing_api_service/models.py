from sqlalchemy import Column, String, Date, DateTime, Integer, Float, Time, Enum, JSON
from sqlalchemy.dialects.mysql import MEDIUMTEXT, DOUBLE
from database import Base
from schemas.standardized_instrument import InstrumentType, CurrencyType


class Benchmark(Base):
    __tablename__ = 'benchmark'

    date = Column('date', Date(), nullable=False, primary_key=True)
    name = Column('name', String(20), nullable=False, primary_key=True)
    type = Column('type', String(20), nullable=False, primary_key=True)
    symbol = Column('symbol', String(20), nullable=False, primary_key=True)
    expiry_date = Column('expiry_date', Date(), nullable=True)
    currency = Column('currency', String(3), nullable=True)
    open = Column('open', Float(), nullable=True)
    high = Column('high', Float(), nullable=True)
    low = Column('low', Float(), nullable=True)
    close = Column('close', Float(), nullable=False)
    volume = Column('volume', Integer(), nullable=True)
    timestamp = Column('timestamp', DateTime(), nullable=True)


class BenchmarkIndex(Base):
    __tablename__ = 'benchmark_index'

    date = Column('date', Date(), nullable=False, primary_key=True)
    benchmark = Column('benchmark', String(20), nullable=False, primary_key=True)
    value = Column('value', DOUBLE(asdecimal=False), nullable=False)


class Forex(Base):
    __tablename__ = 'forex'

    date = Column(Date(), nullable=False, primary_key=True)
    currency = Column(String(3), nullable=False, primary_key=True)
    timestamp = Column(DateTime(), nullable=True)
    close = Column(Float(), nullable=True)


class InterestRate(Base):
    __tablename__ = 'interest_rate'

    date = Column('date', Date(), nullable=False, primary_key=True)
    currency = Column(String(3), nullable=False, primary_key=True)
    tenor = Column('tenor', String(3), nullable=False, primary_key=True)
    rate = Column('rate', Float(), nullable=True)
    timestamp = Column('timestamp', DateTime(), nullable=True)


class Request(Base):
    __tablename__ = 'request'

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50), index=True)
    model_name = Column(String(256), index=True)
    username = Column(String(50), index=True)
    orgname = Column(String(50), index=True)
    body = Column(MEDIUMTEXT)
    response = Column(MEDIUMTEXT)
    time = Column(DateTime(), index=True)
    projects_requested_count = Column(Integer(), index=True)
    projects_priced_count = Column(Integer(), index=True)


class Limit(Base):
    __tablename__ = 'pricing_limit'
    id = Column(Integer, primary_key=True, index=True)
    limit_type = Column(String(50), index=True)
    username = Column(String(50), index=True)
    orgname = Column(String(256), index=True)
    daily = Column(Integer(), index=True)
    monthly = Column(Integer(), index=True)
    lifetime = Column(Integer(), index=True)
    lifetime_reset_date = Column(DateTime(), index=True)


class BlockedAPIKey(Base):
    __tablename__ = 'apikey_blacklist'
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(1024))


class ModelConfig(Base):
    __tablename__ = 'model_config'
    date = Column(Date, primary_key=True, index=True)
    model_name = Column(String(256), primary_key=True, index=True)
    model_version = Column(String(256), primary_key=True, index=True)
    config = Column(JSON, index=True)


class System(Base):
    __tablename__ = 'system'
    date = Column(Date, primary_key=True, index=True)


class StandardizedInstrument(Base):
    __tablename__ = 'standardized_instrument'

    instrument = Column(String(50), primary_key=True, index=True)
    source = Column(String(50), primary_key=True, index=True)
    date = Column(Date, primary_key=True, index=True)
    type = Column(Enum(InstrumentType), primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    currency = Column(Enum(CurrencyType), index=True)
    price = Column(Float, index=True)
    volume = Column(Integer, index=True)


class PricingConfig(Base):
    __tablename__ = 'pricing_config'

    date = Column(Date, primary_key=True, nullable=False, index=True)
    key = Column(String(50), primary_key=True, nullable=False, index=True)
    value = Column(JSON, nullable=False, default={}, index=True)


class InterestCurve(Base):
    __tablename__ = 'interest_curve'

    date = Column(Date, primary_key=True, nullable=False, index=True)
    curve = Column(String(20), primary_key=True, index=True)
    value = Column(JSON, index=True)