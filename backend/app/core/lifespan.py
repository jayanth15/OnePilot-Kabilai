import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db
from app.messaging.gupshup import gupshup_client
from app.sessions.store import session_store
from app.workflows.service import assistant_workflow


async def _retention_sweep(interval_seconds: int = 3600) -> None:
    """Delete chat messages older than 30 days (configurable) once per hour."""
    from app.services.conversation_service import delete_messages_older_than

    retention_days = getattr(settings, "chat_retention_days", 30)
    while True:
        try:
            deleted = delete_messages_older_than(retention_days)
            if deleted:
                import logging

                logging.getLogger(__name__).info("Retention: deleted %d messages >%d days", deleted, retention_days)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Retention sweep failed")
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Create missing tables only — do NOT seed data. Seed once manually via
    # `python -m app.seed` (or manage the DB directly).
    init_db()
    sweeper = asyncio.create_task(
        session_store.sweep_expired(
            assistant_workflow.notify_expired,
            interval_seconds=settings.session_sweep_seconds,
        ),
        name="expired-session-sweeper",
    )
    retention = asyncio.create_task(_retention_sweep(), name="chat-retention-sweeper")
    try:
        yield
    finally:
        sweeper.cancel()
        retention.cancel()
        with suppress(asyncio.CancelledError):
            await sweeper
            await retention
        await gupshup_client.close()
