from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class DeliveryArea(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # area/locality name, e.g. "Anna Nagar"
    pincode: str = ""
    city: str = "Chennai"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
