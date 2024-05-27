from sqlalchemy.orm import Session
from database import get_db
import crud


class AttributeContainer():
    """ Singleton implementation """

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            db: Session = next(get_db())

            cls.__instance = super(AttributeContainer, cls).__new__(cls)

            # dictionary initialization
            cls.__instance.standard = dict()
            cls.__instance.vintage = dict()
            cls.__instance.project = dict()
            cls.__instance.country = dict()
            cls.__instance.sdg = dict()
            cls.__instance.region = dict()
            cls.__instance.subregion = dict()

            versions = crud.static.get_all_versions(db)
            for version in versions:
                cls.__instance.standard[version] = crud.static.read(db, "standard", version)
                cls.__instance.vintage[version] = crud.static.read(db, "vintage", version)
                cls.__instance.project[version] = crud.static.read(db, "project", version)
                cls.__instance.country[version] = crud.static.read(db, "country", version)
                cls.__instance.sdg[version] = crud.static.read(db, "sdg", version)
                cls.__instance.region[version] = crud.static.read(db, "region", version)
                cls.__instance.subregion[version] = crud.static.read(db, "subregion", version)

        return cls.__instance

    def __getitem__(self, key):
        return getattr(self, key)


attributes = AttributeContainer()
