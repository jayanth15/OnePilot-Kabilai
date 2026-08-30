import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import ValidationError

from app.messaging.schemas import InboundMessage, WebhookEvent
from app.workflows.service import assistant_workflow

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/gupshup")
async def gupshup_webhook(
    event: WebhookEvent,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    logger.info("Gupshup webhook type=%s", event.type)

    if event.type != "message":
        return {"status": "ignored", "reason": f"event type '{event.type}'"}

    try:
        message = InboundMessage.model_validate(event.payload)
    except ValidationError:
        logger.exception("Invalid Gupshup message payload")
        return {"status": "ignored", "reason": "invalid message payload"}

    if message.type != "text":
        return {"status": "ignored", "reason": f"message type '{message.type}'"}
    if not message.text or not message.destination:
        return {"status": "ignored", "reason": "empty text or destination"}

    background_tasks.add_task(
        assistant_workflow.handle_message,
        message.destination,
        message.sender.name,
        message.text,
    )
    return {"status": "ok"}
