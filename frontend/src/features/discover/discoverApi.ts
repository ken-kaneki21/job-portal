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
  returned_count: number;
  offset: number;
  limit: number;
  results: RankingResult[];
}

const PAGE_SIZE = 500;

async function fetchBucketPage(
  bucket: RankingBucket,
  offset: number,
): Promise<RankingResponse> {
  const params = new URLSearchParams({
    profile_name: "universal",
    bucket,
    limit: String(PAGE_SIZE),
    offset: String(offset),
  });

  const response = await fetch(
    `${API_BASE_URL}/rankings?${params.toString()}`,
    { credentials: "include" },
  );

  if (!response.ok) {
    throw new Error(
      `Unable to load ${bucket} rankings (${response.status})`,
    );
  }

  return response.json() as Promise<RankingResponse>;
}

async function fetchBucket(
  bucket: RankingBucket,
): Promise<RankingResponse> {
  const firstPage = await fetchBucketPage(bucket, 0);

  if (
    firstPage.returned_count >= firstPage.count ||
    firstPage.results.length === 0
  ) {
    return firstPage;
  }

  const offsets: number[] = [];

  for (
    let offset = PAGE_SIZE;
    offset < firstPage.count;
    offset += PAGE_SIZE
  ) {
    offsets.push(offset);
  }

  const pages = await Promise.all(
    offsets.map((offset) =>
      fetchBucketPage(bucket, offset),
    ),
  );

  const results = [
    ...firstPage.results,
    ...pages.flatMap((page) => page.results),
  ];

  return {
    ...firstPage,
    returned_count: results.length,
    results,
  };
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

  return {
    pipelineRunId:
      highConfidence.pipeline_run_id ??
      discovery.pipeline_run_id ??
      stretch.pipeline_run_id ??
      null,

    results: [
      ...highConfidence.results,
      ...discovery.results,
      ...stretch.results,
    ],

    counts: {
      high_confidence: highConfidence.count,
      discovery: discovery.count,
      stretch: stretch.count,
    },
  };
}
