from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.company import Company
from app.services.catalog import get_company_info

router = APIRouter(prefix="/company", tags=["company"])


class CompanyUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    whatsapp_number: str | None = None
    intro_message: str | None = None
    ai_enabled: bool | None = None


def _get_or_create(session: Session) -> Company:
    company = session.exec(select(Company)).first()
    if not company:
        company = Company(name="Kabilai Dairy")
        session.add(company)
        session.commit()
        session.refresh(company)
    return company


@router.get("")
def get_company(session: Session = Depends(get_session)):
    return get_company_info(session)


@router.patch("")
def update_company(
    body: CompanyUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    company = _get_or_create(session)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    session.commit()
    session.refresh(company)
    return get_company_info(session)
