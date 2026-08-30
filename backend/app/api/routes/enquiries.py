from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.core.database import get_session
from app.core.auth import get_current_user, require_admin
from app.core.normalize import normalize_phone
from app.models.user import User
from app.models.enquiry import Enquiry
from app.services.enquiry_service import (
    create_enquiry,
    list_enquiries_for_phone,
    log_enquiry_change,
    list_enquiry_history_paged,
)

router = APIRouter(prefix="/enquiries", tags=["enquiries"])


class EnquiryCreate(BaseModel):
    phone: str
    message: str = ""
    customer_name: str = ""
    product_interest: str = ""
    delivery_area: str = ""
    source: str = "staff"


class EnquiryUpdate(BaseModel):
    customer_name: str | None = None
    message: str | None = None
    product_interest: str | None = None
    delivery_area: str | None = None
    status: str | None = None


@router.get("")
def list_enquiries(
    phone: str | None = Query(default=None),
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q = select(Enquiry).order_by(desc(Enquiry.created_at))
    if phone:
        q = q.where(Enquiry.phone == normalize_phone(phone))
    if status:
        q = q.where(Enquiry.status == status)
    return session.exec(q).all()


@router.post("")
def create_enquiry_route(
    body: EnquiryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    enquiry = create_enquiry(
        session,
        phone=body.phone,
        message=body.message,
        customer_name=body.customer_name,
        product_interest=body.product_interest,
        delivery_area=body.delivery_area,
        source=body.source,
    )
    log_enquiry_change(
        session,
        enquiry.id,
        "enquiry_number",
        "",
        enquiry.enquiry_number,
        changed_by=current_user.email,
        actor_role="admin" if current_user.is_admin else "user",
    )
    session.commit()
    session.refresh(enquiry)
    return enquiry


@router.get("/{enquiry_id}")
def get_enquiry(enquiry_id: int, session: Session = Depends(get_session)):
    enquiry = session.get(Enquiry, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return enquiry


@router.patch("/{enquiry_id}")
def update_enquiry(
    enquiry_id: int,
    body: EnquiryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    enquiry = session.get(Enquiry, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        old = getattr(enquiry, field, "")
        if old != value:
            log_enquiry_change(
                session,
                enquiry_id,
                field,
                "" if old is None else str(old),
                "" if value is None else str(value),
                changed_by=current_user.email,
                actor_role="admin" if current_user.is_admin else "user",
            )
        setattr(enquiry, field, value)
    enquiry.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(enquiry)
    return enquiry


@router.get("/by-phone/{phone}")
def get_enquiries_by_phone(
    phone: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_enquiries_for_phone(session, phone)


@router.get("/{enquiry_id}/history")
def enquiry_history(
    enquiry_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Return the audit history for an enquiry. Admin-only. Newest first."""
    enquiry = session.get(Enquiry, enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    entries, total = list_enquiry_history_paged(session, enquiry_id, offset=offset, limit=limit)
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
