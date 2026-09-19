from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from jobintel.db.base import Base


class JobApplicationEventRecord(Base):
    """
    Immutable history of application-state changes.

    JobApplicationStateRecord stores the current state.

    JobApplicationEventRecord stores every transition:
        new -> saved
        saved -> applied
        applied -> interviewing
        interviewing -> rejected / offer
    """

    __tablename__ = "job_application_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    previous_status: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="api",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )