"""SQLAlchemy engine, session factory, and declarative base for Atlas."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from atlas.main_settings import settings


engine = create_engine(settings.atlas_database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for Atlas database models."""

