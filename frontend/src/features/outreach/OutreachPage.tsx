import { MessageSquareText } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";

export function OutreachPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Outreach"
        title="Recruiter relationships, organized."
        description="Generate messages, schedule follow-ups, and track recruiter conversations from one place."
      />

      <div className="empty-state">
        <div className="empty-icon">
          <MessageSquareText size={24} />
        </div>
        <h2>Recruiter CRM coming next</h2>
        <p>
          This will manage recruiter contacts, referral requests, generated messages, replies, and follow-up sequences.
        </p>
      </div>
    </div>
  );
}
