from uuid import UUID
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session


from services.auth_service.auth import (
    authenticate,
    create_access_token,
    ensure_development_keys,
)
from services.auth_service.database import get_db,get_engine
from services.auth_service.models import User ,Base 


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    
class UserStatusUpdate(BaseModel):
    is_active: bool

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_development_keys()
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(title="Atlas Auth Service", lifespan=lifespan)


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db,credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(str(user.id), user.role))



@app.post("/auth/register")
async def register(credentials: RegisterRequest,db: Session = Depends(get_db),):
    
    existing_user = db.scalar(select(User).where(User.username == credentials.username))

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = User(
        username=credentials.username,
        password_hash=credentials.password,  # temporary development implementation
        role=credentials.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    
    

@app.patch("/auth/users/{user_id}/status")
async def update_user_status(
        user_id: UUID,
        update: UserStatusUpdate,
        db: Session = Depends(get_db),):
    
    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = update.is_active

    db.commit()
    db.refresh(user)

    return {
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
    }