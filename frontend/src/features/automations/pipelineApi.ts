
import { apiRequest } from "../../lib/api";

export type PipelineStartResponse = {
  message: string;
  workflow_id: string;
  temporal_managed: boolean;
  task_queue?: string;
};

export type WorkflowProgress = {
  current_step: string;
  current_step_index: number;
  completed_steps: number;
  total_steps: number;
  percent: number;
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
  progress?: WorkflowProgress | null;
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
  latest_pipeline_run: LatestPipelineRun | null;
};

export type DailySchedule = {
  exists: boolean;
  schedule_id: string;
  enabled: boolean;
  hour: number;
  minute: number;
  timezone: string;
  send_digest: boolean;
  next_run_at: string | null;
  next_action_times: string[];
  num_actions: number;
  num_actions_missed_catchup_window: number;
  num_actions_skipped_overlap: number;
  running_actions: number;
  task_queue: string;
  overlap_policy: "skip";
};

export type DailyScheduleUpdate = {
  enabled: boolean;
  hour: number;
  minute: number;
  timezone: string;
  send_digest: boolean;
};

export async function startPipeline(): Promise<PipelineStartResponse> {
  return apiRequest<PipelineStartResponse>("/pipeline/run-temporal", {
    method: "POST",
  });
}

export async function getWorkflowStatus(
  workflowId: string,
): Promise<WorkflowStatusResponse> {
  return apiRequest<WorkflowStatusResponse>(
    `/temporal/workflows/${encodeURIComponent(workflowId)}`,
  );
}

export async function getPipelineHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export async function getDailySchedule(): Promise<DailySchedule> {
  return apiRequest<DailySchedule>("/temporal/schedules/daily");
}

export async function saveDailySchedule(
  update: DailyScheduleUpdate,
): Promise<DailySchedule> {
  return apiRequest<DailySchedule>("/temporal/schedules/daily", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
}

export async function pauseDailySchedule(): Promise<DailySchedule> {
  return apiRequest<DailySchedule>("/temporal/schedules/daily/pause", {
    method: "POST",
  });
}

export async function resumeDailySchedule(): Promise<DailySchedule> {
  return apiRequest<DailySchedule>("/temporal/schedules/daily/resume", {
    method: "POST",
  });
}

export async function triggerDailySchedule(): Promise<{
  message: string;
  schedule_id: string;
}> {
  return apiRequest("/temporal/schedules/daily/trigger", {
    method: "POST",
  });
}
