import logging

from sqlmodel import Session

from app.agents.dairy import AgentDeps, agent, normalize_output
from app.core.config import settings
from app.core.database import engine
from app.messaging.gupshup import gupshup_client
from app.messaging.templates import render_reply
from app.services.conversation_service import (
    add_message,
    ensure_contact,
    ensure_conversation,
)
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


def _save_message(conversation_id: int, role: str, content: str) -> None:
    with Session(engine) as session:
        add_message(
            session,
            conversation_id,
            role=role,
            content=content,
            direction="outbound" if role == "assistant" else "inbound",
        )


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

        normalized = " ".join(text.lower().split())

        # Always record the inbound message (customer -> us), regardless of
        # whether the AI is active or the user said the activation phrase.
        with Session(engine) as db_session:
            contact = ensure_contact(db_session, destination, sender_name)
            conversation = ensure_conversation(db_session, contact.id)  # type: ignore[arg-type]
            cid = conversation.id
            assert cid is not None
            add_message(
                db_session,
                cid,
                role="user",
                content=text,
                direction="inbound",
            )

            # Add a new customer to the enquiries CRM on their first message.
            from app.services.enquiry_service import ensure_enquiry

            ensure_enquiry(
                db_session,
                phone=destination,
                message=text,
                customer_name=sender_name or (contact.name if contact else ""),
                source="whatsapp",
            )

        if not ai_enabled:
            logger.info("AI assistant disabled; recorded message but not replying to %s", destination)
            return

        chat_session = await session_store.get_active(destination)

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
            logger.info("Recorded message (no AI session) from %s: %s", destination, text)
            return

        chat_session.touch()

        try:
            reply = await self._run_agent(chat_session, text, destination)
        except Exception:
            logger.exception("Agent run failed for %s", destination)
            reply = "Sorry, something went wrong on my side. Please try again."

        reply = normalize_output(reply)
        _save_message(cid, "assistant", reply)
        await gupshup_client.send_text(destination, reply)


assistant_workflow = AssistantWorkflow()
