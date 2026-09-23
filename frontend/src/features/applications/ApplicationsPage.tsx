
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import {
  fetchApplications,
  type ApplicationItem,
  type ApplicationStatus,
} from "./applicationsApi";

const columns: { status: ApplicationStatus; title: string }[] = [
  { status: "applied", title: "Applied" },
  { status: "interviewing", title: "Interviewing" },
  { status: "offer", title: "Offer" },
  { status: "rejected", title: "Rejected" },
];

function updatedLabel(value: string | null | undefined): string {
  if (!value) return "Tracked";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Tracked";
  return `Updated ${date.toLocaleDateString()}`;
}

export function ApplicationsPage() {
  const query = useQuery({
    queryKey: ["applications", "universal"],
    queryFn: fetchApplications,
  });

  const grouped = new Map<ApplicationStatus, ApplicationItem[]>();
  for (const column of columns) grouped.set(column.status, []);
  for (const item of query.data?.applications ?? []) {
    grouped.get(item.state.status)?.push(item);
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Applications"
        title="Your live application pipeline."
        description="Current application states come directly from the database instead of placeholder cards."
      />

      {query.isLoading ? (
        <div className="panel completion-message">Loading applications...</div>
      ) : null}

      {query.isError ? (
        <div className="panel completion-message completion-error">
          {query.error instanceof Error
            ? query.error.message
            : "Unable to load applications."}
        </div>
      ) : null}

      {!query.isLoading && !query.isError ? (
        <div className="kanban-board">
          {columns.map((column) => {
            const items = grouped.get(column.status) ?? [];
            return (
              <section className="kanban-column" key={column.status}>
                <div className="kanban-heading">
                  <span>{column.title}</span>
                  <strong>{items.length}</strong>
                </div>
                <div className="kanban-list">
                  {items.length === 0 ? (
                    <div className="kanban-card kanban-card-empty">
                      <span>No applications</span>
                      <small>Nothing in this state yet.</small>
                    </div>
                  ) : (
                    items.map((item) => (
                      <div className="kanban-card" key={item.job.id}>
                        <span>{item.job.company}</span>
                        <strong>{item.job.title}</strong>
                        <small>
                          {item.job.location ?? "Location not specified"} ·{" "}
                          {updatedLabel(item.state.updated_at)}
                        </small>
                      </div>
                    ))
                  )}
                </div>
              </section>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
