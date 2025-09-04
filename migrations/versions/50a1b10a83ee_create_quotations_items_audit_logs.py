"""create quotations, quotation_items, audit_logs

Revision ID: 0001_create_quotes
Revises: 
Create Date: 2025-09-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0001_create_quotes"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "quotations",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("quote_no", sa.String(), nullable=True),
        sa.Column("issue_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column("currency", sa.String(), server_default=sa.text("'INR'"), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("validity_date", sa.Date(), nullable=True),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_q_company_issue", "quotations", ["company_id", "issue_date"], unique=False)

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("quotation_id", sa.String(), sa.ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("qty", sa.Numeric(18, 3), server_default=sa.text("1"), nullable=False),
        sa.Column("uom", sa.String(), server_default=sa.text("'EA'"), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("tax_code", sa.String(), nullable=True),
        sa.Column("discount_pct", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("line_total", sa.Numeric(18, 2), server_default=sa.text("0"), nullable=False),
    )
    op.create_index("idx_qi_quote", "quotation_items", ["quotation_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column("company_id", sa.String(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("before_json", pg.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", pg.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_audit_company_at", "audit_logs", ["company_id", "at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_audit_company_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_qi_quote", table_name="quotation_items")
    op.drop_table("quotation_items")
    op.drop_index("idx_q_company_issue", table_name="quotations")
    op.drop_table("quotations")