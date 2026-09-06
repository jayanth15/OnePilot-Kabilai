from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.auth import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "user"
    name: str | None = None


class MeResponse(BaseModel):
    email: str
    role: str
    name: str | None = None


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    if current_user.is_platform_admin:
        role = "admin"
    elif current_user.role in ("admin", "manager", "user"):
        role = current_user.role
    else:
        role = "user"
    return MeResponse(
        email=current_user.email,
        role=role,
        name=current_user.name,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user.email)
    if user.is_platform_admin:
        role = "admin"
    elif user.role in ("admin", "manager", "user"):
        role = user.role
    else:
        role = "user"
    return LoginResponse(
        access_token=token,
        role=role,
        name=user.name,
    )
