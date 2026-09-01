from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select, desc

from app.core.normalize import normalize_phone
from app.models.contact import Contact
from app.models.conversation import Conversation, Message


def ensure_contact(session: Session, phone: str, name: str = "") -> Contact:
    normalized = normalize_phone(phone)
    contact = session.exec(select(Contact).where(Contact.phone == normalized)).first()
    if not contact:
        contact = Contact(phone=normalized, name=name)
        session.add(contact)
        session.commit()
        session.refresh(contact)
    elif name and contact.name != name:
        contact.name = name
        session.commit()
    return contact


def ensure_conversation(session: Session, contact_id: int) -> Conversation:
    conversation = session.exec(
        select(Conversation).where(Conversation.contact_id == contact_id).order_by(desc(Conversation.started_at))
    ).first()
    if not conversation:
        conversation = Conversation(contact_id=contact_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    return conversation


def get_conversation_for_contact(session: Session, contact_id: int) -> Conversation | None:
    return session.exec(
        select(Conversation).where(Conversation.contact_id == contact_id).order_by(desc(Conversation.started_at))
    ).first()


def add_message(
    session: Session,
    conversation_id: int,
    role: str,
    content: str,
    direction: str,
) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content, direction=direction)
    session.add(msg)
    conv = session.get(Conversation, conversation_id)
    if conv:
        conv.last_message_at = msg.created_at
    session.commit()
    session.refresh(msg)
    return msg


def list_messages(session: Session, conversation_id: int) -> list[Message]:
    return list(session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    ).all())


def delete_messages_older_than(days: int = 30) -> int:
    """Delete messages older than `days` and any conversations left without messages."""
    from app.core.database import engine

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    count = 0
    with Session(engine) as session:
        old = session.exec(select(Message).where(Message.created_at < cutoff)).all()
        for m in old:
            session.delete(m)
            count += 1
        session.commit()

        # Remove conversations that no longer have any messages
        conversations = session.exec(select(Conversation)).all()
        for conv in conversations:
            has_msg = session.exec(
                select(Message).where(Message.conversation_id == conv.id)
            ).first()
            if not has_msg:
                session.delete(conv)
        session.commit()
    return count
