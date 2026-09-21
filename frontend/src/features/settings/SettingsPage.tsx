import { BrainCircuit, KeyRound, ShieldCheck } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";

export function SettingsPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Settings"
        title="Configure without touching code."
        description="Providers, integrations, ranking behavior, privacy, notifications, and application preferences will be editable here."
      />

      <div className="settings-list">
        <button className="settings-row">
          <div className="settings-icon">
            <BrainCircuit size={19} />
          </div>
          <div>
            <strong>AI providers</strong>
            <span>Models, fallbacks, and task routing</span>
          </div>
        </button>

        <button className="settings-row">
          <div className="settings-icon">
            <KeyRound size={19} />
          </div>
          <div>
            <strong>Integrations</strong>
            <span>Job sources, email, browser companion, and external services</span>
          </div>
        </button>

        <button className="settings-row">
          <div className="settings-icon">
            <ShieldCheck size={19} />
          </div>
          <div>
            <strong>Privacy & security</strong>
            <span>Data controls, secrets, permissions, and audit behavior</span>
          </div>
        </button>
      </div>
    </div>
  );
}
