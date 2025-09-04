"""add inquiry_id to quotations and backfill

Revision ID: fb1327413698
Revises: 0001_create_quotes
Create Date: 2025-09-04 15:33:22.238872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg 

# revision identifiers, used by Alembic.
revision: str = 'fb1327413698'
down_revision: Union[str, Sequence[str], None] = '0001_create_quotes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "quotations",
        sa.Column("inquiry_id", pg.UUID(as_uuid=True), nullable=True),  # <- pg.UUID
    )
    op.create_foreign_key(
        "fk_quotations_inquiry_id",
        "quotations", "inquiries",
        ["inquiry_id"], ["id"],
        ondelete="SET NULL",
    )

    # (optional) backfill using notes -> inquiry_id regex
    op.execute(
        """
        UPDATE quotations q
        SET inquiry_id = sub.inquiry_id
        FROM (
            SELECT id AS quotation_id,
                   CAST(
                     regexp_replace(notes, '.*?\\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\\b.*', '\\1')
                     AS uuid
                   ) AS inquiry_id
            FROM quotations
            WHERE notes ILIKE '%Auto-created from inquiry%'
        ) sub
        WHERE q.id = sub.quotation_id
          AND sub.inquiry_id IS NOT NULL
        """
    )

    op.create_index("ix_quotations_inquiry_id", "quotations", ["inquiry_id"])
    # If you’re confident everything backfilled, you can enforce NOT NULL:
    # op.alter_column("quotations", "inquiry_id", nullable=False)

def downgrade():
    op.drop_index("ix_quotations_inquiry_id", table_name="quotations")
    op.drop_constraint("fk_quotations_inquiry_id", "quotations", type_="foreignkey")
    op.drop_column("quotations", "inquiry_id")