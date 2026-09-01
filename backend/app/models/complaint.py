from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Complaint(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    complaint_number: str = Field(unique=True, index=True)
    customer_name: str = ""
    phone: str = Field(index=True)  # normalized phone
    message: str = ""
    category: str = ""  # delivery, quality, product, billing, other
    related_product: str = ""
    status: str = "pending"  # pending, in_progress, resolved, closed
    source: str = "whatsapp"  # whatsapp, staff
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
