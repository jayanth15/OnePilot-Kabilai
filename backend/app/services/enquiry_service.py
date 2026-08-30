from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.normalize import normalize_phone
from app.models.enquiry import Enquiry


def _generate_enquiry_number(session: Session) -> str:
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"ENQ-{stamp}-"
    existing = session.exec(
        select(Enquiry).where(Enquiry.enquiry_number.like(f"{prefix}%"))
    ).all()
    seq = len(existing) + 1
    return f"{prefix}{seq:04d}"


def create_enquiry(
    session: Session,
    phone: str,
    message: str = "",
    customer_name: str = "",
    product_interest: str = "",
    delivery_area: str = "",
    source: str = "whatsapp",
) -> Enquiry:
    normalized = normalize_phone(phone)
    enquiry = Enquiry(
        enquiry_number=_generate_enquiry_number(session),
        customer_name=customer_name,
        phone=normalized,
        message=message,
        product_interest=product_interest,
        delivery_area=delivery_area,
        status="new",
        source=source,
    )
    session.add(enquiry)
    session.commit()
    session.refresh(enquiry)
    return enquiry


def ensure_enquiry(
    session: Session,
    phone: str,
    message: str = "",
    customer_name: str = "",
    source: str = "whatsapp",
) -> Enquiry | None:
    """Create an enquiry only if the phone has none yet, so every new customer
    that starts a chat shows up in the enquiries CRM."""
    normalized = normalize_phone(phone)
    existing = session.exec(select(Enquiry).where(Enquiry.phone == normalized)).first()
    if existing:
        return None
    return create_enquiry(
        session,
        phone=normalized,
        message=message,
        customer_name=customer_name,
        source=source,
    )


def list_enquiries_for_phone(session: Session, phone: str) -> list[Enquiry]:
    normalized = normalize_phone(phone)
    return list(session.exec(
        select(Enquiry).where(Enquiry.phone == normalized).order_by(Enquiry.created_at.desc())
    ).all())


def get_latest_enquiry_for_phone(session: Session, phone: str) -> Enquiry | None:
    """Return the most recent active (new/contacted) enquiry for a phone, else newest."""
    normalized = normalize_phone(phone)
    enquiries = list_enquiries_for_phone(session, phone)
    if not enquiries:
        return None
    active = [e for e in enquiries if e.status in ("new", "contacted")]
    return active[0] if active else enquiries[0]


def update_enquiry_fields(
    session: Session,
    enquiry: Enquiry,
    *,
    product_interest: str | None = None,
    delivery_area: str | None = None,
    changed_by: str = "system",
    actor_role: str = "system",
) -> Enquiry:
    """Set enquiry fields, recording changes in the audit history."""
    if product_interest is not None and product_interest != enquiry.product_interest:
        log_enquiry_change(
            session,
            enquiry.id,
            "product_interest",
            enquiry.product_interest,
            product_interest,
            changed_by=changed_by,
            actor_role=actor_role,
        )
        enquiry.product_interest = product_interest
    if delivery_area is not None and delivery_area != enquiry.delivery_area:
        log_enquiry_change(
            session,
            enquiry.id,
            "delivery_area",
            enquiry.delivery_area,
            delivery_area,
            changed_by=changed_by,
            actor_role=actor_role,
        )
        enquiry.delivery_area = delivery_area
    enquiry.updated_at = datetime.now(timezone.utc)
    session.add(enquiry)
    session.commit()
    session.refresh(enquiry)
    return enquiry


def log_enquiry_change(
    session: Session,
    enquiry_id: int,
    field: str,
    old_value: str,
    new_value: str,
    changed_by: str = "system",
    actor_role: str = "system",
) -> None:
    from app.models.enquiry_history import EnquiryHistory

    entry = EnquiryHistory(
        enquiry_id=enquiry_id,
        field=field,
        old_value=old_value or "",
        new_value=new_value or "",
        changed_by=changed_by,
        actor_role=actor_role,
    )
    session.add(entry)


def list_enquiry_history(session: Session, enquiry_id: int) -> list:
    from app.models.enquiry_history import EnquiryHistory

    return list(session.exec(
        select(EnquiryHistory).where(EnquiryHistory.enquiry_id == enquiry_id).order_by(EnquiryHistory.created_at)
    ).all())


def list_enquiry_history_paged(
    session: Session,
    enquiry_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list, int]:
    """Return (entries, total). Entries are newest-first for pagination."""
    from sqlalchemy import func
    from app.models.enquiry_history import EnquiryHistory

    total = session.exec(
        select(func.count()).select_from(EnquiryHistory).where(EnquiryHistory.enquiry_id == enquiry_id)
    ).one()
    entries = session.exec(
        select(EnquiryHistory)
        .where(EnquiryHistory.enquiry_id == enquiry_id)
        .order_by(EnquiryHistory.created_at.desc(), EnquiryHistory.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(entries), int(total)
