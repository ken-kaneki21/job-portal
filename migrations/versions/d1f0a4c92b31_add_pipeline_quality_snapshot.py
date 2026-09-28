"""add pipeline quality snapshot

Revision ID: d1f0a4c92b31
Revises: b3bdb3c07cad
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d1f0a4c92b31"
down_revision: Union[str, Sequence[str], None] = "c3a76f91e4b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs", sa.Column("quality_passed", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "pipeline_runs",
        sa.Column(
            "quality_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "quality_metrics")
    op.drop_column("pipeline_runs", "quality_passed")
