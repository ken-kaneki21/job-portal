import {
  CheckCircle2,
  Clock3,
  LoaderCircle,
  Mail,
  Play,
  RefreshCw,
  Workflow,
} from "lucide-react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import {
  getPipelineHealth,
  startPipeline,
} from "./pipelineApi";
import { fetchSettingsStatus } from "../settings/settingsApi";

export function AutomationsPage() {
  const queryClient =
    useQueryClient();

  const health =
    useQuery({
      queryKey: [
        "pipeline-health",
      ],
      queryFn:
        getPipelineHealth,
      refetchInterval: 15_000,
    });

  const settings =
    useQuery({
      queryKey: [
        "settings-status",
      ],
      queryFn:
        fetchSettingsStatus,
      staleTime: 30_000,
    });

  const runMutation =
    useMutation({
      mutationFn:
        startPipeline,
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: [
            "pipeline-health",
          ],
        });
      },
    });

  const latest =
    health.data
      ?.latest_pipeline_run;

  const runActive =
    latest != null &&
    latest.finished_at === null;

  const runNow = () => {
    if (
      runActive ||
      runMutation.isPending
    ) {
      return;
    }

    runMutation.mutate();
  };

  return (
    <div className="page">
      <PageHeader
        eyebrow="Automations"
        title="Control the entire pipeline here."
        description="Run and inspect the production workflow without terminal commands."
        actions={
          <button
            className="primary-action"
            onClick={runNow}
            disabled={
              runActive ||
              runMutation.isPending
            }
          >
            {runMutation.isPending ? (
              <LoaderCircle
                size={16}
                className="run-status-spinner"
              />
            ) : (
              <Play
                size={16}
                fill="currentColor"
              />
            )}
            {runActive
              ? "Pipeline running"
              : "Run now"}
          </button>
        }
      />

      <div className="automation-grid">
        <section className="panel">
          <div className="automation-icon">
            <Workflow size={20} />
          </div>

          <div className="panel-kicker">
            Job discovery pipeline
          </div>

          <h2>
            {latest
              ? latest.finished_at
                ? latest.success
                  ? "Latest run completed"
                  : "Latest run failed"
                : "Pipeline is running"
              : "No pipeline run yet"}
          </h2>

          <p>
            {latest
              ? `Pipeline run #${latest.id}`
              : "Start the first intelligence run."}
          </p>

          <div className="run-stats">
            <div>
              <span>Fetched</span>
              <strong>
                {latest?.jobs_fetched ??
                  0}
              </strong>
            </div>

            <div>
              <span>Active</span>
              <strong>
                {latest?.active_jobs ??
                  health.data?.active_jobs ??
                  0}
              </strong>
            </div>

            <div>
              <span>Relevant</span>
              <strong>
                {latest?.rankings_persisted ??
                  0}
              </strong>
            </div>
          </div>

          <div className="automation-status">
            {latest?.success ? (
              <CheckCircle2
                size={16}
              />
            ) : (
              <RefreshCw
                size={15}
              />
            )}
            {runActive
              ? "Running"
              : latest?.success
                ? "Healthy"
                : "Ready"}
          </div>
        </section>

        <section className="panel">
          <div className="automation-icon">
            <Mail size={20} />
          </div>

          <div className="panel-kicker">
            Job digest
          </div>

          <h2>
            {settings.data
              ?.preferences
              .daily_digest_enabled
              ? "Email digest enabled"
              : "Email digest disabled"}
          </h2>

          <p>
            One ranked digest can be sent after each pipeline run.
          </p>

          <div className="schedule-preview">
            <Clock3 size={18} />
            <div>
              <strong>
                Daily scheduler
              </strong>
              <span>
                Recurring Temporal scheduling is the next deployment step.
              </span>
            </div>
          </div>

          <div className="settings-state-row">
            <span className="settings-value">
              Freshness:{" "}
              {settings.data
                ?.preferences
                .job_max_age_days ??
                30}{" "}
              days
            </span>

            <span className="settings-value">
              Digest size:{" "}
              {settings.data
                ?.preferences
                .daily_digest_max_jobs ??
                10}
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}
