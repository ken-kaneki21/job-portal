from sqlalchemy import select

from jobintel.db.models import (
    NotificationRecord,
)
from jobintel.db.session import SessionLocal

MAX_RETRIES = 3


def main() -> None:
    with SessionLocal() as session:
        failed = session.scalars(
            select(NotificationRecord).where(NotificationRecord.status == "failed")
        ).all()

        retry_count = 0

        for notification in failed:
            notification.status = "pending"

            notification.error_message = None

            retry_count += 1

            if retry_count >= MAX_RETRIES:
                break

        session.commit()

    print(f"Notifications reset for retry: {retry_count}")


if __name__ == "__main__":
    main()
