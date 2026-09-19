"""add job application events

Revision ID: 98c205316bba
Revises: 848895db4423
Create Date: 2026-09-18 16:22:43.513630

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "98c205316bba"
down_revision: Union[str, Sequence[str], None] = "848895db4423"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_application_events",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "profile_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "previous_status",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "new_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'api'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_job_application_events_job_id",
        "job_application_events",
        ["job_id"],
        unique=False,
    )

    op.create_index(
        "ix_job_application_events_profile_name",
        "job_application_events",
        ["profile_name"],
        unique=False,
    )

    op.create_index(
        "ix_job_application_events_previous_status",
        "job_application_events",
        ["previous_status"],
        unique=False,
    )

    op.create_index(
        "ix_job_application_events_new_status",
        "job_application_events",
        ["new_status"],
        unique=False,
    )

    op.create_index(
        "ix_job_application_events_created_at",
        "job_application_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_job_application_events_created_at",
        table_name="job_application_events",
    )

    op.drop_index(
        "ix_job_application_events_new_status",
        table_name="job_application_events",
    )

    op.drop_index(
        "ix_job_application_events_previous_status",
        table_name="job_application_events",
    )

    op.drop_index(
        "ix_job_application_events_profile_name",
        table_name="job_application_events",
    )

    op.drop_index(
        "ix_job_application_events_job_id",
        table_name="job_application_events",
    )

    op.drop_table("job_application_events")
