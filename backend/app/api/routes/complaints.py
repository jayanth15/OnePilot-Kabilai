from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.core.database import get_session
from app.core.auth import get_current_user, require_admin
from app.core.normalize import normalize_phone
from app.models.user import User
from app.models.complaint import Complaint
from app.services.complaint_service import (
    create_complaint,
    list_complaints_for_phone,
    log_complaint_change,
    list_complaint_history_paged,
)

router = APIRouter(prefix="/complaints", tags=["complaints"])


class ComplaintCreate(BaseModel):
    phone: str
    message: str = ""
    customer_name: str = ""
    category: str = "other"
    related_product: str = ""
    source: str = "staff"


class ComplaintUpdate(BaseModel):
    customer_name: str | None = None
    message: str | None = None
    category: str | None = None
    related_product: str | None = None
    status: str | None = None


@router.get("")
def list_complaints(
    phone: str | None = Query(default=None),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q = select(Complaint).order_by(desc(Complaint.created_at))
    if phone:
        q = q.where(Complaint.phone == normalize_phone(phone))
    if status:
        q = q.where(Complaint.status == status)
    if category:
        q = q.where(Complaint.category == category)
    return session.exec(q).all()


@router.post("")
def create_complaint_route(
    body: ComplaintCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    complaint = create_complaint(
        session,
        phone=body.phone,
        message=body.message,
        customer_name=body.customer_name,
        category=body.category,
        related_product=body.related_product,
        source=body.source,
    )
    log_complaint_change(
        session,
        complaint.id,
        "complaint_number",
        "",
        complaint.complaint_number,
        changed_by=current_user.email,
        actor_role="admin" if current_user.is_admin else "user",
    )
    session.commit()
    session.refresh(complaint)
    return complaint


@router.get("/{complaint_id}")
def get_complaint(complaint_id: int, session: Session = Depends(get_session)):
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}")
def update_complaint(
    complaint_id: int,
    body: ComplaintUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        old = getattr(complaint, field, "")
        if old != value:
            log_complaint_change(
                session,
                complaint_id,
                field,
                "" if old is None else str(old),
                "" if value is None else str(value),
                changed_by=current_user.email,
                actor_role="admin" if current_user.is_admin else "user",
            )
        setattr(complaint, field, value)
    complaint.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(complaint)
    return complaint


@router.get("/by-phone/{phone}")
def get_complaints_by_phone(
    phone: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_complaints_for_phone(session, phone)


@router.get("/{complaint_id}/history")
def complaint_history(
    complaint_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Return the audit history for a complaint. Admin-only. Newest first."""
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    entries, total = list_complaint_history_paged(session, complaint_id, offset=offset, limit=limit)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": e.id,
                "field": e.field,
                "old_value": e.old_value,
                "new_value": e.new_value,
                "changed_by": e.changed_by,
                "actor_role": e.actor_role,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
    }
