"""Environment-backed configuration for the Atlas gateway."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    patient_service_url: str
    doctor_service_url: str
    medicine_service_url: str
    atlas_database_url: str
    downstream_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
