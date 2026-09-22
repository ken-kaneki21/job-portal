"""add candidate profiles

Revision ID: c3a76f91e4b2
Revises: 98c205316bba
Create Date: 2026-09-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3a76f91e4b2"
down_revision: Union[str, Sequence[str], None] = "98c205316bba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "profile_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "universal_payload",
            postgresql.JSONB(
                astext_type=sa.Text(),
            ),
            nullable=False,
        ),
        sa.Column(
            "legacy_payload",
            postgresql.JSONB(
                astext_type=sa.Text(),
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "profile_name",
            name=("uq_candidate_profiles_" "profile_name"),
        ),
    )

    op.create_index(
        "ix_candidate_profiles_profile_name",
        "candidate_profiles",
        [
            "profile_name",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_candidate_profiles_profile_name",
        table_name="candidate_profiles",
    )

    op.drop_table("candidate_profiles")
