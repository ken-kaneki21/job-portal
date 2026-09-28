import { apiRequest } from "../../lib/api";

export interface RankingMetrics {
  sample_count: number;
  positive_count: number;
  base_positive_rate: number;
  precision_at_k: Record<string, number>;
  recall_at_k: Record<string, number>;
  lift_at_k: Record<string, number>;
  pairwise_accuracy: number;
  ndcg_at_k: Record<string, number>;
  mrr: number;
}

export interface EvaluationResponse {
  sample_count: number;
  positive_outcomes: number;
  negative_outcomes: number;
  warning: string | null;
  variants: Array<{ variant: string; metrics: RankingMetrics }>;
}

export interface OutcomeSummary {
  sample_count: number;
  active: boolean;
  global_mean: number;
}

export interface PipelineRun {
  id: number;
  success: boolean;
  started_at: string;
  finished_at: string | null;
  jobs_fetched: number;
  active_jobs: number;
  rankings_persisted: number;
  quality_passed: boolean | null;
  quality_metrics: {
    embedding_coverage?: number;
    ranking_coverage?: number;
    failed_scans?: number;
    stale_jobs?: number;
  } | null;
}

export async function fetchAnalytics() {
  const [evaluation, outcomes, runs] = await Promise.all([
    apiRequest<EvaluationResponse>("/evaluation/ranking"),
    apiRequest<OutcomeSummary>("/outcomes/summary"),
    apiRequest<{ pipeline_runs: PipelineRun[] }>("/pipeline-runs?limit=10"),
  ]);
  return { evaluation, outcomes, runs: runs.pipeline_runs };
}
