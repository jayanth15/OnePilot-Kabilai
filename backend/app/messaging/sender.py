"""Provider-agnostic WhatsApp sender.

``WHATSAPP_PROVIDER=gupshup`` (default) keeps the existing Gupshup behaviour.
``WHATSAPP_PROVIDER=cloud`` uses the official Meta WhatsApp Cloud API
(Graph API version from ``WHATSAPP_API_VERSION``, default ``v26.0``).

All business code (workflows, agents, staff-send) should call
``whatsapp_sender.send_text`` instead of importing a provider client directly.
"""

import logging

from app.core.config import settings
from app.messaging.gupshup import gupshup_client
from app.messaging.whatsapp_cloud import whatsapp_cloud_client

logger = logging.getLogger(__name__)


class WhatsAppSender:
    async def send_text(self, destination: str, text: str) -> None:
        provider = (settings.whatsapp_provider or "gupshup").lower()
        if provider == "cloud":
            await whatsapp_cloud_client.send_text(destination, text)
            return
        await gupshup_client.send_text(destination, text)

    async def close(self) -> None:
        await gupshup_client.close()
        await whatsapp_cloud_client.close()


whatsapp_sender = WhatsAppSender()
