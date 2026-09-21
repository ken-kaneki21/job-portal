const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type RankingBucket =
  | "high_confidence"
  | "discovery"
  | "stretch";

export interface RankingRecord {
  id: number;
  gap_score: number;
  job_id: number;
  profile_name: string;
  bucket: RankingBucket;
  score: number;
  deterministic_score: number;
  semantic_score: number;
  rank_position: number;
  ranked_at: string;
  pipeline_run_id: number;
}

export interface RankedJob {
  id: number;
  title: string;
  company: string;
  location: string | null;
  url: string;
  is_active: boolean;
  posted_at: string | null;
  first_seen_at: string;
  last_seen_at: string;
}

export interface RankingResult {
  ranking: RankingRecord;
  job: RankedJob;
}

interface RankingResponse {
  profile_name: string;
  pipeline_run_id: number | null;
  bucket: RankingBucket | null;
  count: number;
  results: RankingResult[];
}

async function fetchBucket(
  bucket: RankingBucket,
): Promise<RankingResponse> {
  const params = new URLSearchParams({
    profile_name: "universal",
    bucket,
    limit: "500",
  });

  const response = await fetch(
    `${API_BASE_URL}/rankings?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error(
      `Unable to load ${bucket} rankings (${response.status})`,
    );
  }

  return response.json() as Promise<RankingResponse>;
}

export interface DiscoverData {
  pipelineRunId: number | null;
  results: RankingResult[];
  counts: Record<RankingBucket, number>;
}

export async function fetchDiscoverJobs(): Promise<DiscoverData> {
  const [
    highConfidence,
    discovery,
    stretch,
  ] = await Promise.all([
    fetchBucket("high_confidence"),
    fetchBucket("discovery"),
    fetchBucket("stretch"),
  ]);

  const results = [
    ...highConfidence.results,
    ...discovery.results,
    ...stretch.results,
  ];

  return {
    pipelineRunId:
      highConfidence.pipeline_run_id ??
      discovery.pipeline_run_id ??
      stretch.pipeline_run_id ??
      null,

    results,

    counts: {
      high_confidence: highConfidence.count,
      discovery: discovery.count,
      stretch: stretch.count,
    },
  };
}
