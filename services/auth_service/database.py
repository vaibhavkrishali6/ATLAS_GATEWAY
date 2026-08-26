from collections.abc import Generator
from functools import lru_cache

from fastapi import HTTPException, status
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


class Settings(BaseSettings):
    auth_database_url: str

    model_config = SettingsConfigDict(env_file=".env",extra="ignore",)


settings = Settings()


@lru_cache
def get_engine():
    return create_engine(settings.auth_database_url)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
    )


def get_db() -> Generator[Session, None, None]:
    try:
        with get_session_factory()() as session:
            yield session
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication database unavailable",
        )


'''class Settings(BaseSettings):
    auth_database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()


@lru_cache
def get_engine():
    return create_engine(settings.auth_database_url)


def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
    )


def get_db() -> Generator[Session, None, None]:
    with get_session_factory()() as session:
        yield session'''