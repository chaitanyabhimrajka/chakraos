# app/models.py
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, DateTime, func, ForeignKey, Date, Numeric
from sqlalchemy.dialects import postgresql as pg
import uuid

Base = declarative_base()

def uuid_pk() -> str:
    return str(uuid.uuid4())

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_currency: Mapped[str] = mapped_column(String, default="INR")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Inquiry(Base):
    __tablename__ = "inquiries"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)  # 'email' | 'form' | 'whatsapp'
    raw_subject: Mapped[str | None] = mapped_column(Text)
    raw_body: Mapped[str | None] = mapped_column(Text)
    from_email: Mapped[str | None] = mapped_column(String)
    from_phone: Mapped[str | None] = mapped_column(String)
    extraction_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="received")
    received_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))

class Quotation(Base):
    __tablename__ = "quotations"
    id: Mapped[uuid.UUID] = mapped_column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)    
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)  # hook for later
    quote_no: Mapped[str | None] = mapped_column(String)
    issue_date: Mapped["Date"] = mapped_column(Date, server_default=func.current_date())
    currency: Mapped[str] = mapped_column(String, default="INR")
    status: Mapped[str] = mapped_column(String, default="draft")  # draft/pending_approval/approved/sent/accepted/rejected/expired/void
    validity_date: Mapped["Date | None"] = mapped_column(Date)
    payment_terms: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    inquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        pg.UUID(as_uuid=True),
        ForeignKey("inquiries.id", ondelete="SET NULL"),
        nullable=True,
    )
    items: Mapped[list["QuotationItem"]] = relationship(back_populates="quotation", lazy="selectin", cascade="all, delete-orphan")

class QuotationItem(Base):
    __tablename__ = "quotation_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    quotation_id: Mapped[str] = mapped_column(String, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(18, 3), nullable=False, default=1)
    uom: Mapped[str] = mapped_column(String, nullable=False, default="EA")
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    tax_code: Mapped[str | None] = mapped_column(String)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    line_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="items")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id"), nullable=False)
    entity: Mapped[str] = mapped_column(String, nullable=False)  # 'quotation','inquiry',...
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False) # 'create','submit','approve','send',...
    actor: Mapped[str | None] = mapped_column(String)
    before_json: Mapped[dict | None] = mapped_column(pg.JSONB)
    after_json: Mapped[dict | None] = mapped_column(pg.JSONB)
    at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())