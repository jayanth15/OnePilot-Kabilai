import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from pydantic_ai.messages import ModelMessage

from app.core.config import settings


@dataclass
class Session:
    phone: str
    name: str = ""
    history: list[ModelMessage] = field(default_factory=list)
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def expired(self) -> bool:
        idle = datetime.now(timezone.utc) - self.last_activity
        return idle > timedelta(minutes=settings.session_idle_minutes)

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)
