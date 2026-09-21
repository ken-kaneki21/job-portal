import { Building2 } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";

export function CompaniesPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Companies"
        title="Company intelligence."
        description="Hiring momentum, relevant openings, news signals, recruiters, and watchlists will live here."
      />

      <div className="empty-state">
        <div className="empty-icon">
          <Building2 size={24} />
        </div>
        <h2>Company intelligence is next</h2>
        <p>
          This screen will combine company hiring signals, matching roles, recruiter contacts, and relevant news.
        </p>
      </div>
    </div>
  );
}
