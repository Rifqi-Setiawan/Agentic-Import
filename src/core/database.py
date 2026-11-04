from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models.entities import Base

# Sync Engine for Migrations, CLI, Workers, & Seeds
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_engine():
    global engine
    if engine.url != make_url(settings.DATABASE_URL):
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        SessionLocal.configure(bind=engine)
    return engine


def get_db():
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
