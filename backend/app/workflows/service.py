import logging

from sqlmodel import Session, select

from app.agents.dairy import AgentDeps, agent, normalize_output
from app.core.config import settings
from app.core.database import engine
from app.messaging.gupshup import gupshup_client
from app.messaging.templates import render_reply
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.sessions.models import Session as ChatSession
from app.sessions.store import session_store
from app.workflows.models import WorkflowSummary

logger = logging.getLogger(__name__)

ACTIVATION_PHRASES = {"kabilai ai"}
DEACTIVATION_PHRASES = {"stop ai", "stopai", "end ai", "end chat", "bye ai"}

GREETING = (
    "\U0001f9e0 *{brand} on WhatsApp!* Namaste {name}, I can help you pick dairy products, "
    "check prices, and confirm delivery. Say *stop ai* to reach a human. "
    "I'll auto-sleep after {mins} min idle."
)
GOODBYE = "\U0001f44b *AI mode off.* You're back with the human now. Say *kabilai ai* to wake me again."
EXPIRED = "\u23f1\ufe0f *AI session ended* after {mins} min idle. Say *kabilai ai* anytime to chat again."


def _ensure_contact(phone: str, name: str) -> int:
    with Session(engine) as session:
        contact = session.exec(select(Contact).where(Contact.phone == phone)).first()
        if not contact:
            contact = Contact(phone=phone, name=name)
            session.add(contact)
            session.commit()
            session.refresh(contact)
            logger.info("Created new contact: %s (%s)", phone, name)
        elif name and contact.name != name:
            contact.name = name
            session.commit()
        return contact.id  # type: ignore[return-value]


def _save_message(conversation_id: int, role: str, content: str) -> None:
    with Session(engine) as session:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        session.add(msg)
        conv = session.get(Conversation, conversation_id)
        if conv:
            conv.last_message_at = msg.created_at
        session.commit()


class AssistantWorkflow:
    summary = WorkflowSummary(
        id="whatsapp-dairy-assistant",
        name="WhatsApp Dairy Assistant",
        description="Opt-in conversational assistant for product info, pricing, delivery, and enquiries.",
        trigger="Gupshup inbound text webhook",
        status="active",
        tools=["dairy"],
    )

    async def notify_expired(self, phone: str) -> None:
        await gupshup_client.send_text(phone, EXPIRED.format(mins=settings.session_idle_minutes))

    async def _run_agent(self, session: ChatSession, text: str, phone: str) -> str:
        async with session.lock:
            prompt = f"{text}\n\n(User name: {session.name})" if session.name else text
            result = await agent.run(
                prompt,
                deps=AgentDeps(phone=phone),
                message_history=session.history or None,
            )
            session.history = result.all_messages()[-settings.session_max_history :]
            return render_reply(result.output)

    async def handle_message(self, destination: str, sender_name: str, text: str) -> None:
        with Session(engine) as session:
            from app.services.catalog import get_company_info

            ai_enabled = get_company_info(session).get("ai_enabled", True)

        if not ai_enabled:
            logger.info("AI assistant disabled; ignoring message from %s", destination)
            return

        normalized = " ".join(text.lower().split())
        chat_session = await session_store.get_active(destination)
        contact_id = _ensure_contact(destination, sender_name)

        with Session(engine) as db_session:
            conversation = db_session.exec(
                select(Conversation).where(Conversation.contact_id == contact_id).order_by(Conversation.started_at.desc())
            ).first()
            if not conversation:
                conversation = Conversation(contact_id=contact_id)
                db_session.add(conversation)
                db_session.commit()
                cid = conversation.id
            else:
                cid = conversation.id

            # Add a new customer to the enquiries CRM on their first message.
            from app.services.enquiry_service import ensure_enquiry

            customer = db_session.get(Contact, contact_id)
            ensure_enquiry(
                db_session,
                phone=destination,
                message=text,
                customer_name=sender_name or (customer.name if customer else ""),
                source="whatsapp",
            )

        if normalized in ACTIVATION_PHRASES or normalized.startswith("kabilai ai "):
            chat_session = await session_store.start(destination, sender_name)
            first_prompt = ""
            if normalized.startswith("kabilai ai "):
                first_prompt = text.strip()[len("kabilai ai "):].strip()

            if not first_prompt:
                with Session(engine) as session:
                    from app.services.catalog import get_company_info

                    info = get_company_info(session)
                greeting = info.get("intro_message") or GREETING.format(
                    brand=info.get("name") or "Kabilai Dairy",
                    name=sender_name or "there",
                    mins=settings.session_idle_minutes,
                )
                await gupshup_client.send_text(destination, greeting)
                return
            text = first_prompt

        elif normalized in DEACTIVATION_PHRASES:
            if chat_session is not None:
                await session_store.end(destination)
                await gupshup_client.send_text(destination, GOODBYE)
            return

        elif chat_session is None:
            logger.info("Ignoring (no AI session) from %s: %s", destination, text)
            return

        chat_session.touch()

        _save_message(cid, "user", text)

        try:
            reply = await self._run_agent(chat_session, text, destination)
        except Exception:
            logger.exception("Agent run failed for %s", destination)
            reply = "Sorry, something went wrong on my side. Please try again."

        reply = normalize_output(reply)
        _save_message(cid, "assistant", reply)
        await gupshup_client.send_text(destination, reply)


assistant_workflow = AssistantWorkflow()
