"""Structured output models for the Kabilai Dairy WhatsApp agent.

The agent returns one of these (a discriminated union) instead of free-form
text. Rendering to WhatsApp text happens in a single, deterministic place so
every session produces consistent, well-formed messages and never invents data.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ProductItem(BaseModel):
    name: str
    unit: str = ""
    price: float
    category: str = ""


class EnquiryItem(BaseModel):
    enquiry_number: str
    product_interest: str = ""
    delivery_area: str = ""
    status: str = ""


class CompanyInfo(BaseModel):
    name: str
    address: str = ""
    phone: str = ""
    whatsapp_number: str = ""


class TextReply(BaseModel):
    """A plain conversational reply with no structured payload."""
    type: Literal["text"] = "text"
    message: str


class ProductListReply(BaseModel):
    type: Literal["product_list"] = "product_list"
    products: list[ProductItem] = Field(default_factory=list)


class ProductPriceReply(BaseModel):
    type: Literal["product_price"] = "product_price"
    product: ProductItem
    unavailable: bool = False


class DeliveryReply(BaseModel):
    type: Literal["delivery"] = "delivery"
    area: str
    available: bool


class DeliveryCoverageReply(BaseModel):
    type: Literal["delivery_coverage"] = "delivery_coverage"
    areas: list[str] = Field(default_factory=list)


class CompanyInfoReply(BaseModel):
    type: Literal["company_info"] = "company_info"
    company: CompanyInfo


class EnquiryListReply(BaseModel):
    type: Literal["enquiry_list"] = "enquiry_list"
    enquiries: list[EnquiryItem] = Field(default_factory=list)


class EnquiryConfirmedReply(BaseModel):
    type: Literal["enquiry_confirmed"] = "enquiry_confirmed"
    enquiry_number: str
    product_interest: str = ""
    delivery_area: str = ""
    brand: str = ""


class HandoffReply(BaseModel):
    type: Literal["handoff"] = "handoff"


class HelpReply(BaseModel):
    type: Literal["help"] = "help"


DairyReply = (
    TextReply
    | ProductListReply
    | ProductPriceReply
    | DeliveryReply
    | DeliveryCoverageReply
    | CompanyInfoReply
    | EnquiryListReply
    | EnquiryConfirmedReply
    | HandoffReply
    | HelpReply
)
