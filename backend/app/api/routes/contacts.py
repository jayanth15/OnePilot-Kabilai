from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc

from app.core.database import get_session
from app.models.contact import Contact
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/contacts", tags=["contacts"])


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
