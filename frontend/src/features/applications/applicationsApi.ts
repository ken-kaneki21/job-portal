import { apiRequest } from "../../lib/api";

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "rejected"
  | "offer";

export interface JobSummary {
  id: number;
  title: string;
  company: string;
  location: string | null;
  url: string;
  is_active: boolean;
  posted_at: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

export interface ApplicationState {
  id?: number;
  job_id: number;
  profile_name: string;
  status: ApplicationStatus | string;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ApplicationItem {
  job: JobSummary;
  state: ApplicationState;
}

interface ApplicationsResponse {
  applications: ApplicationItem[];
}

interface SavedJobsResponse {
  jobs: ApplicationItem[];
}

export interface ApplicationSummary {
  profile_name: string;
  counts: Record<string, number>;
}

export interface HistoryEvent {
  id: number;
  job_id: number;
  profile_name: string;
  previous_status: string | null;
  new_status: string;
  notes: string | null;
  source: string;
  created_at: string;
}

export interface ApplicationDetailResponse {
  job: Record<string, unknown>;
  state: ApplicationState;
  history: HistoryEvent[];
  application_assets: {
    recruiter_dm?: string;
    email_subject?: string;
    email_body?: string;
    cover_note?: string;
    resume_summary?: string;
    skills_to_emphasize?: string[];
    missing_skills_warning?: string[];
    interview_talking_points?: string[];
  } | null;
}

export interface ReadinessResponse {
  job_id: number;
  company: string;
  title: string;
  ready_for_review: boolean;
  auto_submit_allowed: boolean;
  blocking_issues: string[];
  checks: Array<{
    key: string;
    ok: boolean;
    blocking: boolean;
    message: string;
  }>;
}

export interface AnswerValue {
  key: string;
  value: string | number | null;
  source: string;
  sensitive: boolean;
  review_required: boolean;
}

export interface AnswersResponse {
  job_id: number;
  company: string;
  title: string;
  answers: Record<string, AnswerValue>;
  review_required: boolean;
}

export interface ApplicationBundle {
  applications: ApplicationItem[];
  summary: ApplicationSummary;
}

export async function fetchApplicationBundle(): Promise<ApplicationBundle> {
  const [saved, applications, summary] = await Promise.all([
    apiRequest<SavedJobsResponse>("/saved-jobs?limit=500"),
    apiRequest<ApplicationsResponse>("/applications?limit=500"),
    apiRequest<ApplicationSummary>("/application-state-summary"),
  ]);

  return {
    applications: [...saved.jobs, ...applications.applications],
    summary,
  };
}

export async function fetchApplicationDetail(
  jobId: number,
): Promise<ApplicationDetailResponse> {
  return apiRequest<ApplicationDetailResponse>(`/jobs/${jobId}`);
}

export async function fetchReadiness(
  jobId: number,
): Promise<ReadinessResponse> {
  return apiRequest<ReadinessResponse>(
    `/application-ops/jobs/${jobId}/readiness`,
  );
}

export async function fetchAnswers(jobId: number): Promise<AnswersResponse> {
  return apiRequest<AnswersResponse>(
    `/application-ops/jobs/${jobId}/answers`,
  );
}

export async function updateApplicationStatus(
  jobId: number,
  status: ApplicationStatus,
  notes: string | null,
): Promise<ApplicationState> {
  const response = await apiRequest<{ state: ApplicationState }>(
    `/application-ops/jobs/${jobId}/status`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status,
        notes,
      }),
    },
  );

  return response.state;
}
