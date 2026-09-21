const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface LatestPipelineRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  success: boolean;
  jobs_fetched: number;
  active_jobs: number;
  eligible_jobs: number;
  rankings_persisted: number;
  error_message: string | null;
}

export interface HealthResponse {
  status: string;
  database: string;
  active_jobs: number;
  latest_pipeline_run: LatestPipelineRun | null;
}

export type RankingBucket =
  | "high_confidence"
  | "discovery"
  | "stretch";

export interface OverviewRanking {
  ranking: {
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
  };

  job: {
    id: number;
    title: string;
    company: string;
    location: string | null;
    url: string;
    is_active: boolean;
    posted_at: string | null;
    first_seen_at: string;
    last_seen_at: string;
  };
}

interface RankingStatsResponse {
  profile_name: string;
  pipeline_run_id: number | null;

  total: number;

  buckets: {
    high_confidence: number;
    discovery: number;
    stretch: number;

    [bucket: string]: number;
  };
}

interface ShortlistResponse {
  profile_name: string;
  pipeline_run_id: number | null;

  high_confidence: OverviewRanking[];
  discovery: OverviewRanking[];
  stretch: OverviewRanking[];
}

export interface OverviewData {
  health: HealthResponse;

  counts: {
    highConfidence: number;
    discovery: number;
    stretch: number;
    relevant: number;
  };

  priorities: OverviewRanking[];
}

async function fetchJson<T>(
  path: string,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
  );

  if (!response.ok) {
    throw new Error(
      `API request failed (${response.status})`,
    );
  }

  return response.json() as Promise<T>;
}

function shortlistUrl(): string {
  const params = new URLSearchParams({
    profile_name: "universal",

    high_confidence_limit: "5",
    discovery_limit: "5",
    stretch_limit: "5",
  });

  return `/shortlist?${params.toString()}`;
}

function rankingStatsUrl(): string {
  const params = new URLSearchParams({
    profile_name: "universal",
  });

  return `/rankings/stats?${params.toString()}`;
}

function prioritySort(
  left: OverviewRanking,
  right: OverviewRanking,
): number {
  const bucketPriority: Record<
    RankingBucket,
    number
  > = {
    high_confidence: 0,
    discovery: 1,
    stretch: 2,
  };

  const bucketDifference =
    bucketPriority[
      left.ranking.bucket
    ] -
    bucketPriority[
      right.ranking.bucket
    ];

  if (bucketDifference !== 0) {
    return bucketDifference;
  }

  return (
    right.ranking.score -
    left.ranking.score
  );
}

export async function fetchOverviewData(): Promise<OverviewData> {
  const [
    health,
    rankingStats,
    shortlist,
  ] = await Promise.all([
    fetchJson<HealthResponse>(
      "/health",
    ),

    fetchJson<RankingStatsResponse>(
      rankingStatsUrl(),
    ),

    fetchJson<ShortlistResponse>(
      shortlistUrl(),
    ),
  ]);

  const priorities = [
    ...shortlist.high_confidence,
    ...shortlist.discovery,
    ...shortlist.stretch,
  ]
    .sort(prioritySort)
    .slice(
      0,
      5,
    );

  return {
    health,

    counts: {
      highConfidence:
        rankingStats.buckets
          .high_confidence,

      discovery:
        rankingStats.buckets
          .discovery,

      stretch:
        rankingStats.buckets
          .stretch,

      relevant:
        rankingStats.total,
    },

    priorities,
  };
}
