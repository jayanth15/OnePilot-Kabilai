from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.agents.dairy import AgentDeps, agent
from app.core.database import get_session
from app.messaging.templates import render_reply
from app.models.conversation import Conversation, Message
from app.models.contact import Contact

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

    conversation = session.exec(
        select(Conversation).where(Conversation.contact_id == body.contact_id).order_by(desc(Conversation.started_at))
    ).first()

    if not conversation:
        conversation = Conversation(contact_id=body.contact_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    cid = conversation.id
    assert cid is not None

    user_msg = Message(conversation_id=cid, role="user", content=body.message)
    session.add(user_msg)
    session.commit()  # release the write lock before the agent opens its own sessions

    contact = session.get(Contact, body.contact_id)
    phone = contact.phone if contact else body.message
    result = await agent.run(body.message, deps=AgentDeps(phone=phone))
    reply = render_reply(result.output)

    assistant_msg = Message(conversation_id=cid, role="assistant", content=reply)
    session.add(assistant_msg)
    conversation.last_message_at = assistant_msg.created_at
    session.commit()

    return ChatResponse(reply=reply)


class HistoryItem(BaseModel):
    role: str
    content: str


@router.get("/history", response_model=list[HistoryItem])
async def get_history(contact_id: int = Query(1), session: Session = Depends(get_session)):
    conversation = session.exec(
        select(Conversation).where(Conversation.contact_id == contact_id).order_by(desc(Conversation.started_at))
    ).first()
    if not conversation:
        return []
    msgs = session.exec(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
    ).all()
    return [HistoryItem(role=m.role, content=m.content) for m in msgs]
