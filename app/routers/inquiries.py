# app/routers/inquiries.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db import get_db
from app.models import Company, Inquiry
from fastapi import Body
from app.services.parser.factory import get_parser
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

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