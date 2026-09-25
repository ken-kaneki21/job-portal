import { apiRequest } from "../../lib/api";
export type OpsStatus = {
  schedule: { enabled: boolean; id: string; cron: string; timezone: string };
  notifications: { daily_digest_enabled: boolean; resend_configured: boolean };
  security: { auth_configured: boolean; companion_token_configured: boolean };
  performance: { embedding_batch_size: number };
};
export const getOpsStatus = () => apiRequest<OpsStatus>("/ops/status");
export const ensureSchedule = () => apiRequest("/ops/schedule/ensure", { method: "POST" });
export const triggerSchedule = () => apiRequest("/ops/schedule/trigger", { method: "POST" });
export const testEmail = () => apiRequest("/ops/notifications/test", { method: "POST" });
