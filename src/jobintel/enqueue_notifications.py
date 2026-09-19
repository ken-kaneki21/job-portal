from jobintel.db.notification_repository import (
    enqueue_notifications,
)
from jobintel.db.session import SessionLocal
from jobintel.new_high_confidence import (
    get_high_confidence_job_ids,
    get_recent_successful_ranking_runs,
)

PROFILE_NAME = "data_engineer"

NOTIFICATION_TYPE = "new_high_confidence"


def main() -> None:
    with SessionLocal() as session:
        run_ids = get_recent_successful_ranking_runs(session)

        if len(run_ids) < 2:
            print()
            print("Need at least two successful ranking runs.")
            return

        latest_run_id = run_ids[0]
        previous_run_id = run_ids[1]

        latest_ids = get_high_confidence_job_ids(
            session=session,
            run_id=latest_run_id,
        )

        previous_ids = get_high_confidence_job_ids(
            session=session,
            run_id=previous_run_id,
        )

        new_job_ids = latest_ids - previous_ids

        queued = enqueue_notifications(
            session=session,
            job_ids=new_job_ids,
            pipeline_run_id=latest_run_id,
            profile_name=PROFILE_NAME,
            notification_type=(NOTIFICATION_TYPE),
        )

        session.commit()

    print()
    print("=" * 100)
    print("NOTIFICATION OUTBOX")
    print("=" * 100)

    print(f"Previous run: {previous_run_id}")

    print(f"Latest run:   {latest_run_id}")

    print(f"New high-confidence jobs: {len(new_job_ids)}")

    print(f"Notifications queued: {queued}")


if __name__ == "__main__":
    main()
