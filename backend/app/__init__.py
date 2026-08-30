from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.webhooks import gupshup_webhook
from app.core.config import settings
from app.core.database import init_db
from app.core.lifespan import lifespan
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Kabilai Dairy WhatsApp assistant for product info, pricing, delivery, and enquiries.",
        debug=settings.debug,
        lifespan=lifespan,
    )

    init_db()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_prefix)
    # Bare path for Gupshup webhooks configured without the /api/v1 prefix.
    application.add_api_route("/webhook/gupshup", gupshup_webhook, methods=["POST"], include_in_schema=False)

    @application.get("/", tags=["service"])
    async def service_info() -> dict[str, Any]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api": settings.api_prefix,
        }

    return application


app = create_app()
