"""convert inquiries.id to uuid

Revision ID: fb859dffb8b7
Revises: fb1327413698
Create Date: 2025-09-04 15:42:11.210367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb859dffb8b7'
down_revision: Union[str, Sequence[str], None] = 'fb1327413698'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # If values are valid uuid strings (they should be), this will work:
    op.execute("ALTER TABLE inquiries ALTER COLUMN id TYPE uuid USING id::uuid")

    # (optional) if you had a default on id before, you can set a DB default now:
    # Requires pgcrypto extension, or use uuid-ossp
    # op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # op.execute("ALTER TABLE inquiries ALTER COLUMN id SET DEFAULT gen_random_uuid()")

def downgrade():
    op.execute("ALTER TABLE inquiries ALTER COLUMN id TYPE varchar USING id::text")