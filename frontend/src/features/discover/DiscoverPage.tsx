import {
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  ExternalLink,
  MapPin,
  RefreshCw,
  Search,
  Sparkles,
  Target,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useQuery,
} from "@tanstack/react-query";
import {
  useSearchParams,
} from "react-router-dom";

import { ScoreRing } from "../../components/effects/ScoreRing";
import { PageHeader } from "../../components/ui/PageHeader";
import { Skeleton } from "../../components/ui/Skeleton";
import {
  fetchDiscoverJobs,
  type RankingBucket,
  type RankingResult,
} from "./discoverApi";

type BucketFilter =
  | "all"
  | RankingBucket;

const bucketOrder: Record<
  RankingBucket,
  number
> = {
  high_confidence: 0,
  discovery: 1,
  stretch: 2,
};

function bucketLabel(
  bucket: RankingBucket,
): string {
  switch (bucket) {
    case "high_confidence":
      return "High confidence";

    case "discovery":
      return "Discovery";

    case "stretch":
      return "Stretch";
  }
}

function bucketClass(
  bucket: RankingBucket,
): string {
  return `bucket-${bucket}`;
}

function formatRelativeDate(
  value: string | null,
): string {
  if (!value) {
    return "Date unavailable";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Date unavailable";
  }

  const difference =
    Date.now() -
    date.getTime();

  const minutes =
    Math.floor(
      difference / 60_000,
    );

  if (minutes < 60) {
    return `${Math.max(
      minutes,
      1,
    )}m ago`;
  }

  const hours =
    Math.floor(
      minutes / 60,
    );

  if (hours < 24) {
    return `${hours}h ago`;
  }

  const days =
    Math.floor(
      hours / 24,
    );

  if (days < 30) {
    return `${days}d ago`;
  }

  return date.toLocaleDateString();
}

function scoreLabel(
  score: number,
): string {
  if (score >= 75) {
    return "Excellent match";
  }

  if (score >= 65) {
    return "Strong match";
  }

  if (score >= 55) {
    return "Good match";
  }

  return "Relevant";
}

function parseJobId(
  value: string | null,
): number | null {
  if (!value) {
    return null;
  }

  const parsed =
    Number(value);

  if (
    !Number.isFinite(
      parsed,
    ) ||
    parsed <= 0
  ) {
    return null;
  }

  return parsed;
}

function DiscoverLoading() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Discover"
        title="One feed. Every relevant opportunity."
        description="Loading the latest ranked opportunities."
      />

      <div className="discover-toolbar">
        <div className="discover-search">
          <Skeleton className="skeleton skeleton-line skeleton-full" />
        </div>

        <Skeleton className="skeleton skeleton-line" />
        <Skeleton className="skeleton skeleton-line" />
        <Skeleton className="skeleton skeleton-line" />
      </div>

      <div className="discover-layout">
        <div className="job-list">
          {Array.from({
            length: 4,
          }).map(
            (
              _,
              index,
            ) => (
              <article
                className="job-card job-card-enhanced skeleton-job-card"
                key={index}
              >
                <div className="job-score-column">
                  <Skeleton className="skeleton skeleton-score" />
                </div>

                <div className="job-card-main">
                  <Skeleton className="skeleton skeleton-line skeleton-short" />

                  <div style={{ marginTop: 12 }}>
                    <Skeleton className="skeleton skeleton-title" />
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <Skeleton className="skeleton skeleton-line skeleton-medium" />
                  </div>

                  <div style={{ marginTop: 18 }}>
                    <Skeleton className="skeleton skeleton-line skeleton-full" />
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <Skeleton className="skeleton skeleton-line skeleton-medium" />
                  </div>
                </div>
              </article>
            ),
          )}
        </div>

        <aside className="job-preview skeleton-preview">
          <div className="preview-content">
            <div className="preview-hero">
              <Skeleton className="skeleton skeleton-score" />

              <div className="preview-hero-copy">
                <Skeleton className="skeleton skeleton-line skeleton-short" />

                <div style={{ marginTop: 10 }}>
                  <Skeleton className="skeleton skeleton-title" />
                </div>

                <div style={{ marginTop: 10 }}>
                  <Skeleton className="skeleton skeleton-line skeleton-medium" />
                </div>
              </div>
            </div>

            <div style={{ marginTop: 26 }}>
              {Array.from({
                length: 5,
              }).map(
                (
                  _,
                  index,
                ) => (
                  <div
                    key={index}
                    style={{
                      marginBottom:
                        18,
                    }}
                  >
                    <Skeleton className="skeleton skeleton-line skeleton-full" />
                  </div>
                ),
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export function DiscoverPage() {
  const [
    searchText,
    setSearchText,
  ] = useState("");

  const [
    bucketFilter,
    setBucketFilter,
  ] = useState<BucketFilter>(
    "all",
  );

  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams();

  const jobIdFromUrl =
    useMemo(
      () =>
        parseJobId(
          searchParams.get(
            "job",
          ),
        ),
      [
        searchParams,
      ],
    );

  const selectedJobId =
  jobIdFromUrl;


  const query =
    useQuery({
      queryKey: [
        "discover-rankings",
        "universal",
      ],
      queryFn:
        fetchDiscoverJobs,
      staleTime: 60_000,
    });



  const filteredJobs =
    useMemo(() => {
      const jobs =
        query.data
          ?.results ?? [];

      const normalizedSearch =
        searchText
          .trim()
          .toLowerCase();

      return jobs
        .filter(
          (
            result,
          ) => {
            if (
              bucketFilter !==
                "all" &&
              result.ranking
                .bucket !==
                bucketFilter
            ) {
              return false;
            }

            if (
              !normalizedSearch
            ) {
              return true;
            }

            const searchable =
              [
                result.job
                  .title,
                result.job
                  .company,
                result.job
                  .location ??
                  "",
                result.ranking
                  .bucket,
              ]
                .join(" ")
                .toLowerCase();

            return searchable.includes(
              normalizedSearch,
            );
          },
        )
        .sort(
          (
            left,
            right,
          ) => {
            const bucketDifference =
              bucketOrder[
                left.ranking
                  .bucket
              ] -
              bucketOrder[
                right.ranking
                  .bucket
              ];

            if (
              bucketDifference !==
              0
            ) {
              return bucketDifference;
            }

            return (
              right.ranking
                .score -
              left.ranking
                .score
            );
          },
        );
    }, [
      query.data,
      searchText,
      bucketFilter,
    ]);

  const selectedJob =
    query.data
      ?.results.find(
        (
          result,
        ) =>
          result.job.id ===
          selectedJobId,
      ) ??
    null;

  useEffect(() => {
    if (
      selectedJobId ===
        null ||
      !query.data
    ) {
      return;
    }

    const timer =
      window.setTimeout(
        () => {
          const element =
            document.querySelector(
              `[data-job-id="${selectedJobId}"]`,
            );

          if (
            element instanceof
            HTMLElement
          ) {
            element.scrollIntoView({
              behavior:
                "smooth",
              block:
                "center",
            });
          }
        },
        120,
      );

    return () => {
      window.clearTimeout(
        timer,
      );
    };
  }, [
    selectedJobId,
    query.data,
  ]);

function selectJob(
  result: RankingResult,
) {
  const nextParams =
    new URLSearchParams(
      searchParams,
    );

  nextParams.set(
    "job",
    String(
      result.job.id,
    ),
  );

  setSearchParams(
    nextParams,
    {
      replace: true,
    },
  );
}

  if (
    query.isLoading
  ) {
    return (
      <DiscoverLoading />
    );
  }

  if (
    query.isError
  ) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Discover"
          title="One feed. Every relevant opportunity."
          description="Ranked opportunities from your latest intelligence run."
        />

        <div className="empty-state">
          <BriefcaseBusiness
            size={24}
          />

          <h2>
            Unable to load jobs
          </h2>

          <p>
            {query.error instanceof
            Error
              ? query.error
                  .message
              : "The ranking API could not be reached."}
          </p>

          <button
            className="primary-action"
            onClick={() => {
              void query.refetch();
            }}
          >
            <RefreshCw
              size={16}
            />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const counts =
    query.data?.counts ?? {
      high_confidence:
        0,
      discovery:
        0,
      stretch:
        0,
    };

  const totalJobs =
    query.data?.results
      .length ?? 0;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Discover"
        title="One feed. Every relevant opportunity."
        description={`Latest universal-profile ranking run ${
          query.data
            ?.pipelineRunId ??
          "—"
        } · ${totalJobs} relevant opportunities`}
      />

      <div className="discover-toolbar">
        <div className="discover-search">
          <Search
            size={17}
          />

          <input
            value={
              searchText
            }
            onChange={(
              event,
            ) =>
              setSearchText(
                event.target
                  .value,
              )
            }
            placeholder="Search role, company, location..."
          />
        </div>

        <button
          className={
            bucketFilter ===
            "all"
              ? "primary-action"
              : "secondary-button"
          }
          onClick={() =>
            setBucketFilter(
              "all",
            )
          }
        >
          All
          <span>
            {totalJobs}
          </span>
        </button>

        <button
          className={
            bucketFilter ===
            "high_confidence"
              ? "primary-action"
              : "secondary-button"
          }
          onClick={() =>
            setBucketFilter(
              "high_confidence",
            )
          }
        >
          <CheckCircle2
            size={16}
          />

          High confidence

          <span>
            {
              counts.high_confidence
            }
          </span>
        </button>

        <button
          className={
            bucketFilter ===
            "discovery"
              ? "primary-action"
              : "secondary-button"
          }
          onClick={() =>
            setBucketFilter(
              "discovery",
            )
          }
        >
          <Sparkles
            size={16}
          />

          Discovery

          <span>
            {
              counts.discovery
            }
          </span>
        </button>

        <button
          className={
            bucketFilter ===
            "stretch"
              ? "primary-action"
              : "secondary-button"
          }
          onClick={() =>
            setBucketFilter(
              "stretch",
            )
          }
        >
          <Target
            size={16}
          />

          Stretch

          <span>
            {counts.stretch}
          </span>
        </button>
      </div>

      <div className="discover-layout">
        <div className="job-list">
          {filteredJobs.length ===
          0 ? (
            <div className="empty-state">
              <Search
                size={22}
              />

              <h2>
                No matching jobs
              </h2>

              <p>
                Try another search
                or switch ranking
                buckets.
              </p>
            </div>
          ) : (
            filteredJobs.map(
              (
                result,
                index,
              ) => {
                const {
                  ranking,
                  job,
                } = result;

                const selected =
                  selectedJobId ===
                  job.id;

                const animateEntry =
                  index < 12;

                return (
                  <article
                    data-job-id={
                      job.id
                    }
                    className={[
                      "job-card",
                      "job-card-enhanced",
                      bucketClass(
                        ranking.bucket,
                      ),
                      selected
                        ? "job-card-selected"
                        : "",
                      animateEntry
                        ? "job-card-enter"
                        : "",
                    ]
                      .filter(
                        Boolean,
                      )
                      .join(" ")}
                    style={
                      animateEntry
                        ? {
                            animationDelay:
                              `${Math.min(
                                index *
                                  35,
                                300,
                              )}ms`,
                          }
                        : undefined
                    }
                    key={
                      ranking.id
                    }
                    onClick={() =>
                      selectJob(
                        result,
                      )
                    }
                  >
                    <div className="job-score-column">
                      <ScoreRing
                        score={
                          ranking.score
                        }
                        bucket={
                          ranking.bucket
                        }
                      />
                    </div>

                    <div className="job-card-main">
                      <div className="job-card-heading">
                        <div>
                          <div className="job-company">
                            {
                              job.company
                            }
                          </div>

                          <h2>
                            {
                              job.title
                            }
                          </h2>
                        </div>

                        <span
                          className={[
                            "tag",
                            "bucket-badge",
                            bucketClass(
                              ranking.bucket,
                            ),
                          ].join(
                            " ",
                          )}
                        >
                          {bucketLabel(
                            ranking.bucket,
                          )}
                        </span>
                      </div>

                      <div className="job-meta">
                        <span>
                          <MapPin
                            size={14}
                          />

                          {job.location ??
                            "Location unavailable"}
                        </span>

                        <span>
                          ·
                        </span>

                        <span>
                          <Clock3
                            size={14}
                          />

                          {formatRelativeDate(
                            job.posted_at ??
                              job.first_seen_at,
                          )}
                        </span>
                      </div>

                      <div className="job-source-row">
                        <span>
                          {scoreLabel(
                            ranking.score,
                          )}
                        </span>

                        <span>
                          Gap{" "}
                          {ranking.gap_score.toFixed(
                            1,
                          )}
                        </span>

                        <span>
                          Semantic{" "}
                          {ranking.semantic_score.toFixed(
                            1,
                          )}
                        </span>
                      </div>

                      <div className="tag-row">
                        <span className="tag">
                          Deterministic{" "}
                          {ranking.deterministic_score.toFixed(
                            1,
                          )}
                        </span>

                        <span className="tag">
                          Rank #
                          {
                            ranking.rank_position
                          }
                        </span>

                        <span className="tag">
                          Run{" "}
                          {
                            ranking.pipeline_run_id
                          }
                        </span>
                      </div>

                      <div className="job-card-actions">
                        <button
                          className="secondary-button"
                          onClick={(
                            event,
                          ) => {
                            event.stopPropagation();

                            selectJob(
                              result,
                            );
                          }}
                        >
                          <BriefcaseBusiness
                            size={
                              16
                            }
                          />
                          Analyze
                        </button>

                        <a
                          className="primary-action"
                          href={
                            job.url
                          }
                          target="_blank"
                          rel="noreferrer"
                          onClick={(
                            event,
                          ) =>
                            event.stopPropagation()
                          }
                        >
                          Apply

                          <ArrowUpRight
                            size={
                              16
                            }
                          />
                        </a>
                      </div>
                    </div>
                  </article>
                );
              },
            )
          )}
        </div>

        <aside className="job-preview">
          {selectedJob ? (
            <div
              className="preview-content preview-content-enter"
              key={
                selectedJob
                  .job.id
              }
            >
              <div className="preview-hero">
                <ScoreRing
                  score={
                    selectedJob
                      .ranking
                      .score
                  }
                  bucket={
                    selectedJob
                      .ranking
                      .bucket
                  }
                  size="large"
                />

                <div className="preview-hero-copy">
                  <div className="job-company">
                    {
                      selectedJob
                        .job
                        .company
                    }
                  </div>

                  <h2>
                    {
                      selectedJob
                        .job
                        .title
                    }
                  </h2>

                  <div className="job-meta">
                    <MapPin
                      size={15}
                    />

                    <span>
                      {selectedJob
                        .job
                        .location ??
                        "Location unavailable"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="tag-row">
                <span
                  className={[
                    "tag",
                    "bucket-badge",
                    bucketClass(
                      selectedJob
                        .ranking
                        .bucket,
                    ),
                  ].join(
                    " ",
                  )}
                >
                  {bucketLabel(
                    selectedJob
                      .ranking
                      .bucket,
                  )}
                </span>

                <span className="tag">
                  Bucket rank #
                  {
                    selectedJob
                      .ranking
                      .rank_position
                  }
                </span>
              </div>

              <div className="preview-section">
                <h3>
                  Match intelligence
                </h3>

                <div className="metric-row">
                  <span>
                    Overall match
                  </span>

                  <strong>
                    {selectedJob.ranking.score.toFixed(
                      1,
                    )}
                  </strong>
                </div>

                <div className="preview-meter">
                  <span
                    style={{
                      width:
                        `${Math.min(
                          100,
                          selectedJob
                            .ranking
                            .score,
                        )}%`,
                    }}
                  />
                </div>

                <div className="metric-row">
                  <span>
                    Deterministic
                  </span>

                  <strong>
                    {selectedJob.ranking.deterministic_score.toFixed(
                      1,
                    )}
                  </strong>
                </div>

                <div className="metric-row">
                  <span>
                    Semantic
                  </span>

                  <strong>
                    {selectedJob.ranking.semantic_score.toFixed(
                      1,
                    )}
                  </strong>
                </div>

                <div className="metric-row">
                  <span>
                    Gap fit
                  </span>

                  <strong>
                    {selectedJob.ranking.gap_score.toFixed(
                      1,
                    )}
                  </strong>
                </div>
              </div>

              <div className="preview-section">
                <h3>
                  Opportunity
                </h3>

                <div className="metric-row">
                  <span>
                    Ranking bucket
                  </span>

                  <strong>
                    {bucketLabel(
                      selectedJob
                        .ranking
                        .bucket,
                    )}
                  </strong>
                </div>

                <div className="metric-row">
                  <span>
                    First discovered
                  </span>

                  <strong>
                    {formatRelativeDate(
                      selectedJob
                        .job
                        .first_seen_at,
                    )}
                  </strong>
                </div>

                <div className="metric-row">
                  <span>
                    Pipeline run
                  </span>

                  <strong>
                    #
                    {
                      selectedJob
                        .ranking
                        .pipeline_run_id
                    }
                  </strong>
                </div>
              </div>

              <a
                className="primary-action preview-apply"
                href={
                  selectedJob
                    .job.url
                }
                target="_blank"
                rel="noreferrer"
              >
                Open application

                <ExternalLink
                  size={16}
                />
              </a>
            </div>
          ) : (
            <div className="preview-empty">
              <div className="preview-symbol">
                <BriefcaseBusiness
                  size={24}
                />
              </div>

              <h2>
                Select a job
              </h2>

              <p>
                Select an opportunity
                to inspect its ranking
                signals and application
                link.
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
