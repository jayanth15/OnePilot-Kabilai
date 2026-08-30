from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = Field(default=None)
    email: str = Field(index=True, unique=True)
    password_hash: str

    is_platform_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    role: str = Field(default="user")  # "admin" | "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    company_id: UUID | None = Field(
        default=None,
        foreign_key="company.id",
        index=True,
    )

    @property
    def is_admin(self) -> bool:
        return self.role == "admin" or self.is_platform_admin
