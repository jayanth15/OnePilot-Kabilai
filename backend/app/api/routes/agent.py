import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from app.agents.dairy import agent
from app.core.database import get_session
from app.core.auth import get_current_user
from app.messaging.templates import render_reply
from app.messaging.gupshup import gupshup_client
from app.models.contact import Contact
from app.models.user import User
from app.services.conversation_service import (
    add_message,
    ensure_conversation,
    get_conversation_for_contact,
    list_messages,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    contact_id: int = 1


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, session: Session = Depends(get_session)) -> ChatResponse:
    if not body.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    conversation = ensure_conversation(session, body.contact_id)
    cid = conversation.id
    assert cid is not None

    add_message(session, cid, role="user", content=body.message, direction="inbound")

    contact = session.get(Contact, body.contact_id)
    phone = contact.phone if contact else body.message
    result = await agent.run(body.message, deps=agent_deps(phone))
    reply = render_reply(result.output)

    add_message(session, cid, role="assistant", content=reply, direction="outbound")

    return ChatResponse(reply=reply)


class SendRequest(BaseModel):
    contact_id: int
    message: str


@router.post("/send")
async def send_message(
    body: SendRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Staff sends a WhatsApp message to the customer and stores it as outbound."""
    if not body.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    contact = session.get(Contact, body.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    conversation = ensure_conversation(session, contact.id)  # type: ignore[arg-type]
    cid = conversation.id
    assert cid is not None

    add_message(session, cid, role="assistant", content=body.message, direction="outbound")

    try:
        await gupshup_client.send_text(contact.phone, body.message)
    except Exception as e:
        logger.warning("Failed to send WhatsApp to %s: %s", contact.phone, e)

    return {"ok": True}


class FlagRequest(BaseModel):
    kind: str  # "complaint" | "enquiry"


@router.post("/{contact_id}/flag")
async def flag_conversation(
    contact_id: int,
    body: FlagRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Human-in-the-loop: force-classify the customer as a complaint or enquiry."""
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if body.kind == "complaint":
        from app.services.complaint_service import create_complaint
        from app.services.complaint_service import log_complaint_change

        complaint = create_complaint(
            session,
            phone=contact.phone,
            customer_name=contact.name,
            source="staff",
        )
        log_complaint_change(
            session,
            complaint.id,
            "complaint_number",
            "",
            complaint.complaint_number,
            changed_by=current_user.email,
            actor_role="admin" if current_user.is_admin else "user",
        )
        session.commit()
        return {"kind": "complaint", "reference": complaint.complaint_number}

    if body.kind == "enquiry":
        from app.services.enquiry_service import create_enquiry
        from app.services.enquiry_service import log_enquiry_change

        enquiry = create_enquiry(
            session,
            phone=contact.phone,
            customer_name=contact.name,
            source="staff",
        )
        log_enquiry_change(
            session,
            enquiry.id,
            "enquiry_number",
            "",
            enquiry.enquiry_number,
            changed_by=current_user.email,
            actor_role="admin" if current_user.is_admin else "user",
        )
        session.commit()
        return {"kind": "enquiry", "reference": enquiry.enquiry_number}

    raise HTTPException(status_code=400, detail="kind must be 'complaint' or 'enquiry'")


def agent_deps(phone: str):
    from app.agents.dairy import AgentDeps

    return AgentDeps(phone=phone)


class HistoryItem(BaseModel):
    role: str
    content: str
    direction: str
    created_at: str


@router.get("/history", response_model=list[HistoryItem])
async def get_history(contact_id: int = Query(1), session: Session = Depends(get_session)):
    conversation = get_conversation_for_contact(session, contact_id)
    if not conversation:
        return []
    msgs = list_messages(session, conversation.id)
    return [
        HistoryItem(
            role=m.role,
            content=m.content,
            direction=m.direction,
            created_at=m.created_at.isoformat(),
        )
        for m in msgs
    ]
