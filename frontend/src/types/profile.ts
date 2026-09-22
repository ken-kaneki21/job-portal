export type RolePriority =
  | "primary"
  | "secondary"
  | "discovery"
  | "disabled";

export type RoleFamily = {
  name: string;
  confidence: number;
  priority: RolePriority;
  enabled: boolean;
  matched_signals: string[];
};

export type CandidateIdentity = {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
};

export type ExperienceEntry = {
  company: string | null;
  title: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  skills: string[];
};

export type EducationEntry = {
  institution: string | null;
  degree: string | null;
  field: string | null;
  start_year: number | null;
  end_year: number | null;
};

export type ProjectEntry = {
  name: string;
  description: string | null;
  skills: string[];
};

export type CandidatePreferences = {
  preferred_locations: string[];
  allowed_countries: string[];
  blocked_location_terms: string[];
  blocked_titles: string[];
  remote_preference: boolean | null;
  hybrid_preference: boolean | null;
  relocation_allowed: boolean | null;
  notice_period_days: number | null;
  expected_compensation: string | null;
};

export type UniversalCandidateProfile = {
  schema_version: string;
  profile_name: string;

  identity: CandidateIdentity;

  headline: string | null;
  summary: string | null;

  total_experience_years: number | null;

  role_families: RoleFamily[];

  core_skills: string[];
  secondary_skills: string[];
  tools: string[];
  cloud_platforms: string[];

  industries: string[];
  certifications: string[];

  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];

  preferences: CandidatePreferences;

  source_resume_filename: string | null;
  source_resume_sha256: string | null;

  extracted_at: string;
};

export type ProfileResponse = {
  configured: boolean;
  profile: UniversalCandidateProfile | null;
};

export type ResumeUploadResponse = {
  message: string;
  profile: UniversalCandidateProfile;
};
