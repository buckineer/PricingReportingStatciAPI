from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import config

class Database():
    """ Singleton implementation of the database connection """

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Database, cls).__new__(cls)
            # https://stackoverflow.com/questions/16341911/sqlalchemy-error-mysql-server-has-gone-away
            #cls.__instance.engine = create_engine(config.DATABASE_URL, pool_recycle=config.DATABASE_WAIT_TIME - 100)
            cls.__instance.engine = create_engine(config.DATABASE_URL, pool_recycle=config.DATABASE_WAIT_TIME - 3600, pool_pre_ping=True)
            cls.__instance.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.__instance.engine)
            cls.__instance.Base = declarative_base()
    
        return cls.__instance


database = Database()
Base = database.Base
SessionLocal = database.SessionLocal

class DatabaseContextManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def get_db():
    with DatabaseContextManager() as session:
        yield session