from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    contact_id: int = Field(foreign_key="contact.id", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str  # "user" (customer) or "assistant" (us/AI/staff)
    content: str
    direction: str = "inbound"  # "inbound" (customer) or "outbound" (us)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
