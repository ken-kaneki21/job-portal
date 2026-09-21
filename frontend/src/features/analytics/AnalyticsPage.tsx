import { BarChart3 } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";

export function AnalyticsPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Analytics"
        title="Learn what actually works."
        description="Application outcomes, ranking quality, source performance, and career-skill trends will be measured here."
      />

      <div className="empty-state">
        <div className="empty-icon">
          <BarChart3 size={24} />
        </div>
        <h2>Outcome analytics will grow with usage</h2>
        <p>
          Once applications and outcomes accumulate, this becomes the feedback loop for learning-to-rank.
        </p>
      </div>
    </div>
  );
}
