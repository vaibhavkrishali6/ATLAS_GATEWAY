"""Small, reusable gateway-level role authorization dependencies."""
from fastapi import Depends, HTTPException, Request, status
from atlas.auth.jwt import AuthenticatedUser, require_authenticated_user

SERVICE_ROLES: dict[str, frozenset[str]] = {
    "doctors": frozenset({"doctor", "admin"}),
    "patients": frozenset({"patient", "doctor", "admin"}),
    "medicines": frozenset({"patient", "doctor", "admin"}),
}



async def require_service_access(
        service: str,
        user: AuthenticatedUser = Depends(require_authenticated_user),) -> AuthenticatedUser:
    
    allowed_roles = SERVICE_ROLES.get(service)
    if allowed_roles is None:
        return user
    
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this service",
        )

    return user



