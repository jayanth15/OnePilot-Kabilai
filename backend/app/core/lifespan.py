import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core.config import settings
from app.messaging.gupshup import gupshup_client
from app.sessions.store import session_store
from app.seed import init_data
from app.workflows.service import assistant_workflow


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_data()
    sweeper = asyncio.create_task(
        session_store.sweep_expired(
            assistant_workflow.notify_expired,
            interval_seconds=settings.session_sweep_seconds,
        ),
        name="expired-session-sweeper",
    )
    try:
        yield
    finally:
        sweeper.cancel()
        with suppress(asyncio.CancelledError):
            await sweeper
        await gupshup_client.close()
