from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.normalize import normalize_phone
from app.models.complaint import Complaint


def _generate_complaint_number(session: Session) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"CMP-{stamp}-"
    existing = session.exec(
        select(Complaint).where(Complaint.complaint_number.like(f"{prefix}%"))
    ).all()
    seq = len(existing) + 1
    return f"{prefix}{seq:04d}"


def create_complaint(
    session: Session,
    phone: str,
    message: str = "",
    customer_name: str = "",
    category: str = "other",
    related_product: str = "",
    source: str = "whatsapp",
) -> Complaint:
    normalized = normalize_phone(phone)
    complaint = Complaint(
        complaint_number=_generate_complaint_number(session),
        customer_name=customer_name,
        phone=normalized,
        message=message,
        category=category,
        related_product=related_product,
        status="pending",
        source=source,
    )
    session.add(complaint)
    session.commit()
    session.refresh(complaint)
    return complaint


def list_complaints_for_phone(session: Session, phone: str) -> list[Complaint]:
    normalized = normalize_phone(phone)
    return list(session.exec(
        select(Complaint).where(Complaint.phone == normalized).order_by(Complaint.created_at.desc())
    ).all())


def get_latest_open_complaint_for_phone(session: Session, phone: str) -> Complaint | None:
    """Return the most recent unresolved complaint (pending/in_progress), else newest."""
    normalized = normalize_phone(phone)
    complaints = list_complaints_for_phone(session, phone)
    if not complaints:
        return None
    open_ones = [c for c in complaints if c.status in ("pending", "in_progress")]
    return open_ones[0] if open_ones else complaints[0]


def log_complaint_change(
    session: Session,
    complaint_id: int,
    field: str,
    old_value: str,
    new_value: str,
    changed_by: str = "system",
    actor_role: str = "system",
) -> None:
    from app.models.complaint_history import ComplaintHistory

    session.add(
        ComplaintHistory(
            complaint_id=complaint_id,
            field=field,
            old_value=old_value or "",
            new_value=new_value or "",
            changed_by=changed_by,
            actor_role=actor_role,
        )
    )


def list_complaint_history_paged(
    session: Session,
    complaint_id: int,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list, int]:
    """Return (entries, total). Entries are newest-first for pagination."""
    from sqlalchemy import func
    from app.models.complaint_history import ComplaintHistory

    total = session.exec(
        select(func.count()).select_from(ComplaintHistory).where(ComplaintHistory.complaint_id == complaint_id)
    ).one()
    entries = session.exec(
        select(ComplaintHistory)
        .where(ComplaintHistory.complaint_id == complaint_id)
        .order_by(ComplaintHistory.created_at.desc(), ComplaintHistory.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(entries), int(total)
