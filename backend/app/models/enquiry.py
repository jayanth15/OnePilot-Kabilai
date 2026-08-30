from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Enquiry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    enquiry_number: str = Field(unique=True, index=True)
    customer_name: str = ""
    phone: str = Field(index=True)  # normalized phone
    message: str = ""
    product_interest: str = ""
    delivery_area: str = ""
    status: str = "new"  # new, contacted, converted, closed
    source: str = "whatsapp"  # whatsapp, staff
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
