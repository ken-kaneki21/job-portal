import { useEffect, useMemo, useState } from "react";
import { BarChart3, CheckCircle2, Database, Target } from "lucide-react";

import { MetricCard } from "../../components/ui/MetricCard";
import { PageHeader } from "../../components/ui/PageHeader";
import { fetchAnalytics, type EvaluationResponse, type OutcomeSummary, type PipelineRun } from "./analyticsApi";

type State = { evaluation: EvaluationResponse; outcomes: OutcomeSummary; runs: PipelineRun[] };

function percent(value: number | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function AnalyticsPage() {
  const [data, setData] = useState<State | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchAnalytics().then(setData).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load analytics");
    });
  }, []);

  const baseline = useMemo(
    () => data?.evaluation.variants.find((item) => item.variant === "stored_live_score"),
    [data],
  );
  const latest = data?.runs[0];

  return (
    <div className="page">
      <PageHeader
        eyebrow="Analytics"
        title="Ranking quality and pipeline health."
        description="Outcome-based ranking evaluation and data-quality snapshots from real pipeline runs."
      />

      {error ? <div className="empty-state"><h2>Analytics unavailable</h2><p>{error}</p></div> : null}

      {data ? (
        <>
          <div className="metric-grid">
            <MetricCard label="Completed outcomes" value={String(data.evaluation.sample_count)} detail="Recorded application outcomes" icon={Target} />
            <MetricCard label="MRR" value={baseline ? baseline.metrics.mrr.toFixed(3) : "—"} detail="Mean reciprocal rank" icon={BarChart3} />
            <MetricCard label="NDCG@10" value={percent(baseline?.metrics.ndcg_at_k["10"])} detail="Ranking quality at top 10" icon={CheckCircle2} />
            <MetricCard label="Latest data quality" value={latest?.quality_passed == null ? "Pending" : latest.quality_passed ? "Pass" : "Review"} detail="Latest pipeline quality gate" icon={Database} />
          </div>

          <div className="content-grid">
            <section className="panel">
              <h2>Ranking evaluation</h2>
              <p>{data.evaluation.warning ?? "Historical application outcomes are available for ranking evaluation."}</p>
              {data.evaluation.variants.map((variant) => (
                <div className="list-row" key={variant.variant}>
                  <strong>{variant.variant}</strong>
                  <span>NDCG@10 {percent(variant.metrics.ndcg_at_k["10"])} · MRR {variant.metrics.mrr.toFixed(3)} · Pairwise {percent(variant.metrics.pairwise_accuracy)}</span>
                </div>
              ))}
            </section>

            <section className="panel">
              <h2>Outcome learning</h2>
              <p>{data.outcomes.active ? "Outcome signals are active in ranking." : "Outcome learning activates after enough completed application outcomes accumulate."}</p>
              <div className="list-row"><strong>Samples</strong><span>{data.outcomes.sample_count}</span></div>
              <div className="list-row"><strong>Positive outcomes</strong><span>{data.evaluation.positive_outcomes}</span></div>
              <div className="list-row"><strong>Negative outcomes</strong><span>{data.evaluation.negative_outcomes}</span></div>
            </section>
          </div>

          <section className="panel">
            <h2>Recent pipeline quality</h2>
            {data.runs.map((run) => (
              <div className="list-row" key={run.id}>
                <strong>Run #{run.id} · {run.success ? "success" : "failed"}</strong>
                <span>{run.quality_metrics ? `embeddings ${percent(run.quality_metrics.embedding_coverage)} · ranking ${percent(run.quality_metrics.ranking_coverage)} · failed scans ${run.quality_metrics.failed_scans ?? 0}` : "quality snapshot available after next pipeline run"}</span>
              </div>
            ))}
          </section>
        </>
      ) : !error ? <div className="empty-state"><BarChart3 size={24} /><h2>Loading analytics…</h2></div> : null}
    </div>
  );
}
