from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Company(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    address: str = ""
    phone: str = ""
    whatsapp_number: str = ""
    intro_message: str = ""
    ai_enabled: bool = Field(default=True)
