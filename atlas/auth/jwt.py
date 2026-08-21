"""RS256 access-token validation for Atlas proxy routes."""

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from atlas.main_settings import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
        """Identity extracted from a validated access token."""
        user_id: str
        role: str
         

async def require_authenticated_user(
        request: Request,
        credentials:HTTPAuthorizationCredentials | None = Depends(bearer_scheme),) -> AuthenticatedUser:
    
    """Validate a Bearer token and retain its identity on the request state."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        public_key = settings.auth_public_key_path.read_text(encoding="utf-8")
        
        claims = jwt.decode(
                credentials.credentials,
                public_key,
                algorithms=["RS256"],
                issuer=settings.jwt_issuer,
                options={"require": ["exp", "iss", "sub", "role"]},)
        
        user = AuthenticatedUser(user_id=str(claims["sub"]), role=str(claims["role"]))
    except (OSError, jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise _unauthorized() from None

    request.state.user = user
    return user


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
