from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: str = ""  # e.g. "Fresh Milk", "Curd", "Paneer"
    unit: str = ""  # e.g. "500ml", "1kg", "packet"
    price: float = 0.0  # price in INR for the given unit
    description: str = ""
    is_available: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
