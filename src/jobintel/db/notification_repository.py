from sqlalchemy.dialects.postgresql import insert

from jobintel.db.models import NotificationRecord


def enqueue_notifications(
    session,
    job_ids: set[int],
    pipeline_run_id: int,
    profile_name: str,
    notification_type: str,
) -> int:
    """
    Insert pending notifications.

    Duplicate notifications for the same
    job/profile/type are ignored.
    """

    if not job_ids:
        return 0

    rows = [
        {
            "job_id": job_id,
            "pipeline_run_id": pipeline_run_id,
            "profile_name": profile_name,
            "notification_type": notification_type,
            "status": "pending",
        }
        for job_id in sorted(job_ids)
    ]

    stmt = (
        insert(NotificationRecord)
        .values(rows)
        .on_conflict_do_nothing(constraint=("uq_notification_job_profile_type"))
        .returning(NotificationRecord.id)
    )

    inserted_ids = session.scalars(stmt).all()

    return len(inserted_ids)
