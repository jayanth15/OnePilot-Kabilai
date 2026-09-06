"""Meta WhatsApp Business Platform — Cloud API client (Graph API v26.0).

Latest version verified 2026-09-03: Graph API ``v26.0`` (released Jul 29, 2026,
available until TBD; v25.0 expires Jul 29, 2028). Docs:
https://developers.facebook.com/docs/whatsapp/cloud-api/
https://developers.facebook.com/docs/graph-api/changelog/version26.0/

Endpoint shape (Cloud API):
    POST https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages
    Headers: Authorization: Bearer {ACCESS_TOKEN}, Content-Type: application/json
    Body: {"messaging_product": "whatsapp", "to": "<e164>", "type": "text",
           "text": {"body": "...", "preview_url": false}}

Inbound webhooks arrive as Meta `entry[].changes[].value` payloads; parsing
lives in ``app.api.routes.webhooks`` (see ``parse_cloud_payload`` there) so
this module stays send-only plus ``mark_read``.
"""

import logging

import httpx

from app.core.config import Settings, settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"
WHATSAPP_TEXT_LIMIT = 4096


def messages_url(version: str, phone_number_id: str) -> str:
    """Build the versioned Cloud API messages endpoint."""
    version = version if version.startswith("v") else f"v{version}"
    return f"{GRAPH_BASE}/{version}/{phone_number_id}/messages"


class WhatsAppCloudClient:
    def __init__(
        self,
        config: Settings = settings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._client = http_client
        self._owns_client = http_client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.config.whatsapp_timeout_seconds)
        return self._client

    @property
    def is_configured(self) -> bool:
        return bool(self.config.whatsapp_access_token and self.config.whatsapp_phone_number_id)

    async def send_text(
        self,
        destination: str,
        text: str,
        preview_url: bool = False,
    ) -> str | None:
        """Send a session text message. Returns Meta message id (or None in mock)."""
        text = (text or "")[:WHATSAPP_TEXT_LIMIT]

        if self.config.whatsapp_mock or not self.is_configured:
            logger.info("[MOCK-CLOUD %s] WhatsApp -> %s: %s", self.config.whatsapp_api_version, destination, text)
            return None

        url = messages_url(self.config.whatsapp_api_version, self.config.whatsapp_phone_number_id)
        response = await self._get_client().post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.whatsapp_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": destination,
                "type": "text",
                "text": {"body": text, "preview_url": preview_url},
            },
        )
        response.raise_for_status()
        data = response.json()
        msg_id = None
        try:
            msg_id = data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError):
            pass
        logger.info("Sent Cloud API %s message to %s: %s", self.config.whatsapp_api_version, destination, msg_id)
        return msg_id

    async def send_template(
        self,
        destination: str,
        template_name: str,
        language: str = "en",
        components: list[dict] | None = None,
    ) -> str | None:
        """Send a pre-approved template (required outside the 24h service window)."""
        if self.config.whatsapp_mock or not self.is_configured:
            logger.info(
                "[MOCK-CLOUD %s] Template '%s' -> %s",
                self.config.whatsapp_api_version,
                template_name,
                destination,
            )
            return None

        url = messages_url(self.config.whatsapp_api_version, self.config.whatsapp_phone_number_id)
        payload: dict = {
            "messaging_product": "whatsapp",
            "to": destination,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language}},
        }
        if components:
            payload["template"]["components"] = components
        response = await self._get_client().post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.whatsapp_access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError):
            return None

    async def mark_read(self, message_id: str) -> None:
        """Mark an inbound message as read (blue ticks). Best-effort."""
        if self.config.whatsapp_mock or not self.is_configured or not message_id:
            return
        url = messages_url(self.config.whatsapp_api_version, self.config.whatsapp_phone_number_id)
        try:
            await self._get_client().post(
                url,
                headers={
                    "Authorization": f"Bearer {self.config.whatsapp_access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                },
            )
        except Exception:
            logger.exception("Cloud API mark_read failed for %s", message_id)

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None


whatsapp_cloud_client = WhatsAppCloudClient()
