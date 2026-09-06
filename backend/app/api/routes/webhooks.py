import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.core.config import settings
from app.messaging.schemas import InboundMessage, WebhookEvent
from app.workflows.service import assistant_workflow

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_cloud_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Parse a Meta WhatsApp Cloud API webhook into inbound text messages.

    Returns a list of {phone, name, text, message_id} for type=text messages.
    Delivery-status updates (value.statuses) are ignored.
    """
    out: list[dict[str, str]] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            contacts = {c.get("wa_id", ""): c.get("profile", {}).get("name", "") for c in value.get("contacts", []) or []}
            for msg in value.get("messages", []) or []:
                if msg.get("type") != "text":
                    continue
                body = ((msg.get("text") or {}).get("body") or "").strip()
                phone = msg.get("from", "")
                if not body or not phone:
                    continue
                out.append(
                    {
                        "phone": phone,
                        "name": contacts.get(phone, ""),
                        "text": body,
                        "message_id": msg.get("id", ""),
                    }
                )
    return out


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


@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> Response:
    """Meta webhook verification handshake (GET from Meta during setup)."""
    if hub_mode == "subscribe" and hub_verify_token and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("WhatsApp Cloud webhook verified")
        return PlainTextResponse(hub_challenge, status_code=status.HTTP_200_OK)
    logger.warning("WhatsApp Cloud webhook verify failed (mode=%s)", hub_mode)
    return PlainTextResponse("Forbidden", status_code=status.HTTP_403_FORBIDDEN)


@router.post("/whatsapp")
async def whatsapp_inbound(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Receive Meta WhatsApp Cloud API events (Cloud API v26.0 shape)."""
    if payload.get("object") and payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored", "reason": "not a whatsapp event"}

    messages = parse_cloud_payload(payload)
    if not messages:
        return {"status": "ignored", "reason": "no inbound text messages"}

    from app.messaging.whatsapp_cloud import whatsapp_cloud_client

    for m in messages:
        background_tasks.add_task(
            assistant_workflow.handle_message,
            m["phone"],
            m["name"],
            m["text"],
        )
        if m["message_id"]:
            background_tasks.add_task(whatsapp_cloud_client.mark_read, m["message_id"])
    return {"status": "ok", "count": len(messages)}
