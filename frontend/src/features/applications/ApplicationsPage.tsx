import {
  CheckCircle2,
  ChevronRight,
  ClipboardCopy,
  ExternalLink,
  FileText,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import {
  fetchAnswers,
  fetchApplicationBundle,
  fetchApplicationDetail,
  fetchReadiness,
  updateApplicationStatus,
  type ApplicationItem,
  type ApplicationStatus,
} from "./applicationsApi";

const columns: Array<{
  status: ApplicationStatus;
  label: string;
}> = [
  { status: "saved", label: "Saved" },
  { status: "applied", label: "Applied" },
  { status: "interviewing", label: "Interviewing" },
  { status: "rejected", label: "Rejected" },
  { status: "offer", label: "Offer" },
];

function formatDate(value?: string | null): string {
  if (!value) {
    return "Recently updated";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Recently updated";
  }

  return date.toLocaleString();
}

function itemStatus(item: ApplicationItem): ApplicationStatus {
  return item.state.status as ApplicationStatus;
}

export function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");

  const applicationsQuery = useQuery({
    queryKey: ["applications-bundle"],
    queryFn: fetchApplicationBundle,
    staleTime: 30_000,
  });

  const detailQuery = useQuery({
    queryKey: ["application-detail", selectedJobId],
    queryFn: () => fetchApplicationDetail(selectedJobId as number),
    enabled: selectedJobId !== null,
  });

  const readinessQuery = useQuery({
    queryKey: ["application-readiness", selectedJobId],
    queryFn: () => fetchReadiness(selectedJobId as number),
    enabled: selectedJobId !== null,
  });

  const answersQuery = useQuery({
    queryKey: ["application-answers", selectedJobId],
    queryFn: () => fetchAnswers(selectedJobId as number),
    enabled: selectedJobId !== null,
  });

  const mutation = useMutation({
    mutationFn: async ({
      jobId,
      status,
    }: {
      jobId: number;
      status: ApplicationStatus;
    }) =>
      updateApplicationStatus(
        jobId,
        status,
        notes.trim() || null,
      ),
    onSuccess: async () => {
      setNotes("");
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["applications-bundle"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["application-detail", selectedJobId],
        }),
      ]);
    },
  });

  const grouped = useMemo(() => {
    const items = applicationsQuery.data?.applications ?? [];

    return Object.fromEntries(
      columns.map(({ status }) => [
        status,
        items.filter((item) => itemStatus(item) === status),
      ]),
    ) as Record<ApplicationStatus, ApplicationItem[]>;
  }, [applicationsQuery.data]);

  const selectedItem = useMemo(() => {
    if (selectedJobId === null) {
      return null;
    }

    return (
      applicationsQuery.data?.applications.find(
        (item) => item.job.id === selectedJobId,
      ) ?? null
    );
  }, [applicationsQuery.data, selectedJobId]);

  async function copyWorkdayCommand() {
    if (selectedJobId === null) {
      return;
    }

    await navigator.clipboard.writeText(
      `python -m jobintel.workday_autofill --job-id ${selectedJobId}`,
    );
  }

  if (applicationsQuery.isLoading) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Applications"
          title="Your application pipeline."
          description="Loading your real application history and outcomes."
        />
        <div className="empty-state">
          <RefreshCw size={22} />
          <h2>Loading applications</h2>
        </div>
      </div>
    );
  }

  if (applicationsQuery.isError) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Applications"
          title="Your application pipeline."
          description="Track every opportunity from shortlist to outcome."
        />
        <div className="empty-state">
          <h2>Unable to load applications</h2>
          <p>
            {applicationsQuery.error instanceof Error
              ? applicationsQuery.error.message
              : "Application API could not be reached."}
          </p>
          <button
            className="primary-action"
            onClick={() => {
              void applicationsQuery.refetch();
            }}
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const total = applicationsQuery.data?.applications.length ?? 0;

  return (
    <div className="page applications-page">
      <PageHeader
        eyebrow="Applications"
        title="Your application pipeline."
        description={`${total} tracked opportunities. Status changes feed your outcome-learning and ranking evaluation loop.`}
      />

      <div className="application-summary-strip">
        {columns.map(({ status, label }) => (
          <div className="application-summary-chip" key={status}>
            <span>{label}</span>
            <strong>
              {applicationsQuery.data?.summary.counts[status] ?? 0}
            </strong>
          </div>
        ))}
      </div>

      <div className="kanban-board applications-kanban">
        {columns.map(({ status, label }) => {
          const items = grouped[status] ?? [];

          return (
            <section className="kanban-column" key={status}>
              <div className="kanban-heading">
                <span>{label}</span>
                <strong>{items.length}</strong>
              </div>

              <div className="kanban-list">
                {items.length === 0 ? (
                  <div className="application-column-empty">
                    No jobs here yet.
                  </div>
                ) : (
                  items.map((item) => (
                    <button
                      type="button"
                      className={`kanban-card application-card ${
                        selectedJobId === item.job.id
                          ? "application-card-selected"
                          : ""
                      }`}
                      key={item.job.id}
                      onClick={() => {
                        setSelectedJobId(item.job.id);
                        setNotes(item.state.notes ?? "");
                      }}
                    >
                      <span>{item.job.company}</span>
                      <strong>{item.job.title}</strong>
                      <small>
                        {item.job.location ?? "Location unavailable"}
                      </small>
                      <small>{formatDate(item.state.updated_at)}</small>
                    </button>
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>

      {selectedItem ? (
        <section className="application-detail-panel panel">
          <div className="application-detail-heading">
            <div>
              <span className="panel-kicker">Application workspace</span>
              <h2>{selectedItem.job.title}</h2>
              <p>
                {selectedItem.job.company}
                {selectedItem.job.location
                  ? ` - ${selectedItem.job.location}`
                  : ""}
              </p>
            </div>

            <a
              className="secondary-button"
              href={selectedItem.job.url}
              target="_blank"
              rel="noreferrer"
            >
              <ExternalLink size={15} />
              Open application
            </a>
          </div>

          <div className="application-detail-grid">
            <div className="application-detail-section">
              <h3>Status</h3>
              <div className="application-status-actions">
                {columns.map(({ status, label }) => (
                  <button
                    type="button"
                    className={
                      itemStatus(selectedItem) === status
                        ? "primary-action"
                        : "secondary-button"
                    }
                    key={status}
                    disabled={mutation.isPending}
                    onClick={() => {
                      mutation.mutate({
                        jobId: selectedItem.job.id,
                        status,
                      });
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <label className="application-notes-label">
                Notes
                <textarea
                  value={notes}
                  placeholder="Recruiter contact, interview date, rejection reason, or anything useful..."
                  onChange={(event) => {
                    setNotes(event.target.value);
                  }}
                />
              </label>

              <p className="application-helper">
                Add notes first, then choose a status to save both together.
              </p>
            </div>

            <div className="application-detail-section">
              <h3>Readiness</h3>

              {readinessQuery.isLoading ? (
                <p>Checking profile and application readiness...</p>
              ) : readinessQuery.data ? (
                <>
                  <div
                    className={`application-readiness ${
                      readinessQuery.data.ready_for_review
                        ? "application-readiness-ready"
                        : "application-readiness-blocked"
                    }`}
                  >
                    <ShieldCheck size={17} />
                    <strong>
                      {readinessQuery.data.ready_for_review
                        ? "Ready for manual review"
                        : "Needs attention"}
                    </strong>
                  </div>

                  <div className="application-check-list">
                    {readinessQuery.data.checks.map((check) => (
                      <div key={check.key}>
                        <CheckCircle2 size={14} />
                        <span>{check.message}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p>Readiness data unavailable.</p>
              )}

              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  void copyWorkdayCommand();
                }}
              >
                <ClipboardCopy size={15} />
                Copy Workday assist command
              </button>
            </div>

            <div className="application-detail-section">
              <h3>Application assets</h3>

              {detailQuery.data?.application_assets ? (
                <>
                  <p>
                    {detailQuery.data.application_assets.resume_summary ??
                      "Resume summary available."}
                  </p>

                  <div className="tag-row">
                    {(
                      detailQuery.data.application_assets.skills_to_emphasize ??
                      []
                    ).map((skill) => (
                      <span className="tag tag-positive" key={skill}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </>
              ) : (
                <p>No generated application assets for this job yet.</p>
              )}

              <a
                className="ghost-button"
                href={`/discover?job=${selectedItem.job.id}`}
              >
                <FileText size={14} />
                View full job intelligence
                <ChevronRight size={14} />
              </a>
            </div>

            <div className="application-detail-section">
              <h3>Reusable answers</h3>

              {answersQuery.data ? (
                <div className="application-answer-list">
                  {Object.entries(answersQuery.data.answers)
                    .filter(([, answer]) => answer.value !== null)
                    .slice(0, 8)
                    .map(([key, answer]) => (
                      <div key={key}>
                        <span>{key.replaceAll("_", " ")}</span>
                        <strong>
                          {answer.sensitive
                            ? "Available - sensitive"
                            : String(answer.value)}
                        </strong>
                      </div>
                    ))}
                </div>
              ) : (
                <p>Loading reusable answers...</p>
              )}
            </div>
          </div>

          <div className="application-history">
            <h3>History</h3>

            {detailQuery.data?.history?.length ? (
              detailQuery.data.history.map((event) => (
                <div className="application-history-row" key={event.id}>
                  <span>{formatDate(event.created_at)}</span>
                  <strong>
                    {event.previous_status ?? "new"} {"->"} {event.new_status}
                  </strong>
                  <small>{event.notes ?? event.source}</small>
                </div>
              ))
            ) : (
              <p>No application transitions recorded yet.</p>
            )}
          </div>
        </section>
      ) : (
        <div className="application-selection-hint">
          Select an application card to open its workspace.
        </div>
      )}
    </div>
  );
}
