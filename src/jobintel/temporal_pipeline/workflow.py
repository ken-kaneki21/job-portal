from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from jobintel.pipeline import STEPS
    from jobintel.temporal_pipeline.activities import (
        FinalizePipelineInput,
        PipelineStepInput,
        create_pipeline_run_activity,
        finalize_pipeline_run_activity,
        run_pipeline_step_activity,
    )


CRITICAL_STEPS = {
    "Direct ATS ingestion",
    "JD enrichment",
    "Refresh job embeddings",
    "Candidate JD gap analysis",
    "Ranking",
    "Data quality checks",
}


BEST_EFFORT_STEPS = {
    "Broad search",
    "Queue company discovery candidates",
    "Resolve company ATS",
    "Generate application assets",
    "Daily shortlist",
    "Daily email digest",
    "New high-confidence jobs",
    "Queue notifications",
    "Retry failed notifications",
    "Deliver notifications",
}


def is_best_effort_step(
    label: str,
) -> bool:
    return label in BEST_EFFORT_STEPS


@workflow.defn
class JobIntelligencePipelineWorkflow:
    _total_steps: int
    _completed_steps_count: int
    _current_step_index: int
    _current_step: str

    def __init__(self) -> None:
        self._total_steps = len(STEPS)
        self._completed_steps_count = 0
        self._current_step_index = 0
        self._current_step = "Starting pipeline"

    @workflow.query
    def progress(self) -> dict[str, int | float | str]:
        percent = 0.0

        if self._total_steps > 0:
            percent = round(
                min(
                    100.0,
                    (self._completed_steps_count / self._total_steps) * 100.0,
                ),
                1,
            )

        return {
            "current_step": self._current_step,
            "current_step_index": self._current_step_index,
            "completed_steps": self._completed_steps_count,
            "total_steps": self._total_steps,
            "percent": percent,
        }

    @workflow.run
    async def run(self) -> dict[str, object]:
        self._total_steps = len(STEPS)
        self._completed_steps_count = 0
        self._current_step_index = 0
        self._current_step = "Creating pipeline run"

        run_id = await workflow.execute_activity(
            create_pipeline_run_activity,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=15),
                backoff_coefficient=2.0,
            ),
        )

        completed_steps: list[str] = []
        skipped_steps: list[str] = []
        warnings: list[dict[str, str]] = []

        workflow.logger.info(
            "Starting Job Intelligence pipeline run %s",
            run_id,
        )

        try:
            for index, (label, module) in enumerate(
                STEPS,
                start=1,
            ):
                self._current_step_index = index
                self._current_step = label

                workflow.logger.info(
                    "Starting step: %s",
                    label,
                )

                try:
                    await workflow.execute_activity(
                        run_pipeline_step_activity,
                        PipelineStepInput(
                            run_id=run_id,
                            label=label,
                            module=module,
                        ),
                        start_to_close_timeout=timedelta(hours=2),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=timedelta(seconds=10),
                            maximum_interval=timedelta(minutes=5),
                            backoff_coefficient=2.0,
                        ),
                    )

                    completed_steps.append(label)
                    self._completed_steps_count = len(completed_steps)

                    workflow.logger.info(
                        "Completed step: %s",
                        label,
                    )

                except Exception as exc:
                    error_message = str(exc)

                    if is_best_effort_step(label):
                        workflow.logger.warning(
                            "Best-effort step failed after retries: %s",
                            label,
                        )

                        skipped_steps.append(label)

                        self._completed_steps_count = len(completed_steps) + len(
                            skipped_steps
                        )

                        warnings.append(
                            {
                                "step": label,
                                "module": module,
                                "error": error_message,
                            }
                        )

                        continue

                    workflow.logger.error(
                        "Critical step failed: %s",
                        label,
                    )

                    raise RuntimeError(
                        "Critical pipeline step failed: " f"{label}. {error_message}"
                    ) from exc

            self._current_step = "Finalizing pipeline"

            await workflow.execute_activity(
                finalize_pipeline_run_activity,
                FinalizePipelineInput(
                    run_id=run_id,
                    success=True,
                    error_message=None,
                ),
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(
                    maximum_attempts=5,
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    backoff_coefficient=2.0,
                ),
            )

            self._completed_steps_count = self._total_steps
            self._current_step = "Completed"

            workflow.logger.info(
                "Pipeline run %s completed",
                run_id,
            )

            return {
                "pipeline_run_id": run_id,
                "success": True,
                "completed_steps": completed_steps,
                "skipped_steps": skipped_steps,
                "warnings": warnings,
                "warning_count": len(warnings),
            }

        except Exception as exc:
            error_message = str(exc)
            self._current_step = "Failed"

            workflow.logger.error(
                "Pipeline run %s failed: %s",
                run_id,
                error_message,
            )

            try:
                await workflow.execute_activity(
                    finalize_pipeline_run_activity,
                    FinalizePipelineInput(
                        run_id=run_id,
                        success=False,
                        error_message=error_message,
                    ),
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(
                        maximum_attempts=5,
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        backoff_coefficient=2.0,
                    ),
                )
            except Exception as finalize_exc:
                workflow.logger.error(
                    "Unable to finalize failed pipeline run %s: %s",
                    run_id,
                    finalize_exc,
                )

            raise
