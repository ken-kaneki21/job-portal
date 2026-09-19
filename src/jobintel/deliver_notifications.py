from datetime import datetime, timezone

from sqlalchemy import select

from jobintel.db.models import (
    JobRankingRecord,
    JobRecord,
    NotificationRecord,
)
from jobintel.db.session import SessionLocal
from jobintel.notifications.resend_provider import (
    send_email,
)
from jobintel.notifications.templates import (
    build_job_email,
)


PROFILE_NAME = "data_engineer"

NOTIFICATION_TYPE = (
    "new_high_confidence"
)


def load_pending_notifications(
    session,
):
    stmt = (
        select(
            NotificationRecord,
            JobRecord,
            JobRankingRecord.score,
        )
        .join(
            JobRecord,
            JobRecord.id
            == NotificationRecord.job_id,
        )
        .join(
            JobRankingRecord,
            (
                JobRankingRecord.job_id
                == NotificationRecord.job_id
            )
            & (
                JobRankingRecord.pipeline_run_id
                == NotificationRecord.pipeline_run_id
            ),
        )
        .where(
            NotificationRecord.profile_name
            == PROFILE_NAME
        )
        .where(
            NotificationRecord.notification_type
            == NOTIFICATION_TYPE
        )
        .where(
            NotificationRecord.status
            == "pending"
        )
        .where(
            JobRankingRecord.profile_name
            == PROFILE_NAME
        )
        .order_by(
            NotificationRecord.id.asc()
        )
    )

    return session.execute(
        stmt
    ).all()


def main() -> None:
    with SessionLocal() as session:
        rows = load_pending_notifications(
            session
        )

        if not rows:
            print()
            print(
                "No pending notifications."
            )
            return

        sent_count = 0
        failed_count = 0

        for notification, job, score in rows:
            subject, html = (
                build_job_email(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    score=float(score),
                    apply_url=job.apply_url,
                )
            )

            idempotency_key = (
                f"jobintel/"
                f"{notification.notification_type}/"
                f"{notification.id}"
            )

            try:
                email_id = send_email(
                    subject=subject,
                    html=html,
                    idempotency_key=(
                        idempotency_key
                    ),
                )

                notification.status = (
                    "sent"
                )

                notification.sent_at = (
                    datetime.now(
                        timezone.utc
                    )
                )

                notification.error_message = (
                    None
                )

                sent_count += 1

                print()
                print(
                    f"Sent notification "
                    f"{notification.id}"
                )

                print(
                    f"Job: {job.title} "
                    f"at {job.company}"
                )

                print(
                    f"Score: "
                    f"{float(score):.1f}"
                )

                print(
                    f"Resend email ID: "
                    f"{email_id}"
                )

            except Exception as exc:
                notification.status = (
                    "failed"
                )

                notification.error_message = (
                    str(exc)
                )

                failed_count += 1

                print()
                print(
                    f"Failed notification "
                    f"{notification.id}"
                )

                print(
                    f"Error: {exc}"
                )

            session.commit()

    print()
    print("=" * 100)
    print(
        "NOTIFICATION DELIVERY"
    )
    print("=" * 100)

    print(
        f"Sent:   {sent_count}"
    )

    print(
        f"Failed: {failed_count}"
    )


if __name__ == "__main__":
    main()