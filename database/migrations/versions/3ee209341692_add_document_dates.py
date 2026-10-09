"""Add source_updated_at to documents

Revision ID: 3ee209341692
Revises: 4d65588e92d2
Create Date: 2026-10-09 20:58:23.596772

document_date deferred: no reliable end-to-end extraction exists yet.
Do not add it here until the parser and ingestion pipeline produce it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ee209341692'
down_revision: Union[str, None] = '4d65588e92d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=True))
    # document_date deferred — no extraction implementation exists yet.


def downgrade() -> None:
    op.drop_column('documents', 'source_updated_at')
