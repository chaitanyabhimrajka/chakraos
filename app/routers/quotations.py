# app/routers/quotations.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.db import get_db
from app.models import Company, Quotation, QuotationItem, AuditLog
from app.schemas import QuotationCreate, QuotationRead, QuotationItemCreate
from sqlalchemy.orm import selectinload, joinedload

router = APIRouter(prefix="/quotations", tags=["quotations"])

async def _get_company_or_404(db: AsyncSession, code: str) -> Company:
    res = await db.execute(select(Company).where(Company.code == code))
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail=f"company {code} not found")
    return company

async def _next_quote_no(db: AsyncSession, company_code: str) -> str:
    """
    Simple, readable numbering: ALAB-Q-0001 per company.
    Not race-safe for ultra-concurrency; good for now.
    """
    prefix = f"{company_code}-Q-"
    res = await db.execute(
        select(func.max(Quotation.quote_no)).where(Quotation.quote_no.like(f"{prefix}%"))
    )
    last = res.scalar_one_or_none()
    if last:
        # extract trailing digits
        import re
        m = re.search(r"(\d+)$", last)
        n = int(m.group(1)) + 1 if m else 1
    else:
        n = 1
    return f"{prefix}{n:04d}"

@router.post("", response_model=QuotationRead)
async def create_quotation(payload: QuotationCreate, db: AsyncSession = Depends(get_db)):
    company = await _get_company_or_404(db, payload.company_code)

    quote = Quotation(
        company_id=company.id,
        currency=payload.currency,
        status="draft",
        validity_date=payload.validity_date,
        payment_terms=payload.payment_terms,
        notes=payload.notes,
    )
    # assign quote_no
    quote.quote_no = await _next_quote_no(db, company.code)

    # items
    items = []
    for it in payload.items:
        line_total = round((it.qty or 0) * (it.unit_price or 0) * (1 - (it.discount_pct or 0) / 100.0), 2)
        items.append(
            QuotationItem(
                description=it.description,
                qty=it.qty,
                uom=it.uom,
                unit_price=it.unit_price,
                tax_code=it.tax_code,
                discount_pct=it.discount_pct,
                line_total=line_total,
            )
        )
    quote.items = items

    db.add(quote)
    # audit
    db.add(AuditLog(
        company_id=company.id,
        entity="quotation",
        entity_id="(pending)",
        action="create",
        before_json=None,
        after_json={"quote_no": quote.quote_no, "items": [it.description for it in items]},
    ))

    await db.commit()
    await db.refresh(quote)
    return quote

@router.get("/{quotation_id}", response_model=QuotationRead)
async def get_quotation(quotation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Quotation)
        .where(Quotation.id == quotation_id)
        .options(selectinload(Quotation.items))
    )
    res = await db.execute(stmt)
    quote = res.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="quotation not found")
    await db.refresh(quote)
    return quote

@router.get("", response_model=List[QuotationRead])
async def list_quotations(
    company_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Quotation).options(selectinload(Quotation.items))
    if company_code:
        q = await db.execute(select(Company).where(Company.code == company_code))
        company = q.scalar_one_or_none()
        if not company:
            return []
        stmt = stmt.where(Quotation.company_id == company.id)
    stmt = stmt.order_by(Quotation.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    return list(res.scalars())