from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.auth import require_admin
from app.core.security import hash_password, verify_password
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str
    role: str = "user"
    is_active: bool = True


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = None


def _serialize(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": "admin" if user.is_admin else "user",
        "is_active": user.is_active,
        "is_platform_admin": user.is_platform_admin,
    }


@router.get("")
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    users = session.exec(select(User).order_by(User.created_at)).all()
    return [_serialize(u) for u in users]


@router.post("")
def create_user(
    body: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'user'")
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=body.is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _serialize(user)


@router.patch("/{user_id}")
def update_user(
    user_id: UUID,
    body: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        if body.role not in ("admin", "user"):
            raise HTTPException(status_code=400, detail="role must be 'admin' or 'user'")
        user.role = body.role
    if body.name is not None:
        user.name = body.name
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password:
        user.password_hash = hash_password(body.password)
    session.commit()
    session.refresh(user)
    return _serialize(user)


@router.get("/{user_id}")
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize(user)
