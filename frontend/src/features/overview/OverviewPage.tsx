import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Database,
  RefreshCw,
  Sparkles,
  Target,
} from "lucide-react";
import {
  useQuery,
} from "@tanstack/react-query";
import {
  useNavigate,
} from "react-router-dom";

import { MetricCard } from "../../components/ui/MetricCard";
import { PageHeader } from "../../components/ui/PageHeader";
import { Skeleton } from "../../components/ui/Skeleton";
import {
  fetchOverviewData,
  type OverviewRanking,
  type RankingBucket,
} from "./overviewApi";

function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-IN",
  ).format(value);
}

function formatRelativeTime(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "—";
  }

  const milliseconds =
    Date.now() -
    date.getTime();

  const minutes =
    Math.max(
      1,
      Math.floor(
        milliseconds /
          60_000,
      ),
    );

  if (minutes < 60) {
    return `${minutes}m`;
  }

  const hours =
    Math.floor(
      minutes / 60,
    );

  if (hours < 24) {
    return `${hours}h`;
  }

  return `${Math.floor(
    hours / 24,
  )}d`;
}

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

function PriorityJob({
  result,
  onOpen,
}: {
  result: OverviewRanking;
  onOpen: () => void;
}) {
  const {
    ranking,
    job,
  } = result;

  return (
    <article
      className="priority-job"
      onClick={onOpen}
    >
      <div className="priority-score">
        <span>
          {ranking.score.toFixed(
            1,
          )}
        </span>

        <small>
          match
        </small>
      </div>

      <div className="priority-main">
        <div className="priority-topline">
          <div>
            <div className="job-company">
              {job.company}
            </div>

            <h3>
              {job.title}
            </h3>
          </div>

          <div className="job-age">
            <Clock3
              size={14}
            />

            {formatRelativeTime(
              job.posted_at ??
                job.first_seen_at,
            )}
          </div>
        </div>

        <div className="job-location">
          {job.location ??
            "Location unavailable"}
        </div>

        <div className="tag-row">
          <span className="tag tag-positive">
            {bucketLabel(
              ranking.bucket,
            )}
          </span>

          <span className="tag">
            Gap{" "}
            {ranking.gap_score.toFixed(
              1,
            )}
          </span>

          <span className="tag">
            Semantic{" "}
            {ranking.semantic_score.toFixed(
              1,
            )}
          </span>
        </div>
      </div>

      <button
        className="job-open-button"
        aria-label={`Open ${job.title}`}
        onClick={(
          event,
        ) => {
          event.stopPropagation();
          onOpen();
        }}
      >
        <ArrowRight
          size={17}
        />
      </button>
    </article>
  );
}

function OverviewLoading() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Command center"
        title="Your job search, prioritized."
        description="Loading your latest intelligence."
      />

      <section className="metric-grid">
        {Array.from({
          length: 4,
        }).map(
          (
            _,
            index,
          ) => (
            <div
              className="metric-card skeleton-metric"
              key={index}
            >
              <Skeleton className="skeleton skeleton-score" />

              <div style={{ marginTop: 18 }}>
                <Skeleton className="skeleton skeleton-line skeleton-short" />
              </div>

              <div style={{ marginTop: 12 }}>
                <Skeleton className="skeleton skeleton-title" />
              </div>

              <div style={{ marginTop: 14 }}>
                <Skeleton className="skeleton skeleton-line skeleton-medium" />
              </div>
            </div>
          ),
        )}
      </section>

      <section className="dashboard-grid">
        <div className="panel priority-panel">
          <div className="panel-heading">
            <div>
              <Skeleton className="skeleton skeleton-line skeleton-short" />

              <div style={{ marginTop: 10 }}>
                <Skeleton className="skeleton skeleton-title" />
              </div>
            </div>
          </div>

          <div className="priority-list">
            {Array.from({
              length: 4,
            }).map(
              (
                _,
                index,
              ) => (
                <div
                  className="priority-job"
                  key={index}
                >
                  <Skeleton className="skeleton skeleton-score" />

                  <div className="priority-main">
                    <Skeleton className="skeleton skeleton-line skeleton-short" />

                    <div style={{ marginTop: 10 }}>
                      <Skeleton className="skeleton skeleton-title" />
                    </div>

                    <div style={{ marginTop: 10 }}>
                      <Skeleton className="skeleton skeleton-line skeleton-medium" />
                    </div>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>

        <div className="side-stack">
          <div className="panel">
            <Skeleton className="skeleton skeleton-line skeleton-short" />

            <div style={{ marginTop: 12 }}>
              <Skeleton className="skeleton skeleton-title" />
            </div>

            <div style={{ marginTop: 24 }}>
              {Array.from({
                length: 3,
              }).map(
                (
                  _,
                  index,
                ) => (
                  <div
                    key={index}
                    style={{
                      marginBottom:
                        20,
                    }}
                  >
                    <Skeleton className="skeleton skeleton-line skeleton-medium" />

                    <div style={{ marginTop: 8 }}>
                      <Skeleton className="skeleton skeleton-line skeleton-short" />
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>

          <div className="panel intelligence-panel">
            <Skeleton className="skeleton skeleton-line skeleton-short" />

            <div style={{ marginTop: 12 }}>
              <Skeleton className="skeleton skeleton-title" />
            </div>

            <div style={{ marginTop: 14 }}>
              <Skeleton className="skeleton skeleton-line skeleton-medium" />
            </div>

            <div
              className="run-stats"
              style={{
                marginTop: 24,
              }}
            >
              {Array.from({
                length: 3,
              }).map(
                (
                  _,
                  index,
                ) => (
                  <div
                    key={index}
                  >
                    <Skeleton className="skeleton skeleton-line skeleton-short" />

                    <div style={{ marginTop: 8 }}>
                      <Skeleton className="skeleton skeleton-title" />
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export function OverviewPage() {
  const navigate =
    useNavigate();

  const query =
    useQuery({
      queryKey: [
        "overview",
        "universal",
      ],
      queryFn:
        fetchOverviewData,
      staleTime: 60_000,
    });

  if (
    query.isLoading
  ) {
    return (
      <OverviewLoading />
    );
  }

  if (
    query.isError ||
    !query.data
  ) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Command center"
          title="Your job search, prioritized."
          description="Review the latest intelligence from your job search pipeline."
        />

        <div className="empty-state">
          <Database
            size={24}
          />

          <h2>
            Unable to load overview
          </h2>

          <p>
            {query.error instanceof
            Error
              ? query.error
                  .message
              : "The API could not be reached."}
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

  const {
    health,
    counts,
    priorities,
  } = query.data;

  const latestRun =
    health.latest_pipeline_run;

  const runHealthy =
    latestRun?.success ===
    true;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Command center"
        title="Your job search, prioritized."
        description="Real-time intelligence from your latest normalized, enriched, and ranked job dataset."
        actions={
          <button
            className="primary-action"
            onClick={() =>
              navigate(
                "/discover",
              )
            }
          >
            Review opportunities

            <ArrowRight
              size={16}
            />
          </button>
        }
      />

      <section className="metric-grid">
        <MetricCard
          label="Active jobs"
          value={formatNumber(
            health.active_jobs,
          )}
          detail="Currently active across all sources"
          icon={BriefcaseBusiness}
        />

        <MetricCard
          label="Relevant"
          value={formatNumber(
            counts.relevant,
          )}
          detail="Matched to your universal profile"
          icon={Target}
        />

        <MetricCard
          label="High confidence"
          value={formatNumber(
            counts.highConfidence,
          )}
          detail="Priority opportunities to review first"
          icon={CheckCircle2}
        />

        <MetricCard
          label="Discovery"
          value={formatNumber(
            counts.discovery,
          )}
          detail={`${formatNumber(
            counts.stretch,
          )} additional stretch opportunities`}
          icon={Sparkles}
        />
      </section>

      <section className="dashboard-grid">
        <div className="panel priority-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">
                Priority queue
              </div>

              <h2>
                Best opportunities right now
              </h2>
            </div>

            <button
              className="ghost-button"
              onClick={() =>
                navigate(
                  "/discover",
                )
              }
            >
              View all

              <ArrowRight
                size={15}
              />
            </button>
          </div>

          <div className="priority-list">
            {priorities.length ===
            0 ? (
              <div className="empty-state">
                <Target
                  size={20}
                />

                <h3>
                  No ranked opportunities
                </h3>

                <p>
                  Run job intelligence
                  to generate matches.
                </p>
              </div>
            ) : (
              priorities.map(
                (
                  result,
                ) => (
                  <PriorityJob
                    key={
                      result.ranking.id
                    }
                    result={
                      result
                    }
                    onOpen={() =>
                      navigate(
                        `/discover?job=${result.job.id}`,
                      )
                    }
                  />
                ),
              )
            )}
          </div>
        </div>

        <div className="side-stack">
          <div className="panel">
            <div className="panel-kicker">
              Today
            </div>

            <h2>
              Next best actions
            </h2>

            <div className="action-list">
              <button
                className="action-row"
                onClick={() =>
                  navigate(
                    "/discover",
                  )
                }
              >
                <div className="action-icon">
                  <Target
                    size={17}
                  />
                </div>

                <div>
                  <strong>
                    Review{" "}
                    {
                      counts.highConfidence
                    }{" "}
                    high-confidence{" "}
                    {counts.highConfidence ===
                    1
                      ? "job"
                      : "jobs"}
                  </strong>

                  <span>
                    Highest-priority matches
                    from run{" "}
                    {latestRun?.id ??
                      "—"}
                  </span>
                </div>
              </button>

              <button
                className="action-row"
                onClick={() =>
                  navigate(
                    "/discover",
                  )
                }
              >
                <div className="action-icon">
                  <Sparkles
                    size={17}
                  />
                </div>

                <div>
                  <strong>
                    Explore{" "}
                    {formatNumber(
                      counts.discovery,
                    )}{" "}
                    discovery jobs
                  </strong>

                  <span>
                    Broader matches worth
                    reviewing
                  </span>
                </div>
              </button>

              <button
                className="action-row"
                onClick={() =>
                  navigate(
                    "/discover",
                  )
                }
              >
                <div className="action-icon">
                  <BriefcaseBusiness
                    size={17}
                  />
                </div>

                <div>
                  <strong>
                    Inspect{" "}
                    {formatNumber(
                      counts.stretch,
                    )}{" "}
                    stretch roles
                  </strong>

                  <span>
                    Higher-experience or
                    adjacent opportunities
                  </span>
                </div>
              </button>
            </div>
          </div>

          <div className="panel intelligence-panel">
            <div className="panel-kicker">
              Latest intelligence run
            </div>

            <div className="run-status-line">
              <div>
                <h2>
                  {runHealthy
                    ? "Completed successfully"
                    : latestRun
                      ? "Run needs attention"
                      : "No run available"}
                </h2>

                <p>
                  {latestRun
                    ? `Pipeline run ${latestRun.id}`
                    : "Start an intelligence run to generate results."}
                </p>
              </div>

              <span className="status-badge">
                {runHealthy
                  ? "Healthy"
                  : "Attention"}
              </span>
            </div>

            <div className="run-stats">
              <div>
                <span>
                  Fetched
                </span>

                <strong>
                  {formatNumber(
                    latestRun
                      ?.jobs_fetched ??
                      0,
                  )}
                </strong>
              </div>

              <div>
                <span>
                  Active
                </span>

                <strong>
                  {formatNumber(
                    latestRun
                      ?.active_jobs ??
                      health.active_jobs,
                  )}
                </strong>
              </div>

              <div>
                <span>
                  Relevant
                </span>

                <strong>
                  {formatNumber(
                    latestRun
                      ?.rankings_persisted ??
                      counts.relevant,
                  )}
                </strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
