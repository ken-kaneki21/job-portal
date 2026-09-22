import {
  CheckCircle2,
  Clock3,
  Play,
  RefreshCw,
  Workflow,
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";

export function AutomationsPage() {
  return (
    <div className="page">
      <PageHeader
        eyebrow="Automations"
        title="Control the entire pipeline here."
        description="Normal use will not require terminal commands. Run, schedule, inspect, and retry workflows from this screen."
        actions={
          <button className="primary-action">
            <Play size={16} fill="currentColor" />
            Run now
          </button>
        }
      />

      <div className="automation-grid">
        <section className="panel">
          <div className="automation-icon">
            <Workflow size={20} />
          </div>

          <div className="panel-kicker">Job discovery pipeline</div>
          <h2>Latest run completed</h2>
          <p>All configured sources finished successfully.</p>

          <div className="run-stats">
            <div>
              <span>Fetched</span>
              <strong>6,803</strong>
            </div>
            <div>
              <span>Active</span>
              <strong>7,518</strong>
            </div>
            <div>
              <span>Relevant</span>
              <strong>461</strong>
            </div>
          </div>

          <div className="automation-status">
            <CheckCircle2 size={16} />
            Healthy
          </div>
        </section>

        <section className="panel">
          <div className="panel-kicker">Schedule</div>
          <h2>Run automatically</h2>
          <p>Scheduling will be backed by Temporal.</p>

          <div className="schedule-preview">
            <Clock3 size={18} />
            <div>
              <strong>Manual mode</strong>
              <span>No recurring schedule configured</span>
            </div>
          </div>

          <button className="secondary-button">
            <RefreshCw size={15} />
            Configure schedule
          </button>
        </section>
      </div>
    </div>
  );
}
