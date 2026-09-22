import { apiRequest } from "../../lib/api";

export type SettingsStatus = {
  ai: {
    openai: boolean;
    groq: boolean;
  };
  integrations: {
    adzuna: boolean;
    resend: boolean;
    temporal: boolean;
  };
  preferences: {
    job_max_age_days: number;
    daily_digest_enabled: boolean;
    daily_digest_max_jobs: number;
  };
  privacy: {
    review_before_submit: boolean;
    auto_submit_enabled: boolean;
  };
};

export async function fetchSettingsStatus(): Promise<SettingsStatus> {
  return apiRequest<SettingsStatus>(
    "/settings/status",
  );
}
