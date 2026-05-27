import base64
import hashlib
import hmac
import time
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings

SESSION_COOKIE_NAME = "sourcehunter_session"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=120)


class AuthUser(BaseModel):
    username: str


def create_session_token(username: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    expires_at = int(time.time()) + settings.auth_session_ttl_seconds
    payload = f"{username}|{expires_at}"
    signature = _sign(payload, settings.auth_session_secret)
    return base64.urlsafe_b64encode(f"{payload}|{signature}".encode("utf-8")).decode("ascii")


def set_session_cookie(response: Response, username: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_token(username, settings),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.auth_session_ttl_seconds,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def authenticate_credentials(username: str, password: str, settings: Settings | None = None) -> AuthUser | None:
    settings = settings or get_settings()
    username_matches = hmac.compare_digest(username, settings.auth_username)
    password_matches = hmac.compare_digest(password, settings.auth_password)
    if username_matches and password_matches:
        return AuthUser(username=settings.auth_username)
    return None


def require_authenticated_user(
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    if not settings.auth_enabled:
        return AuthUser(username=settings.auth_username)
    user = verify_session_token(session_token, settings)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def verify_session_token(token: str | None, settings: Settings | None = None) -> AuthUser | None:
    if not token:
        return None
    settings = settings or get_settings()
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        username, expires_at_text, signature = decoded.rsplit("|", 2)
        expires_at = int(expires_at_text)
    except (ValueError, UnicodeDecodeError):
        return None

    payload = f"{username}|{expires_at}"
    expected_signature = _sign(payload, settings.auth_session_secret)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    if expires_at < int(time.time()):
        return None
    if not hmac.compare_digest(username, settings.auth_username):
        return None
    return AuthUser(username=username)


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
