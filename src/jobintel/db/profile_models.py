from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jobintel.db.base import Base


class CandidateProfileRecord(Base):
    __tablename__ = "candidate_profiles"

    __table_args__ = (
        UniqueConstraint(
            "profile_name",
            name="uq_candidate_profiles_profile_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    profile_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    universal_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    legacy_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
