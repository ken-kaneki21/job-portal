import { PageHeader } from "../../components/ui/PageHeader";

const columns = [
  {
    title: "Shortlisted",
    count: 8,
    items: [
      ["Databricks", "Senior Data Engineer"],
      ["Adobe", "Data Platform Engineer"],
    ],
  },
  {
    title: "Applied",
    count: 12,
    items: [
      ["American Express", "Data Engineer II"],
      ["Oracle", "Senior Data Systems Engineer"],
    ],
  },
  {
    title: "Interviewing",
    count: 4,
    items: [
      ["Qualcomm", "AI Engineer"],
      ["EXL", "Palantir Data Engineer"],
    ],
  },
  {
    title: "Offer / Final",
    count: 1,
    items: [["Example Company", "Data Engineer"]],
  },
];

export function ApplicationsPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Applications"
        title="Your application pipeline."
        description="Track every opportunity from shortlist to interview and outcome."
      />

      <div className="kanban-board">
        {columns.map((column) => (
          <section className="kanban-column" key={column.title}>
            <div className="kanban-heading">
              <span>{column.title}</span>
              <strong>{column.count}</strong>
            </div>

            <div className="kanban-list">
              {column.items.map(([company, role]) => (
                <div className="kanban-card" key={`${company}-${role}`}>
                  <span>{company}</span>
                  <strong>{role}</strong>
                  <small>Updated recently</small>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
