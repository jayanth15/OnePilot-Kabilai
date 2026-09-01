"""Pydantic AI agent for Kabilai Dairy — product info, delivery checks, enquiries.

The agent returns a structured ``DairyReply`` (discriminated union) rather than
free-form text. Tools collect real data; rendering happens once in
``app.messaging.templates.render_reply``.
"""

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from sqlmodel import Session

from app.core.config import settings
from app.core.database import engine
from app.core.normalize import normalize_phone
from app.agents.replies import (
    DairyReply,
    CompanyInfo,
    CompanyInfoReply,
    ComplaintConfirmedReply,
    ComplaintItem,
    ComplaintListReply,
    DeliveryCoverageReply,
    DeliveryReply,
    EnquiryConfirmedReply,
    EnquiryItem,
    EnquiryListReply,
    HandoffReply,
    HelpReply,
    ProductItem,
    ProductListReply,
    ProductPriceReply,
    TextReply,
)
from app.services.catalog import (
    get_brand_name,
    get_company_info,
    list_products,
    get_product_by_name,
    is_delivery_available,
    list_delivery_areas,
)
from app.services.enquiry_service import (
    create_enquiry,
    list_enquiries_for_phone,
    get_latest_enquiry_for_phone,
    update_enquiry_fields,
)
from app.services.complaint_service import (
    create_complaint,
    list_complaints_for_phone,
)
from app.messaging.gupshup import gupshup_client


class AgentDeps(BaseModel):
    """Carries the current customer phone so tools can update their enquiry."""
    phone: str


def _build_model() -> Model | str:
    if settings.agent_model == "test":
        from pydantic_ai.models.test import TestModel

        return TestModel()
    return settings.agent_model


def _msg_brand(session: Session) -> str:
    return get_brand_name(session)


def normalize_output(text: str) -> str:
    """Convert literal unicode-escape sequences (e.g. \\u20b9) that an LLM may
    reproduce into the real characters so WhatsApp shows the rupee symbol."""
    import re

    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    return text


agent = Agent(
    _build_model(),
    output_type=DairyReply,
    deps_type=AgentDeps,
    system_prompt=(
        "You are a helpful dairy assistant for Kabilai Dairy. "
        "Always answer with one of the allowed structured reply types — never free text. "
        "\n\n"
        "MANDATORY TOOL RULES:\n"
        "- For ANY question about a product price, product existence, or catalog, you MUST call "
        "get_product_price or list_dairy_products. Never answer a price from memory.\n"
        "- For ANY question about delivery to an area or pincode, you MUST call check_delivery_area.\n"
        "- For the company address/contact, you MUST call get_company_information.\n"
        "- Never invent products, prices, or areas. If a tool returns nothing, say so.\n\n"
        "CLASSIFY THE MESSAGE FIRST: is it an ENQUIRY or a COMPLAINT?\n"
        "- COMPLAINT = the customer is unhappy / reporting a problem (e.g. milk not delivered, "
        "milk is bad/sour, wrong item, late delivery, damaged product, billing issue). "
        "If it is a complaint you MUST call capture_complaint.\n"
        "- ENQUIRY = the customer is asking about products, prices, availability, delivery, or "
        "interest in buying. If it is an enquiry you MUST call create_enquiry_tool.\n\n"
        "Reply mapping:\n"
        "- ProductListReply for the catalog, ProductPriceReply for a price.\n"
        "- DeliveryReply for availability, CompanyInfoReply for company details.\n"
        "- EnquiryConfirmedReply for a confirmed enquiry, EnquiryListReply for past enquiries.\n"
        "- ComplaintConfirmedReply for a captured complaint, ComplaintListReply for past complaints.\n"
        "- HelpReply for a menu, HandoffReply to escalate, TextReply only for brief chat."
    ),
)


@agent.tool
async def get_company_information(ctx: RunContext[AgentDeps]) -> CompanyInfo:
    """Get the company name, address, and contact details."""
    with Session(engine) as session:
        info = get_company_info(session)
        return CompanyInfo(
            name=info["name"],
            address=info["address"],
            phone=info["phone"],
            whatsapp_number=info["whatsapp_number"],
        )


@agent.tool
async def list_dairy_products(ctx: RunContext[AgentDeps]) -> list[ProductItem]:
    """List all available dairy products with prices."""
    with Session(engine) as session:
        products = list_products(session)
        return [
            ProductItem(
                name=p.name,
                unit=p.unit,
                price=p.price,
                category=p.category,
            )
            for p in products
        ]


@agent.tool
async def get_product_price(ctx: RunContext[AgentDeps], product_name: str) -> ProductItem | None:
    """Get the current price and details for a product by name."""
    with Session(engine) as session:
        product = get_product_by_name(session, product_name)
        if not product:
            return None
        enquiry = get_latest_enquiry_for_phone(session, ctx.deps.phone)
        if enquiry:
            update_enquiry_fields(
                session,
                enquiry,
                product_interest=product.name,
                changed_by="whatsapp-agent",
                actor_role="system",
            )
        return ProductItem(
            name=product.name,
            unit=product.unit,
            price=product.price,
            category=product.category,
        )


@agent.tool
async def check_delivery_area(ctx: RunContext[AgentDeps], area: str) -> bool:
    """Check whether we deliver to a given area or pincode (Chennai)."""
    with Session(engine) as session:
        matched, _token = is_delivery_available(session, area)
        if matched:
            enquiry = get_latest_enquiry_for_phone(session, ctx.deps.phone)
            if enquiry:
                update_enquiry_fields(
                    session,
                    enquiry,
                    delivery_area=matched.name,
                    changed_by="whatsapp-agent",
                    actor_role="system",
                )
        return matched is not None


@agent.tool
async def list_delivery_area_names(ctx: RunContext[AgentDeps]) -> list[str]:
    """List all areas/localities we currently deliver to."""
    with Session(engine) as session:
        areas = list_delivery_areas(session)
        return [a.name for a in areas]


@agent.tool
async def find_enquiries_by_phone(ctx: RunContext[AgentDeps], phone: str) -> list[EnquiryItem]:
    """Find past enquiries for a customer by phone number."""
    with Session(engine) as session:
        enquiries = list_enquiries_for_phone(session, phone)
        return [
            EnquiryItem(
                enquiry_number=e.enquiry_number,
                product_interest=e.product_interest,
                delivery_area=e.delivery_area,
                status=e.status,
            )
            for e in enquiries
        ]


@agent.tool
async def create_enquiry_tool(
    ctx: RunContext[AgentDeps],
    phone: str,
    message: str = "",
    customer_name: str = "",
    product_interest: str = "",
    delivery_area: str = "",
) -> EnquiryConfirmedReply:
    """Capture a customer enquiry. Provide phone and optional product/area.
    Sends a WhatsApp confirmation to the customer."""
    with Session(engine) as session:
        brand = _msg_brand(session)
        enquiry = create_enquiry(
            session,
            phone=phone,
            message=message,
            customer_name=customer_name,
            product_interest=product_interest,
            delivery_area=delivery_area,
            source="whatsapp",
        )

    return EnquiryConfirmedReply(
        enquiry_number=enquiry.enquiry_number,
        product_interest=product_interest,
        delivery_area=delivery_area,
        brand=brand,
    )


@agent.tool
async def request_operator_handoff(ctx: RunContext[AgentDeps], phone: str) -> HandoffReply:
    """Hand the customer over to a human member of our team."""
    normalized = normalize_phone(phone)
    try:
        from app.messaging.templates import operator_handoff_msg

        await gupshup_client.send_text(normalized, operator_handoff_msg())
    except Exception:
        pass
    return HandoffReply()


@agent.tool
async def capture_complaint(
    ctx: RunContext[AgentDeps],
    phone: str,
    message: str = "",
    customer_name: str = "",
    category: str = "other",
    related_product: str = "",
) -> ComplaintConfirmedReply:
    """Capture a customer complaint (e.g. milk not delivered, milk is bad).
    Provide phone and optional category/product. Sends a WhatsApp confirmation."""
    with Session(engine) as session:
        brand = _msg_brand(session)
        complaint = create_complaint(
            session,
            phone=phone,
            message=message,
            customer_name=customer_name,
            category=category,
            related_product=related_product,
            source="whatsapp",
        )

    return ComplaintConfirmedReply(
        complaint_number=complaint.complaint_number,
        category=category,
        related_product=related_product,
        brand=brand,
    )


@agent.tool
async def find_complaints_by_phone(ctx: RunContext[AgentDeps], phone: str) -> list[ComplaintItem]:
    """Find past complaints for a customer by phone number."""
    with Session(engine) as session:
        complaints = list_complaints_for_phone(session, phone)
        return [
            ComplaintItem(
                complaint_number=c.complaint_number,
                category=c.category,
                related_product=c.related_product,
                status=c.status,
            )
            for c in complaints
        ]
