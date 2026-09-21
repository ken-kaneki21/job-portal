import type {
  LucideIcon,
} from "lucide-react";

import { AnimatedNumber } from "../effects/AnimatedNumber";
import { InteractiveSurface } from "../effects/InteractiveSurface";

type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
};

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
}: MetricCardProps) {
  return (
    <InteractiveSurface
      className="metric-card metric-card-animated"
    >
      <div className="metric-card-accent" />

      <div className="metric-icon">
        <Icon size={18} />
      </div>

      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        <AnimatedNumber
          value={value}
        />
      </div>

      <div className="metric-detail">
        {detail}
      </div>
    </InteractiveSurface>
  );
}
