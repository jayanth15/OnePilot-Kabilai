from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.core.auth import get_current_user
from app.core.database import get_session
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.conversation_service import ensure_contact, ensure_conversation

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactEnsure(BaseModel):
    phone: str
    name: str = ""


@router.post("/ensure")
def ensure_contact_route(
    body: ContactEnsure,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Ensure a Contact + Conversation exists for a phone (e.g. manual enquiry).

    Lets staff message a customer who has never messaged on WhatsApp yet.
    """
    contact = ensure_contact(session, body.phone, body.name or "")
    conversation = ensure_conversation(session, contact.id)  # type: ignore[arg-type]
    return {"id": contact.id, "phone": contact.phone, "name": contact.name, "conversation_id": conversation.id}


@router.get("")
async def list_contacts(session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact).order_by(desc(Contact.created_at))).all()
    result = []
    for c in contacts:
        conv = session.exec(
            select(Conversation).where(Conversation.contact_id == c.id).order_by(desc(Conversation.last_message_at))
        ).first()
        last_msg = ""
        if conv:
            msg = session.exec(
                select(Message).where(Message.conversation_id == conv.id).order_by(desc(Message.created_at))
            ).first()
            if msg:
                last_msg = msg.content
        result.append({
            "id": c.id,
            "phone": c.phone,
            "name": c.name,
            "last_message": last_msg[:80] if last_msg else "",
            "created_at": c.created_at.isoformat(),
        })
    return result
