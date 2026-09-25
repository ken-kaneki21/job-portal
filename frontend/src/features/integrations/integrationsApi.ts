
import { API_BASE_URL, ApiError, apiRequest } from "../../lib/api";

export type PortalName = "foundit" | "indeed" | "linkedin" | "naukri";

export type PortalImportResult = {
  portal: string;
  filename: string | null;
  valid_rows: number;
  new_jobs: number;
  matched_existing: number;
  existing_source: number;
  raw_payloads_saved: number;
};

export type HiringPostResult = {
  role: string | null;
  company: string | null;
  location: string | null;
  skills: string[];
  minimum_experience_years: number | null;
  contact_emails: string[];
  source_url: string | null;
  review_required: boolean;
  auto_apply: boolean;
  raw_text: string;
};

async function errorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string | { message?: string };
    };
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail?.message) return payload.detail.message;
  } catch {
    // Use generic message below.
  }
  return `Request failed with status ${response.status}`;
}

export async function importPortalFile(
  portal: PortalName,
  file: File,
): Promise<PortalImportResult> {
  const form = new FormData();
  form.append("portal", portal);
  form.append("file", file);

  const response = await fetch(`${API_BASE_URL}/integrations/portal-import`, {
    credentials: "include",
    method: "POST",
    body: form,
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response));
  }
  return (await response.json()) as PortalImportResult;
}

export async function extractHiringPost(
  text: string,
  sourceUrl?: string,
): Promise<HiringPostResult> {
  return apiRequest<HiringPostResult>("/integrations/hiring-post/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      source_url: sourceUrl?.trim() || null,
    }),
  });
}
