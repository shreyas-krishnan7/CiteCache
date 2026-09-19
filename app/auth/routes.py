"""
Sign-up / login / logout. The session is a JWT in an HttpOnly cookie, so the
browser remembers the user across visits and page scripts can't read it.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, field_validator

from app.auth.users import AuthStoreUnavailable, UsernameTaken, authenticate, create_user
from app.config import settings

COOKIE_NAME = "citecache_session"
_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,32}$")

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        v = v.strip().lower()
        if not _USERNAME_RE.match(v):
            raise ValueError("Username must be 3-32 characters: letters, digits, '_', '.' or '-'.")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        # bcrypt only uses the first 72 bytes of a password.
        if not 8 <= len(v.encode()) <= 72:
            raise ValueError("Password must be 8-72 characters long.")
        return v


class UserOut(BaseModel):
    username: str


def _secret() -> str:
    if not settings.jwt_secret or len(settings.jwt_secret) < 32:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "JWT_SECRET must be set in .env (at least 32 characters).")
    return settings.jwt_secret


def _start_session(response: Response, user: dict) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": user["id"], "username": user["username"], "iat": now,
         "exp": now + timedelta(days=settings.jwt_expire_days)},
        _secret(), algorithm="HS256",
    )
    response.set_cookie(
        COOKIE_NAME, token, max_age=settings.jwt_expire_days * 86400,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )


def current_user(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")
    try:
        claims = jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired -- please sign in again.")
    return {"id": claims["sub"], "username": claims["username"]}


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(credentials: Credentials, response: Response) -> UserOut:
    try:
        user = create_user(credentials.username, credentials.password)
    except UsernameTaken:
        raise HTTPException(status.HTTP_409_CONFLICT, "That username is already taken.")
    except AuthStoreUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    _start_session(response, user)
    return UserOut(username=user["username"])


@router.post("/login", response_model=UserOut)
def login(credentials: Credentials, response: Response) -> UserOut:
    try:
        user = authenticate(credentials.username, credentials.password)
    except AuthStoreUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password.")
    _start_session(response, user)
    return UserOut(username=user["username"])


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure)
    return response


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(current_user)) -> UserOut:
    return UserOut(username=user["username"])
