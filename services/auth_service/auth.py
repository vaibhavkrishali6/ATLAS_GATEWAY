"""Development credentials and RS256 token creation."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.auth_service.models import User


class AuthSettings(BaseSettings):
    jwt_issuer: str
    jwt_expiration_minutes: int = 60
    auth_private_key_path: Path
    auth_public_key_path: Path

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AuthSettings()




def ensure_development_keys() -> None:
    """Create a local key pair once when no development keys are present."""
    if settings.auth_private_key_path.exists() and settings.auth_public_key_path.exists():
        return

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings.auth_private_key_path.parent.mkdir(parents=True, exist_ok=True)
    settings.auth_public_key_path.parent.mkdir(parents=True, exist_ok=True)
    settings.auth_private_key_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    settings.auth_public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def authenticate(db: Session,username: str,password: str,) -> User | None:
    """Authenticate a user by username and password."""
    statement = select(User).where(User.username == username)
    user = db.scalar(statement)

    if (user is None or not user.is_active or user.password_hash != password):
        return None
    
    return user


def create_access_token(user_id: str, role: str) -> str:
    """Sign a short-lived RS256 JWT using the auth service's private key."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iss": settings.jwt_issuer,
        "exp": now + timedelta(minutes=settings.jwt_expiration_minutes),
    }
    private_key = settings.auth_private_key_path.read_text(encoding="utf-8")
    return jwt.encode(payload, private_key, algorithm="RS256")
