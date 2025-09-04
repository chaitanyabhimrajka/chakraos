"""normalize inquiries.id to uuid

Revision ID: e6414121da12
Revises: fb859dffb8b7
Create Date: 2025-09-04 15:47:19.576758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6414121da12'
down_revision: Union[str, Sequence[str], None] = 'fb859dffb8b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) ensure column exists (but don't error if it already does)
    op.execute("""
    ALTER TABLE quotations
      ADD COLUMN IF NOT EXISTS inquiry_id uuid
    """)

    # 2) if the column exists but is TEXT, convert it to UUID
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='quotations'
          AND column_name='inquiry_id'
          AND udt_name <> 'uuid'
      ) THEN
        ALTER TABLE quotations
          ALTER COLUMN inquiry_id TYPE uuid USING inquiry_id::uuid;
      END IF;
    END $$;
    """)

    # 3) add FK only if it isn't already present
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname='fk_quotations_inquiry_id'
      ) THEN
        ALTER TABLE quotations
          ADD CONSTRAINT fk_quotations_inquiry_id
          FOREIGN KEY (inquiry_id) REFERENCES inquiries(id)
          ON DELETE SET NULL;
      END IF;
    END $$;
    """)

def downgrade():
    # mirror the guards on downgrade so it's safe to re-run
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname='fk_quotations_inquiry_id'
      ) THEN
        ALTER TABLE quotations DROP CONSTRAINT fk_quotations_inquiry_id;
      END IF;
    END $$;
    """)
    op.execute("""
    ALTER TABLE quotations DROP COLUMN IF EXISTS inquiry_id;
    """)