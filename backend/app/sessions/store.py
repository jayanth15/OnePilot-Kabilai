import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.sessions.models import Session

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def get_active(self, phone: str) -> Session | None:
        async with self._lock:
            session = self._sessions.get(phone)
            if session is None:
                return None
            if session.expired:
                del self._sessions[phone]
                return None
            return session

    async def start(self, phone: str, name: str = "") -> Session:
        async with self._lock:
            session = Session(phone=phone, name=name)
            self._sessions[phone] = session
        logger.info("Session started for %s", phone)
        return session

    async def end(self, phone: str) -> bool:
        async with self._lock:
            ended = self._sessions.pop(phone, None) is not None
        if ended:
            logger.info("Session ended for %s", phone)
        return ended

    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)

    async def sweep_expired(
        self,
        on_expire: Callable[[str], Awaitable[None]],
        *,
        interval_seconds: int,
    ) -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            async with self._lock:
                expired = [phone for phone, session in self._sessions.items() if session.expired]
                for phone in expired:
                    del self._sessions[phone]

            for phone in expired:
                logger.info("Session expired for %s (idle)", phone)
                try:
                    await on_expire(phone)
                except Exception:
                    logger.exception("Failed to send expiry notice to %s", phone)


session_store = SessionStore()
