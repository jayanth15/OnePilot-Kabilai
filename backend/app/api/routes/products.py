from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, desc

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    category: str = ""
    unit: str = ""
    price: float = 0.0
    description: str = ""
    is_available: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    price: float | None = None
    description: str | None = None
    is_available: bool | None = None


@router.get("")
def list_products(
    search: str | None = Query(default=None),
    is_available: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q = select(Product).order_by(desc(Product.created_at))
    if search:
        like = f"%{search}%"
        q = q.where(Product.name.like(like) | Product.category.like(like))
    if is_available is not None:
        q = q.where(Product.is_available is is_available)
    return session.exec(q).all()


@router.post("")
def create_product(
    body: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    product = Product(**body.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/{product_id}")
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}")
def update_product(
    product_id: int,
    body: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    product.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"ok": True}
