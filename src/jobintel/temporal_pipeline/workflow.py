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


# ---------------------------------------------------------
# Pipeline step policy
# ---------------------------------------------------------
#
# Critical:
# If one of these fails after Temporal retries,
# the whole pipeline should fail.
#
# Best effort:
# If one of these fails after retries,
# record the warning and continue.
#
# This keeps transient third-party/search/notification
# problems from blocking the core job intelligence system.
# ---------------------------------------------------------


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
    @workflow.run
    async def run(self) -> dict:
        # -------------------------------------------------
        # Create pipeline run
        # -------------------------------------------------

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

        warnings: list[dict] = []

        workflow.logger.info(
            "Starting Job Intelligence pipeline run %s",
            run_id,
        )

        try:
            # ---------------------------------------------
            # Execute pipeline steps
            # ---------------------------------------------

            for label, module in STEPS:
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
                        start_to_close_timeout=(timedelta(hours=2)),
                        retry_policy=RetryPolicy(
                            maximum_attempts=3,
                            initial_interval=(timedelta(seconds=10)),
                            maximum_interval=(timedelta(minutes=5)),
                            backoff_coefficient=2.0,
                        ),
                    )

                    completed_steps.append(label)

                    workflow.logger.info(
                        "Completed step: %s",
                        label,
                    )

                except Exception as exc:
                    error_message = str(exc)

                    # -------------------------------------
                    # Best-effort step
                    # -------------------------------------

                    if is_best_effort_step(label):
                        workflow.logger.warning(
                            "Best-effort step failed after retries: %s",
                            label,
                        )

                        skipped_steps.append(label)

                        warnings.append(
                            {
                                "step": label,
                                "module": module,
                                "error": (error_message),
                            }
                        )

                        continue

                    # -------------------------------------
                    # Critical step
                    # -------------------------------------

                    workflow.logger.error(
                        "Critical step failed: %s",
                        label,
                    )

                    raise RuntimeError(
                        f"Critical pipeline step failed: {label}. {error_message}"
                    ) from exc

            # ---------------------------------------------
            # Successful pipeline
            # ---------------------------------------------

            await workflow.execute_activity(
                finalize_pipeline_run_activity,
                FinalizePipelineInput(
                    run_id=run_id,
                    success=True,
                    error_message=None,
                ),
                start_to_close_timeout=(timedelta(minutes=2)),
                retry_policy=RetryPolicy(
                    maximum_attempts=5,
                    initial_interval=(timedelta(seconds=2)),
                    maximum_interval=(timedelta(seconds=30)),
                    backoff_coefficient=2.0,
                ),
            )

            workflow.logger.info(
                "Pipeline run %s completed",
                run_id,
            )

            return {
                "pipeline_run_id": run_id,
                "success": True,
                "completed_steps": (completed_steps),
                "skipped_steps": (skipped_steps),
                "warnings": warnings,
                "warning_count": len(warnings),
            }

        except Exception as exc:
            # ---------------------------------------------
            # Failed pipeline
            # ---------------------------------------------

            error_message = str(exc)

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
                        error_message=(error_message),
                    ),
                    start_to_close_timeout=(timedelta(minutes=2)),
                    retry_policy=RetryPolicy(
                        maximum_attempts=5,
                        initial_interval=(timedelta(seconds=2)),
                        maximum_interval=(timedelta(seconds=30)),
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
