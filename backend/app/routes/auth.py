from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import AuthUser, LoginRequest, authenticate_credentials, clear_session_cookie, require_authenticated_user
from app.auth import set_session_cookie
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthUser)
def login(request: LoginRequest, response: Response, settings: Settings = Depends(get_settings)) -> AuthUser:
    user = authenticate_credentials(request.username, request.password, settings)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    set_session_cookie(response, user.username, settings)
    return user


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=AuthUser)
def me(user: AuthUser = Depends(require_authenticated_user)) -> AuthUser:
    return user
