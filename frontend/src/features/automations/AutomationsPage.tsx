import {
  CheckCircle2,
  Clock3,
  LoaderCircle,
  Mail,
  PauseCircle,
  Play,
  RefreshCw,
  Save,
  Send,
  Workflow,
} from "lucide-react";
import { useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import { fetchSettingsStatus } from "../settings/settingsApi";
import {
  getDailySchedule,
  getPipelineHealth,
  pauseDailySchedule,
  resumeDailySchedule,
  saveDailySchedule,
  startPipeline,
  triggerDailySchedule,
} from "./pipelineApi";

function browserTimezone(): string {
  try {
    return (
      Intl.DateTimeFormat()
        .resolvedOptions()
        .timeZone || "UTC"
    );
  } catch {
    return "UTC";
  }
}

function formatNextRun(
  value: string | null | undefined,
): string {
  if (!value) {
    return "Not scheduled yet";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Next run unavailable";
  }

  return date.toLocaleString();
}

function formatScheduleTime(
  hour: number | undefined,
  minute: number | undefined,
): string {
  const resolvedHour =
    hour ?? 8;

  const resolvedMinute =
    minute ?? 0;

  return `${String(
    resolvedHour,
  ).padStart(2, "0")}:${String(
    resolvedMinute,
  ).padStart(2, "0")}`;
}

export function AutomationsPage() {
  const queryClient =
    useQueryClient();

  const [
    scheduleTimeDraft,
    setScheduleTimeDraft,
  ] = useState<string | null>(
    null,
  );

  const [
    timezoneDraft,
    setTimezoneDraft,
  ] = useState<string | null>(
    null,
  );

  const [
    sendDigestDraft,
    setSendDigestDraft,
  ] = useState<boolean | null>(
    null,
  );

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

  const schedule =
    useQuery({
      queryKey: [
        "daily-schedule",
      ],
      queryFn:
        getDailySchedule,
      refetchInterval: 15_000,
      retry: false,
    });

  const scheduleTime =
    scheduleTimeDraft ??
    formatScheduleTime(
      schedule.data?.hour,
      schedule.data?.minute,
    );

  const timezone =
    timezoneDraft ??
    schedule.data?.timezone ??
    browserTimezone();

  const sendDigest =
    sendDigestDraft ??
    schedule.data?.send_digest ??
    true;

  const resetScheduleDrafts =
    () => {
      setScheduleTimeDraft(
        null,
      );

      setTimezoneDraft(
        null,
      );

      setSendDigestDraft(
        null,
      );
    };

  const refreshSchedule =
    async () => {
      await queryClient.invalidateQueries({
        queryKey: [
          "daily-schedule",
        ],
      });
    };

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

  const saveMutation =
    useMutation({
      mutationFn: saveDailySchedule,
      onSuccess: async () => {
        resetScheduleDrafts();

        await refreshSchedule();
      },
    });

  const pauseMutation =
    useMutation({
      mutationFn: pauseDailySchedule,
      onSuccess: refreshSchedule,
    });

  const resumeMutation =
    useMutation({
      mutationFn: resumeDailySchedule,
      onSuccess: refreshSchedule,
    });

  const triggerMutation =
    useMutation({
      mutationFn: triggerDailySchedule,
      onSuccess: async () => {
        await Promise.all([
          refreshSchedule(),
          queryClient.invalidateQueries({
            queryKey: [
              "pipeline-health",
            ],
          }),
        ]);
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

  const scheduleBusy =
    saveMutation.isPending ||
    pauseMutation.isPending ||
    resumeMutation.isPending ||
    triggerMutation.isPending;

  const saveSchedule = () => {
    const [
      hourText,
      minuteText,
    ] = scheduleTime.split(":");

    const hour = Number(hourText);
    const minute = Number(minuteText);

    if (
      !Number.isInteger(hour) ||
      !Number.isInteger(minute)
    ) {
      return;
    }

    saveMutation.mutate({
      enabled:
        schedule.data?.enabled ??
        true,
      hour,
      minute,
      timezone,
      send_digest: sendDigest,
    });
  };

  const toggleSchedule = () => {
    if (!schedule.data?.exists) {
      saveSchedule();
      return;
    }

    if (schedule.data.enabled) {
      pauseMutation.mutate();
    } else {
      resumeMutation.mutate();
    }
  };

  const emailReady =
    settings.data
      ?.integrations.resend ??
    false;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Automations"
        title="Control the entire pipeline here."
        description="Run now or let Temporal execute a durable daily intelligence schedule."
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

        <section className="panel automation-schedule-panel">
          <div className="automation-icon">
            <Clock3 size={20} />
          </div>

          <div className="panel-kicker">
            Daily Temporal schedule
          </div>

          <h2>
            {schedule.isError
              ? "Temporal schedule unavailable"
              : schedule.data?.exists
                ? schedule.data.enabled
                  ? "Daily automation enabled"
                  : "Daily automation paused"
                : "No daily schedule yet"}
          </h2>

          <p>
            Temporal stores the recurring schedule, skips overlapping runs, and can trigger the ranked email digest.
          </p>

          <div className="schedule-form">
            <label>
              <span>Run time</span>

              <input
                type="time"
                value={scheduleTime}
                onChange={(event) =>
                  setScheduleTimeDraft(
                    event.target.value,
                  )
                }
              />
            </label>

            <label>
              <span>Timezone</span>

              <input
                value={timezone}
                onChange={(event) =>
                  setTimezoneDraft(
                    event.target.value,
                  )
                }
                placeholder="Asia/Kolkata"
              />
            </label>
          </div>

          <label className="schedule-checkbox">
            <input
              type="checkbox"
              checked={sendDigest}
              onChange={(event) =>
                setSendDigestDraft(
                  event.target.checked,
                )
              }
            />

            <span>
              Send ranked email digest after a successful quality-checked run
            </span>
          </label>

          {sendDigest &&
            !emailReady && (
              <div className="automation-warning">
                <Mail size={15} />

                Configure Resend and notification email addresses before enabling digest delivery.
              </div>
            )}

          <div className="schedule-preview">
            <Clock3 size={18} />

            <div>
              <strong>
                Next execution
              </strong>

              <span>
                {formatNextRun(
                  schedule.data
                    ?.next_run_at,
                )}
              </span>
            </div>
          </div>

          <div className="automation-schedule-meta">
            <span>
              Runs:{" "}
              {schedule.data
                ?.num_actions ??
                0}
            </span>

            <span>
              Overlap skips:{" "}
              {schedule.data
                ?.num_actions_skipped_overlap ??
                0}
            </span>

            <span>
              Running:{" "}
              {schedule.data
                ?.running_actions ??
                0}
            </span>
          </div>

          <div className="automation-schedule-actions">
            <button
              className="primary-action"
              onClick={saveSchedule}
              disabled={
                scheduleBusy ||
                !scheduleTime ||
                !timezone.trim()
              }
            >
              {saveMutation.isPending ? (
                <LoaderCircle
                  size={15}
                  className="run-status-spinner"
                />
              ) : (
                <Save size={15} />
              )}

              Save schedule
            </button>

            <button
              className="secondary-button"
              onClick={toggleSchedule}
              disabled={scheduleBusy}
            >
              {schedule.data?.enabled ? (
                <PauseCircle size={15} />
              ) : (
                <Play size={15} />
              )}

              {schedule.data?.exists
                ? schedule.data.enabled
                  ? "Pause"
                  : "Resume"
                : "Enable"}
            </button>

            <button
              className="secondary-button"
              onClick={() =>
                triggerMutation.mutate()
              }
              disabled={
                scheduleBusy ||
                !schedule.data?.exists
              }
            >
              <Send size={15} />
              Trigger now
            </button>
          </div>

          {(saveMutation.isError ||
            pauseMutation.isError ||
            resumeMutation.isError ||
            triggerMutation.isError) && (
            <p className="automation-error">
              Unable to update the Temporal schedule. Check that Temporal is running and the timezone is a valid IANA timezone.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
