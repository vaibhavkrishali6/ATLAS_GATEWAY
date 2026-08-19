from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    patient_database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


@lru_cache
def get_engine():
    return create_engine(settings.patient_database_url)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    with get_session_factory()() as session:
        yield session
