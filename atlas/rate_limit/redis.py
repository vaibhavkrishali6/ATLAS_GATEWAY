from functools import lru_cache

import redis
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_url: str 

    model_config = SettingsConfigDict(env_file=".env",extra="ignore",)


settings = Settings()


@lru_cache
def get_redis() -> redis.Redis:
    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )