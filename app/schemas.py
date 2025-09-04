# app/schemas.py
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime

# ---------- Quotation ----------

class QuotationBase(BaseModel):
    inquiry_id: UUID | None = None # link back to Inquiry if any

class QuotationItemCreate(BaseModel):
    description: str
    qty: float = 1
    uom: str = "EA"
    unit_price: float = 0
    tax_code: Optional[str] = None
    discount_pct: float = 0

class QuotationItemRead(QuotationItemCreate):
    id: str
    line_total: float

class QuotationCreate(BaseModel):
    company_code: str = Field(..., min_length=1)
    issue_date: Optional[date] = None
    currency: str = "INR"
    validity_date: Optional[date] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    items: List[QuotationItemCreate] = Field(default_factory=list)

class QuotationRead(BaseModel):
    id: UUID
    quote_no: Optional[str]
    company_id: str
    issue_date: date
    currency: str
    status: str
    validity_date: Optional[date]
    payment_terms: Optional[str]
    notes: Optional[str]
    created_at: datetime
    items: List[QuotationItemRead] = Field(default_factory=list)

    class Config:
        from_attributes = True