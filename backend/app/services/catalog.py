from sqlmodel import Session, select

from app.models.company import Company
from app.models.product import Product
from app.models.delivery import DeliveryArea


def get_company(session: Session) -> Company | None:
    return session.exec(select(Company)).first()


def get_brand_name(session: Session) -> str:
    company = get_company(session)
    return company.name if company else "Kabilai Dairy"


def get_company_info(session: Session) -> dict:
    company = get_company(session)
    return {
        "name": company.name if company else "Kabilai Dairy",
        "address": company.address if company else "",
        "phone": company.phone if company else "",
        "whatsapp_number": company.whatsapp_number if company else "",
        "intro_message": company.intro_message if company else "",
        "ai_enabled": company.ai_enabled if company else True,
    }


def list_products(session: Session, query: str = "", available_only: bool = True) -> list[Product]:
    q = select(Product)
    if available_only:
        q = q.where(Product.is_available == True)  # noqa: E712
    if query:
        like = f"%{query}%"
        q = q.where(Product.name.like(like) | Product.category.like(like))
    return list(session.exec(q).all())


def get_product_by_name(session: Session, name: str) -> Product | None:
    like = f"%{name.strip()}%"
    return session.exec(select(Product).where(Product.name.like(like))).first()


def is_delivery_available(session: Session, area_query: str) -> tuple[DeliveryArea | None, str]:
    """Return (area, matched_token). Matches by area name or pincode."""
    token = area_query.strip()
    if not token:
        return None, token
    areas = session.exec(
        select(DeliveryArea).where(DeliveryArea.is_active == True)  # noqa: E712
    ).all()
    area = next(
        (a for a in areas if token == a.pincode or a.name.lower() == token.lower()),
        None,
    )
    return area, token


def list_delivery_areas(session: Session, active_only: bool = True) -> list[DeliveryArea]:
    """Return the delivery areas we cover, optionally only active ones."""
    q = select(DeliveryArea)
    if active_only:
        q = q.where(DeliveryArea.is_active == True)  # noqa: E712
    return list(session.exec(q).all())
