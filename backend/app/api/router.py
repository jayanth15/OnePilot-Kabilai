from fastapi import APIRouter

from app.api.routes import (
    agent,
    auth,
    company,
    complaints,
    contacts,
    delivery_areas,
    enquiries,
    health,
    products,
    settings,
    users,
    webhooks,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(agent.router)
api_router.include_router(contacts.router)
api_router.include_router(settings.router)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(products.router)
api_router.include_router(delivery_areas.router)
api_router.include_router(enquiries.router)
api_router.include_router(complaints.router)
api_router.include_router(company.router)
api_router.include_router(users.router)
