from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class ComplaintHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    complaint_id: int = Field(foreign_key="complaint.id", index=True)
    field: str = ""  # "status", "category", "note", ...
    old_value: str = ""
    new_value: str = ""
    changed_by: str = ""  # user email or "system"
    actor_role: str = ""  # "admin", "user", "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
