from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Contact(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    phone: str = Field(unique=True, index=True)
    name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
