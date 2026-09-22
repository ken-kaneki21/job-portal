import {
  BrainCircuit,
  CheckCircle2,
  KeyRound,
  Mail,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import { fetchSettingsStatus } from "./settingsApi";

function StateBadge({
  ready,
  label,
}: {
  ready: boolean;
  label: string;
}) {
  return (
    <span
      className={
        ready
          ? "settings-state settings-state-ready"
          : "settings-state settings-state-missing"
      }
    >
      {ready ? (
        <CheckCircle2 size={14} />
      ) : (
        <XCircle size={14} />
      )}
      {label}
    </span>
  );
}

export function SettingsPage() {
  const query =
    useQuery({
      queryKey: [
        "settings-status",
      ],
      queryFn:
        fetchSettingsStatus,
      staleTime: 30_000,
    });

  const data =
    query.data;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Settings"
        title="Know exactly what is configured."
        description="Live integration readiness, notification state, ranking freshness, and application safety controls."
      />

      {query.isError ? (
        <div className="empty-state">
          <h2>
            Settings API unavailable
          </h2>
          <p>
            Start the backend and retry.
          </p>
        </div>
      ) : (
        <div className="settings-list settings-live-list">
          <section className="settings-row settings-live-row">
            <div className="settings-icon">
              <BrainCircuit size={19} />
            </div>

            <div>
              <strong>
                AI providers
              </strong>
              <span>
                Optional enrichment and generation providers
              </span>

              <div className="settings-state-row">
                <StateBadge
                  ready={
                    data?.ai.openai ??
                    false
                  }
                  label="OpenAI"
                />
                <StateBadge
                  ready={
                    data?.ai.groq ??
                    false
                  }
                  label="Groq"
                />
              </div>
            </div>
          </section>

          <section className="settings-row settings-live-row">
            <div className="settings-icon">
              <KeyRound size={19} />
            </div>

            <div>
              <strong>
                Integrations
              </strong>
              <span>
                Discovery, orchestration, and email delivery
              </span>

              <div className="settings-state-row">
                <StateBadge
                  ready={
                    data?.integrations.adzuna ??
                    false
                  }
                  label="Adzuna"
                />
                <StateBadge
                  ready={
                    data?.integrations.temporal ??
                    false
                  }
                  label="Temporal"
                />
                <StateBadge
                  ready={
                    data?.integrations.resend ??
                    false
                  }
                  label="Email / Resend"
                />
              </div>
            </div>
          </section>

          <section className="settings-row settings-live-row">
            <div className="settings-icon">
              <Mail size={19} />
            </div>

            <div>
              <strong>
                Daily job digest
              </strong>
              <span>
                One ranked email after a pipeline run when enabled
              </span>

              <div className="settings-state-row">
                <StateBadge
                  ready={
                    data?.preferences.daily_digest_enabled ??
                    false
                  }
                  label={
                    data?.preferences.daily_digest_enabled
                      ? "Enabled"
                      : "Disabled"
                  }
                />

                <span className="settings-value">
                  Top{" "}
                  {data?.preferences.daily_digest_max_jobs ??
                    10}{" "}
                  jobs · max age{" "}
                  {data?.preferences.job_max_age_days ??
                    30}{" "}
                  days
                </span>
              </div>
            </div>
          </section>

          <section className="settings-row settings-live-row">
            <div className="settings-icon">
              <ShieldCheck size={19} />
            </div>

            <div>
              <strong>
                Application safety
              </strong>
              <span>
                Autofill remains review-first
              </span>

              <div className="settings-state-row">
                <StateBadge
                  ready={
                    data?.privacy.review_before_submit ??
                    true
                  }
                  label="Review required"
                />

                <StateBadge
                  ready={
                    !(
                      data?.privacy.auto_submit_enabled ??
                      false
                    )
                  }
                  label="Auto-submit off"
                />
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
