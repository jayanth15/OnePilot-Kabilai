from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import get_session
from app.models.contact import Contact

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact).order_by(Contact.created_at.desc())).all()
    provider = (settings.whatsapp_provider or "gupshup").lower()
    if provider == "cloud":
        messaging_channel = "whatsapp-cloud"
        messaging_mock = settings.whatsapp_mock
        source_number = settings.whatsapp_phone_number_id
    else:
        messaging_channel = "gupshup-whatsapp"
        messaging_mock = settings.gupshup_mock
        source_number = settings.gupshup_source_number
    return {
        "environment": settings.environment,
        "api_prefix": settings.api_prefix,
        "agent_model": settings.agent_model,
        "messaging_channel": messaging_channel,
        "messaging_mock": messaging_mock,
        "source_number": source_number,
        "whatsapp_provider": provider,
        "whatsapp_api_version": settings.whatsapp_api_version,
        "session_idle_minutes": settings.session_idle_minutes,
        "contacts": [
            {
                "id": c.id,
                "phone": c.phone,
                "name": c.name,
                "created_at": c.created_at.isoformat(),
            }
            for c in contacts
        ],
    }
