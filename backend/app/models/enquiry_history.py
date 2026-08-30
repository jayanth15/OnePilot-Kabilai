from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class EnquiryHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    enquiry_id: int = Field(foreign_key="enquiry.id", index=True)
    field: str = ""  # "status", "customer_name", ... or "note"
    old_value: str = ""
    new_value: str = ""
    changed_by: str = ""  # user email or "system"
    actor_role: str = ""  # "admin", "user", "system"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
