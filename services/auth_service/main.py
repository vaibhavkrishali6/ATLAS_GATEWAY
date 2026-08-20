"""Minimal development auth service that issues Atlas access tokens."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from services.auth_service.auth import authenticate, create_access_token, ensure_development_keys


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_development_keys()
    yield


app = FastAPI(title="Atlas Auth Service", lifespan=lifespan)


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> TokenResponse:
    role = authenticate(credentials.username, credentials.password)
    if role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(credentials.username, role))
