from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    type: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class Sender(BaseModel):
    phone: str = ""
    name: str = ""


class InboundMessage(BaseModel):
    id: str = ""
    source: str = ""
    type: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    sender: Sender = Field(default_factory=Sender)

    @property
    def text(self) -> str:
        return str(self.payload.get("text", "")).strip()

    @property
    def destination(self) -> str:
        return self.source or self.sender.phone
