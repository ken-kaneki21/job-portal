import { apiRequest } from "../../lib/api";
import type {
  ProfileResponse,
  ResumeUploadResponse,
  UniversalCandidateProfile,
} from "../../types/profile";

export async function fetchProfile(): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>("/profile");
}

export async function uploadResume(
  file: File,
): Promise<ResumeUploadResponse> {
  const body = new FormData();
  body.append("file", file);

  return apiRequest<ResumeUploadResponse>("/profile/resume", {
    method: "POST",
    body,
  });
}

export async function saveProfile(
  profile: UniversalCandidateProfile,
): Promise<ProfileResponse> {
  return apiRequest<ProfileResponse>("/profile", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });
}
