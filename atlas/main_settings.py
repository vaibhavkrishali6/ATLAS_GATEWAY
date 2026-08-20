"""Environment-backed configuration for the Atlas gateway."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    patient_service_url: str
    doctor_service_url: str
    medicine_service_url: str
    jwt_issuer: str
    auth_public_key_path: Path
    jwt_expiration_minutes: int = 60
    atlas_database_url: str
    downstream_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
