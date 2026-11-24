"""Exercise cached ingestion, ranking, auth and real Temporal replay."""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import timedelta
from html import escape
from pathlib import Path
from unittest.mock import patch

import httpx
from sqlalchemy import select, text
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from jobintel import main as ingestion
from jobintel import rank
from jobintel.db.models import JobRankingRecord, JobRecord, RawJobRecord
from jobintel.db.session import SessionLocal
from jobintel.models.company import Company
from jobintel.pipeline import create_pipeline_run, finalize_pipeline_run
from jobintel.ranking.scoring import detect_min_experience
from jobintel.sources.greenhouse import BASE_URL, GreenhouseSource

QUEUE = "cached-stack-acceptance"
COMPANY = Company(
    name="Cached Experience Fixture", ats="greenhouse", identifier="offline"
)
DESCRIPTIONS = [
    "<p>Experience: 2-5 years</p><p>Minimum 5 years of experience required</p>",
    "<p>Minimum 2 years of experience</p><h3>Preferred qualifications</h3>"
    "<p>At least 6 years of experience with Spark</p>",
]
PROFILE = {
    "name": "screening",
    "target_titles": ["Data Engineer"],
    "adjacent_titles": [],
    "exclude_titles": [],
    "preferred_locations": ["Bengaluru"],
    "allowed_countries": ["India"],
    "blocked_location_terms": [],
    "core_skills": ["Python"],
    "secondary_skills": [],
    "max_preferred_experience_years": 3,
    "hard_max_experience_years": 4,
}


def cached_response(request):
    if str(request.url.copy_with(query=None)) != f"{BASE_URL}/offline/jobs":
        raise RuntimeError(
            "Acceptance driver attempted a URL outside its cached fixture"
        )
    return httpx.Response(
        200,
        json={
            "jobs": [
                {
                    "id": i,
                    "title": "Data Engineer",
                    "location": {"name": "Bengaluru"},
                    "absolute_url": f"https://example.invalid/jobs/{i}",
                    "content": f"<p>{escape('Python')}</p>{description}",
                }
                for i, description in enumerate(DESCRIPTIONS, 1)
            ]
        },
    )


@activity.defn
async def cached_ingest_rank(run_id: int) -> dict:
    replay = run_id != 0
    if not replay:
        run_id = create_pipeline_run()

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(cached_response)
    ) as cached:
        with (
            patch.object(ingestion, "load_companies", return_value=[COMPANY]),
            patch.object(
                ingestion,
                "build_sources",
                return_value={"greenhouse": GreenhouseSource(cached)},
            ),
        ):
            await ingestion.main()

    previous_run = os.environ.get("JOBINTEL_PIPELINE_RUN_ID")
    os.environ["JOBINTEL_PIPELINE_RUN_ID"] = str(run_id)
    try:
        rank.main()
    finally:
        if previous_run is None:
            os.environ.pop("JOBINTEL_PIPELINE_RUN_ID", None)
        else:
            os.environ["JOBINTEL_PIPELINE_RUN_ID"] = previous_run

    with SessionLocal() as session:
        jobs = session.scalars(select(JobRecord).order_by(JobRecord.external_id)).all()
        raw = session.scalars(select(RawJobRecord)).all()
        ranking_ids = session.scalars(
            select(JobRankingRecord.job_id).where(
                JobRankingRecord.pipeline_run_id == run_id,
                JobRankingRecord.profile_name == PROFILE["name"],
            )
        ).all()
        result = {
            "run_id": run_id,
            "stored_jobs": [job.external_id for job in jobs],
            "raw_count": len(raw),
            "floors": [detect_min_experience(job.description or "") for job in jobs],
            "ranked_ids": ranking_ids,
        }
        if (
            result["stored_jobs"] != ["1", "2"]
            or len(raw) != 2
            or result["floors"] != [5, 2]
            or ranking_ids != [jobs[1].id]
        ):
            raise RuntimeError(f"Unexpected PostgreSQL state: {result}")
    if replay:
        finalize_pipeline_run(run_id, True)
    return result


@workflow.defn
class CachedReplay:
    def __init__(self):
        self.first = None
        self.resume = False

    @workflow.signal
    def continue_after_restart(self):
        self.resume = True

    @workflow.query
    def checkpoint(self):
        return self.first

    @workflow.run
    async def run(self):
        self.first = await workflow.execute_activity(
            cached_ingest_rank, 0, start_to_close_timeout=timedelta(minutes=2)
        )
        await workflow.wait_condition(lambda: self.resume)
        return await workflow.execute_activity(
            cached_ingest_rank,
            self.first["run_id"],
            start_to_close_timeout=timedelta(minutes=2),
        )


async def connect():
    address = os.environ["JOBINTEL_TEMPORAL_ADDRESS"]
    deadline = asyncio.get_running_loop().time() + 45
    while True:
        try:
            return await asyncio.wait_for(Client.connect(address), timeout=4)
        except (RuntimeError, TimeoutError):
            if asyncio.get_running_loop().time() >= deadline:
                raise
            await asyncio.sleep(1)


async def exercise(output_dir):
    from uuid import uuid4

    temporal = await connect()
    with SessionLocal() as session:
        if (
            session.bind.dialect.name != "postgresql"
            or session.scalar(
                text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")
            )
            != 1
        ):
            raise RuntimeError("Real PostgreSQL with pgvector is required")
        if session.scalar(text("SELECT count(*) FROM jobs")):
            raise RuntimeError("Acceptance requires a fresh disposable database")

    workers = []
    with (output_dir / "worker.log").open("x", encoding="utf-8") as log:
        try:

            def start():
                process = subprocess.Popen(
                    [sys.executable, __file__, "worker"], stdout=log, stderr=log
                )
                workers.append(process)
                return process

            first_worker = start()
            handle = await temporal.start_workflow(
                CachedReplay.run,
                id=f"cached-acceptance-{uuid4().hex}",
                task_queue=QUEUE,
                execution_timeout=timedelta(minutes=4),
            )
            first = None
            while first is None:
                first = await asyncio.wait_for(
                    handle.query(CachedReplay.checkpoint), timeout=100
                )
                if first is None:
                    if first_worker.poll() is not None:
                        raise RuntimeError("Initial worker exited before checkpoint")
                    await asyncio.sleep(0.25)
            first_worker.kill()
            first_worker.wait(timeout=10)
            second = start()
            await asyncio.wait_for(
                handle.signal(CachedReplay.continue_after_restart), timeout=15
            )
            after = await asyncio.wait_for(handle.result(), timeout=125)
            if first != after or first_worker.pid == second.pid:
                raise RuntimeError("Replay diverged from the persisted checkpoint")
            return {
                "workflow_id": handle.id,
                "worker_pids": [first_worker.pid, second.pid],
                "checkpoint": first,
                "after_replay": after,
            }
        finally:
            for worker in workers:
                if worker.poll() is None:
                    worker.terminate()
                    worker.wait(timeout=10)


def verify_api(url, result):
    with httpx.Client(base_url=url, timeout=10, trust_env=False) as http:
        anonymous = http.get("/rankings").status_code
        login = http.post(
            "/auth/login",
            json={
                "username": os.environ["JOBINTEL_AUTH_USERNAME"],
                "password": os.environ["JOBINTEL_AUTH_PASSWORD"],
            },
        )
        login.raise_for_status()
        me = http.get("/auth/me")
        me.raise_for_status()
        if (
            anonymous != 401
            or not login.json()["auth_enabled"]
            or not me.json()["authenticated"]
        ):
            raise RuntimeError("Signed session boundary failed")
        query = {
            "profile_name": PROFILE["name"],
            "pipeline_run_id": result["checkpoint"]["run_id"],
        }
        response = http.get("/rankings", params=query)
        other = http.get(
            "/rankings", params={**query, "profile_name": "unpopulated-secondary"}
        )
        response.raise_for_status()
        other.raise_for_status()
        ids = [item["job"]["id"] for item in response.json()["results"]]
        if ids != result["checkpoint"]["ranked_ids"] or other.json()["count"] != 0:
            raise RuntimeError("API ranking or profile filtering diverged")
        return {
            "anonymous_status": anonymous,
            "ranked_ids": ids,
            "other_profile_rows": 0,
        }


def wait_for_api(url):
    deadline = time.monotonic() + 35
    with httpx.Client(base_url=url, timeout=2, trust_env=False) as http:
        while time.monotonic() < deadline:
            try:
                if http.get("/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(1)
    raise RuntimeError("Application failed readiness on the isolated HTTP port")


async def start_worker():
    client = await connect()
    async with Worker(
        client,
        task_queue=QUEUE,
        workflows=[CachedReplay],
        activities=[cached_ingest_rank],
        workflow_runner=UnsandboxedWorkflowRunner(),
    ):
        await asyncio.Event().wait()


if __name__ == "__main__":
    if sys.argv[1:] == ["worker"]:
        asyncio.run(start_worker())
    elif len(sys.argv) == 3:
        directory = Path(sys.argv[1])
        wait_for_api(sys.argv[2])
        result = asyncio.run(exercise(directory))
        with (directory / "temporal-postgres.json").open(
            "x", encoding="utf-8"
        ) as output:
            json.dump(result, output, indent=2)
        result["http"] = verify_api(sys.argv[2], result)
        with (directory / "accepted.json").open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
    else:
        raise SystemExit("Usage: verify_cached_stack.py OUTPUT_DIR API_URL")
