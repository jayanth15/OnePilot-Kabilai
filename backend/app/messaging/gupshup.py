import json
import logging

import httpx

from app.core.config import Settings, settings

logger = logging.getLogger(__name__)

GUPSHUP_MESSAGE_URL = "https://api.gupshup.io/wa/api/v1/msg"
WHATSAPP_TEXT_LIMIT = 4096


class GupshupClient:
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
            self._client = httpx.AsyncClient(timeout=self.config.gupshup_timeout_seconds)
        return self._client

    async def send_text(self, destination: str, text: str) -> None:
        text = text[:WHATSAPP_TEXT_LIMIT]

        if self.config.gupshup_mock:
            logger.info("[MOCK] WhatsApp -> %s: %s", destination, text)
            return

        response = await self._get_client().post(
            GUPSHUP_MESSAGE_URL,
            headers={
                "apikey": self.config.gupshup_api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "channel": "whatsapp",
                "source": self.config.gupshup_source_number,
                "destination": destination,
                "src.name": self.config.gupshup_app_name,
                "message": json.dumps({"type": "text", "text": text}),
            },
        )
        response.raise_for_status()
        logger.info("Sent WhatsApp message to %s: %s", destination, response.text)

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None


gupshup_client = GupshupClient()
