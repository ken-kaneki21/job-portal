
import { apiRequest } from "../../lib/api";

export type ApplicationStatus = "applied" | "interviewing" | "rejected" | "offer";

export type ApplicationItem = {
  job: {
    id: number;
    company: string;
    title: string;
    location: string | null;
    apply_url?: string | null;
  };
  state: {
    status: ApplicationStatus;
    notes?: string | null;
    updated_at?: string | null;
  };
};

export type ApplicationsResponse = {
  profile_name: string;
  status: string | null;
  count: number;
  applications: ApplicationItem[];
};

export async function fetchApplications(): Promise<ApplicationsResponse> {
  return apiRequest<ApplicationsResponse>(
    "/applications?profile_name=universal&limit=500",
  );
}
