import { apiRequest } from "../../lib/api";

export type PipelineStartResponse = {
  message: string;
  workflow_id: string;
  temporal_managed: boolean;
  task_queue?: string;
};

export type WorkflowStatusResponse = {
  workflow_id: string;
  status: string;

  workflow_type?: string | null;
  run_id?: string | null;
  task_queue?: string | null;

  start_time?: string | null;
  close_time?: string | null;

  temporal_managed?: boolean;

  result?: unknown;
  error?: string | null;
};

export type LatestPipelineRun = {
  id: number;
  started_at: string;
  finished_at: string | null;

  success: boolean;

  jobs_fetched: number;
  active_jobs: number;
  eligible_jobs: number;
  rankings_persisted: number;

  error_message: string | null;
};

export type HealthResponse = {
  status: string;
  database: string;
  active_jobs: number;

  latest_pipeline_run:
    | LatestPipelineRun
    | null;
};

export async function startPipeline(): Promise<PipelineStartResponse> {
  return apiRequest<PipelineStartResponse>(
    "/pipeline/run-temporal",
    {
      method: "POST",
    },
  );
}

export async function getWorkflowStatus(
  workflowId: string,
): Promise<WorkflowStatusResponse> {
  return apiRequest<WorkflowStatusResponse>(
    `/temporal/workflows/${encodeURIComponent(
      workflowId,
    )}`,
  );
}

export async function getPipelineHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(
    "/health",
  );
}
