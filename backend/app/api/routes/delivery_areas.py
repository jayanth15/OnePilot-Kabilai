from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.delivery import DeliveryArea

router = APIRouter(prefix="/delivery-areas", tags=["delivery-areas"])


class DeliveryAreaCreate(BaseModel):
    name: str
    pincode: str = ""
    city: str = "Chennai"
    is_active: bool = True


class DeliveryAreaUpdate(BaseModel):
    name: str | None = None
    pincode: str | None = None
    city: str | None = None
    is_active: bool | None = None


@router.get("")
def list_delivery_areas(
    city: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q = select(DeliveryArea).order_by(desc(DeliveryArea.created_at))
    if city:
        q = q.where(DeliveryArea.city == city)
    if is_active is not None:
        q = q.where(DeliveryArea.is_active is is_active)
    return session.exec(q).all()


@router.post("")
def create_delivery_area(
    body: DeliveryAreaCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    area = DeliveryArea(**body.model_dump())
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@router.get("/{area_id}")
def get_delivery_area(area_id: int, session: Session = Depends(get_session)):
    area = session.get(DeliveryArea, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Delivery area not found")
    return area


@router.patch("/{area_id}")
def update_delivery_area(
    area_id: int,
    body: DeliveryAreaUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    area = session.get(DeliveryArea, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Delivery area not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    session.commit()
    session.refresh(area)
    return area


@router.delete("/{area_id}")
def delete_delivery_area(
    area_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    area = session.get(DeliveryArea, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Delivery area not found")
    session.delete(area)
    session.commit()
    return {"ok": True}
