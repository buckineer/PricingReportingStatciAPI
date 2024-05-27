from sqlalchemy.orm import Session
from models import ModelConfig
from schemas.model_config import ModelConfigDelete


def read(db: Session, **kwargs):
    query = db.query(ModelConfig)

    if kwargs:
        query = query.filter_by(**kwargs)

    return query.all()


def create(db: Session, model_config: ModelConfig):
    db_model_config = ModelConfig(**model_config.dict())
    db.add(db_model_config)
    db.commit()
    db.refresh(db_model_config)
    return db_model_config


def update(db: Session, model_config: ModelConfig) -> ModelConfig:
    db_model_config = db.query(ModelConfig).filter_by(
        date=model_config.date,
        model_name=model_config.model_name,
        model_version=model_config.model_version
    ).first()

    if not db_model_config:
        return None

    for key, value in model_config.dict(exclude_unset=True).items():
        setattr(db_model_config, key, value)
    
    db.commit()
    return db_model_config


def delete(db: Session, model_config: ModelConfigDelete):
    db_model_config = db.query(ModelConfig).filter_by(**model_config.dict()).first()

    if not db_model_config:
        return None

    db.delete(db_model_config)
    db.commit()

    return True
