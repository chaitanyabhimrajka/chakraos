# app/routers/inquiries.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db import get_db
from app.models import Company, Inquiry, Quotation, QuotationItem, AuditLog
from fastapi import Body
from app.services.parser.factory import get_parser
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from app.schemas import QuotationRead

router = APIRouter(prefix="/inquiries", tags=["inquiries"])

class InquiryCreate(BaseModel):
    source: Literal["email", "form", "whatsapp"]
    raw_subject: Optional[str] = None
    raw_body: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_phone: Optional[str] = None
    company_code: str = Field(default="ALAB")

class InquiryOut(BaseModel):
    id: str
    company_code: str
    source: str
    raw_subject: Optional[str]
    raw_body: Optional[str]
    from_email: Optional[EmailStr]
    from_phone: Optional[str]
    status: Literal["received","parsed","draft_created","needs_review","closed"]
    received_at: str
    extraction_json: Optional[dict] = None


class IngestRequest(BaseModel):
    text: str = Field(..., description="Raw natural language inquiry")
    from_email: Optional[EmailStr] = None
    from_phone: Optional[str] = None
    source: Literal["email","form","whatsapp"] = "form"
    company_code: str = "ALAB"

@router.post("", response_model=InquiryOut, status_code=201)
async def create_inquiry(payload: InquiryCreate, db: AsyncSession = Depends(get_db)):
    # resolve company
    res = await db.execute(select(Company).where(Company.code == payload.company_code))
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(400, "company_code not found")

    row = Inquiry(
        company_id=company.id,
        source=payload.source,
        raw_subject=payload.raw_subject,
        raw_body=payload.raw_body,
        from_email=payload.from_email,
        from_phone=payload.from_phone,
        status="received",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return InquiryOut(
        id=row.id,
        company_code=payload.company_code,
        source=row.source,
        raw_subject=row.raw_subject,
        raw_body=row.raw_body,
        from_email=row.from_email,
        from_phone=row.from_phone,
        status=row.status,
        received_at=row.received_at.isoformat(),
    )

@router.get("", response_model=List[InquiryOut])
async def list_inquiries(company_code: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Inquiry, Company.code).join(Company, Company.id == Inquiry.company_id)
    if company_code:
        stmt = stmt.where(Company.code == company_code)
    stmt = stmt.order_by(desc(Inquiry.received_at))
    res = await db.execute(stmt)
    rows = []
    for inq, code in res.all():
        rows.append(InquiryOut(
            id=inq.id,
            company_code=code,
            source=inq.source,
            raw_subject=inq.raw_subject,
            raw_body=inq.raw_body,
            from_email=inq.from_email,
            from_phone=inq.from_phone,
            status=inq.status,
            received_at=inq.received_at.isoformat(),
            extraction_json=inq.extraction_json,  
        ))
    return rows

@router.get("/{inquiry_id}", response_model=InquiryOut)
async def get_inquiry(inquiry_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Inquiry, Company.code).join(Company, Company.id == Inquiry.company_id).where(Inquiry.id == inquiry_id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(404, "Inquiry not found")
    inq, code = row
    return InquiryOut(
        id=inq.id, company_code=code, source=inq.source,
        raw_subject=inq.raw_subject, raw_body=inq.raw_body,
        from_email=inq.from_email, from_phone=inq.from_phone,
        status=inq.status, received_at=inq.received_at.isoformat(),
        extraction_json=inq.extraction_json,
    )

@router.post("/ingest", response_model=InquiryOut, status_code=201)
async def ingest_inquiry(payload: IngestRequest, db: AsyncSession = Depends(get_db)):
    # resolve company (same as in create_inquiry)
    res = await db.execute(select(Company).where(Company.code == payload.company_code))
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(400, "company_code not found")

    parser = get_parser()
    extraction = parser.parse(payload.text)

    row = Inquiry(
        company_id=company.id,
        source=payload.source,
        raw_subject=None,
        raw_body=payload.text,
        from_email=payload.from_email,
        from_phone=payload.from_phone,
        extraction_json=extraction,
        status="parsed" if extraction.get("detected") else "received",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return InquiryOut(
        id=row.id,
        company_code=payload.company_code,
        source=row.source,
        raw_subject=row.raw_subject,
        raw_body=row.raw_body,
        from_email=row.from_email,
        from_phone=row.from_phone,
        status=row.status,
        received_at=row.received_at.isoformat(),
        extraction_json=row.extraction_json,
    )

@router.post("/{inquiry_id}/to-quotation", response_model=QuotationRead)
async def inquiry_to_quotation(inquiry_id: str, db: AsyncSession = Depends(get_db)):
    # load inquiry
    res = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inq = res.scalar_one_or_none()
    if not inq:
        raise HTTPException(status_code=404, detail="inquiry not found")

    # resolve company (prefer FK if present)
    company = None
    if getattr(inq, "company_id", None):
        company = await db.get(Company, inq.company_id)
    elif getattr(inq, "company_code", None):
        res_c = await db.execute(select(Company).where(Company.code == inq.company_code))
        company = res_c.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=400, detail="company for inquiry not found")

    # helper for quote numbers
    from sqlalchemy import func
    async def _next_quote_no(db: AsyncSession, company_code: str) -> str:
        prefix = f"{company_code}-Q-"
        r = await db.execute(
            select(func.max(Quotation.quote_no)).where(Quotation.quote_no.like(f"{prefix}%"))
        )
        last = r.scalar_one_or_none()
        if last:
            import re
            m = re.search(r"(\d+)$", last)
            n = int(m.group(1)) + 1 if m else 1
        else:
            n = 1
        return f"{prefix}{n:04d}"

    # build first item from extraction_json (fallbacks are safe)
    desc = inq.raw_subject or ""
    qty, uom = 1.0, "EA"
    if inq.extraction_json:
        j = inq.extraction_json or {}
        desc = j.get("product_snippet") or j.get("product") or desc or (inq.raw_body[:120] if inq.raw_body else "Line 1")
        try:
            qty = float(j.get("qty") or qty)
        except Exception:
            pass
        uom = (j.get("unit") or j.get("uom") or uom)

    quote = Quotation(
        inquiry_id=inq.id,  
        company_id=company.id,
        currency="INR",
        status="draft",
        notes=f"Auto-created from inquiry {inq.id}",
    )
    quote.quote_no = await _next_quote_no(db, company.code)

    quote.items = [
        QuotationItem(
            description=desc or "Line 1",
            qty=qty,
            uom=uom,
            unit_price=0,
            line_total=0,
        )
    ]

    db.add(quote)
    db.add(AuditLog(
        company_id=company.id,
        entity="quotation",
        entity_id="(pending)",
        action="create_from_inquiry",
        before_json={"inquiry_id": inq.id},
        after_json={"quote_no": quote.quote_no},
    ))

    await db.commit()
    # ensure items are loaded; prevents async lazy-load after commit
    await db.refresh(quote, attribute_names=["items"])
    return quote