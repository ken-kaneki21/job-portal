import {
  Check,
  ChevronDown,
  FileText,
  FileUp,
  LoaderCircle,
  MapPin,
  RefreshCw,
  Save,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import {
  type ChangeEvent,
  useRef,
  useState,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "../../components/ui/PageHeader";
import type {
  RoleFamily,
  RolePriority,
  UniversalCandidateProfile,
} from "../../types/profile";
import {
  fetchProfile,
  saveProfile,
  uploadResume,
} from "./profileApi";
import "./profile.css";

const priorities: Array<{
  value: RolePriority;
  label: string;
}> = [
  {
    value: "primary",
    label: "Primary",
  },
  {
    value: "secondary",
    label: "Secondary",
  },
  {
    value: "discovery",
    label: "Discovery",
  },
  {
    value: "disabled",
    label: "Disabled",
  },
];

function percentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function ProfilePage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [draft, setDraft] =
    useState<UniversalCandidateProfile | null>(null);

  const [message, setMessage] = useState<string | null>(null);

  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: fetchProfile,
  });

  const profile = draft ?? profileQuery.data?.profile ?? null;

  const uploadMutation = useMutation({
    mutationFn: uploadResume,

    onMutate: () => {
      setMessage(null);
    },

    onSuccess: (response) => {
      setDraft(response.profile);

      queryClient.setQueryData(
        ["profile"],
        {
          configured: true,
          profile: response.profile,
        },
      );

      setMessage("Resume analyzed successfully.");
    },

    onError: (error: Error) => {
      setMessage(error.message);
    },
  });

  const saveMutation = useMutation({
    mutationFn: saveProfile,

    onSuccess: (response) => {
      setDraft(response.profile);

      queryClient.setQueryData(
        ["profile"],
        response,
      );

      setMessage("Profile saved.");
    },

    onError: (error: Error) => {
      setMessage(error.message);
    },
  });

  function chooseResume() {
    fileInputRef.current?.click();
  }

  function handleResumeSelected(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    uploadMutation.mutate(file);

    event.target.value = "";
  }

  function updateRole(
    roleName: string,
    changes: Partial<RoleFamily>,
  ) {
    if (!profile) {
      return;
    }

    setDraft({
      ...profile,
      role_families: profile.role_families.map((role) =>
        role.name === roleName
          ? {
              ...role,
              ...changes,
            }
          : role,
      ),
    });
  }

  function updateLocations(value: string) {
    if (!profile) {
      return;
    }

    const locations = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    setDraft({
      ...profile,
      preferences: {
        ...profile.preferences,
        preferred_locations: locations,
      },
    });
  }

  function updateExperience(value: string) {
    if (!profile) {
      return;
    }

    const parsed = Number.parseFloat(value);

    setDraft({
      ...profile,
      total_experience_years:
        Number.isFinite(parsed) ? parsed : null,
    });
  }

  function handleSave() {
    if (!profile) {
      return;
    }

    saveMutation.mutate(profile);
  }

  if (profileQuery.isLoading) {
    return (
      <div className="page profile-loading">
        <LoaderCircle
          className="profile-spinner"
          size={28}
        />
        <span>Loading career profile...</span>
      </div>
    );
  }

  if (profileQuery.isError) {
    return (
      <div className="page">
        <PageHeader
          eyebrow="Profile intelligence"
          title="Unable to load your profile."
          description="The frontend could not reach the Job Intelligence API."
        />

        <div className="profile-error-card">
          <strong>API connection failed</strong>
          <span>{profileQuery.error.message}</span>

          <button
            className="secondary-button"
            onClick={() => profileQuery.refetch()}
          >
            <RefreshCw size={15} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <input
        ref={fileInputRef}
        className="profile-file-input"
        type="file"
        accept="application/pdf,.pdf"
        onChange={handleResumeSelected}
      />

      <PageHeader
        eyebrow="Profile intelligence"
        title="Your career profile drives every recommendation."
        description="Your resume becomes a structured, editable profile used for discovery, ranking, gap analysis, outreach, and application assistance."
        actions={
          <div className="profile-header-actions">
            {profile ? (
              <button
                className="secondary-button"
                disabled={saveMutation.isPending}
                onClick={handleSave}
              >
                {saveMutation.isPending ? (
                  <LoaderCircle
                    className="profile-spinner"
                    size={15}
                  />
                ) : (
                  <Save size={15} />
                )}
                Save profile
              </button>
            ) : null}

            <button
              className="primary-action"
              disabled={uploadMutation.isPending}
              onClick={chooseResume}
            >
              {uploadMutation.isPending ? (
                <LoaderCircle
                  className="profile-spinner"
                  size={16}
                />
              ) : (
                <FileUp size={16} />
              )}

              {profile ? "Replace resume" : "Upload resume"}
            </button>
          </div>
        }
      />

      {message ? (
        <div className="profile-message">
          <Check size={15} />
          {message}
        </div>
      ) : null}

      {!profile ? (
        <section className="profile-onboarding">
          <div className="profile-onboarding-icon">
            <FileText size={27} />
          </div>

          <div className="page-eyebrow">Start here</div>

          <h2>Upload your canonical resume.</h2>

          <p>
            Job Intelligence will extract skills and detect relevant role
            families, then build the profile used by the ranking engine.
          </p>

          <button
            className="primary-action"
            onClick={chooseResume}
          >
            <FileUp size={16} />
            Choose PDF
          </button>

          <div className="profile-privacy-note">
            <ShieldCheck size={14} />
            PDF only · maximum 10 MB · never commit generated personal profile
            data
          </div>
        </section>
      ) : (
        <>
          <section className="profile-summary-grid">
            <article className="panel profile-summary-card">
              <div className="profile-card-icon">
                <FileText size={19} />
              </div>

              <div className="panel-kicker">Source resume</div>

              <h2>
                {profile.source_resume_filename ??
                  "Uploaded resume"}
              </h2>

              <p>
                Last analyzed{" "}
                {new Date(
                  profile.extracted_at,
                ).toLocaleString()}
              </p>

              <div className="profile-status">
                <Check size={13} />
                Parsed and active
              </div>
            </article>

            <article className="panel profile-summary-card">
              <div className="profile-card-icon">
                <Target size={19} />
              </div>

              <div className="panel-kicker">Role intelligence</div>

              <h2>
                {
                  profile.role_families.filter(
                    (role) => role.enabled,
                  ).length
                }{" "}
                active role families
              </h2>

              <p>
                {
                  profile.role_families.filter(
                    (role) =>
                      role.priority === "primary" &&
                      role.enabled,
                  ).length
                }{" "}
                currently treated as primary.
              </p>
            </article>

            <article className="panel profile-summary-card">
              <div className="profile-card-icon">
                <Sparkles size={19} />
              </div>

              <div className="panel-kicker">Detected skills</div>

              <h2>
                {profile.core_skills.length +
                  profile.secondary_skills.length}
              </h2>

              <p>
                {profile.core_skills.length} core skills and{" "}
                {profile.secondary_skills.length} secondary skills.
              </p>
            </article>

            <article className="panel profile-summary-card">
              <div className="profile-card-icon">
                <MapPin size={19} />
              </div>

              <div className="panel-kicker">Search geography</div>

              <h2>
                {profile.preferences.preferred_locations.length ||
                  0}{" "}
                preferred locations
              </h2>

              <p>
                Used as ranking preferences rather than hard exclusions.
              </p>
            </article>
          </section>

          <section className="profile-content-grid">
            <div className="profile-main-column">
              <article className="panel">
                <div className="profile-section-heading">
                  <div>
                    <div className="panel-kicker">
                      Role families
                    </div>
                    <h2>Control what the system searches for.</h2>
                  </div>

                  <span className="profile-section-note">
                    Ranked from your resume
                  </span>
                </div>

                <div className="role-intelligence-list">
                  {profile.role_families.map((role) => (
                    <div
                      className={`role-intelligence-row ${
                        role.enabled
                          ? ""
                          : "role-intelligence-disabled"
                      }`}
                      key={role.name}
                    >
                      <button
                        className={`role-toggle ${
                          role.enabled
                            ? "role-toggle-active"
                            : ""
                        }`}
                        onClick={() =>
                          updateRole(role.name, {
                            enabled: !role.enabled,
                            priority: role.enabled
                              ? "disabled"
                              : "discovery",
                          })
                        }
                        aria-label={`Toggle ${role.name}`}
                      >
                        {role.enabled ? <Check size={13} /> : null}
                      </button>

                      <div className="role-intelligence-main">
                        <div className="role-intelligence-title">
                          <strong>{role.name}</strong>

                          <span>
                            {percentage(role.confidence)}
                          </span>
                        </div>

                        <div className="role-confidence-track">
                          <div
                            className="role-confidence-fill"
                            style={{
                              width: percentage(
                                role.confidence,
                              ),
                            }}
                          />
                        </div>

                        <div className="role-signal-row">
                          {role.matched_signals
                            .slice(0, 6)
                            .map((signal) => (
                              <span key={signal}>
                                {signal}
                              </span>
                            ))}
                        </div>
                      </div>

                      <div className="profile-select-wrapper">
                        <select
                          value={role.priority}
                          disabled={!role.enabled}
                          onChange={(event) =>
                            updateRole(role.name, {
                              priority: event.target
                                .value as RolePriority,
                              enabled:
                                event.target.value !==
                                "disabled",
                            })
                          }
                        >
                          {priorities.map((option) => (
                            <option
                              value={option.value}
                              key={option.value}
                            >
                              {option.label}
                            </option>
                          ))}
                        </select>

                        <ChevronDown
                          size={14}
                          aria-hidden="true"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel">
                <div className="panel-kicker">
                  Skills intelligence
                </div>

                <h2>What the resume currently proves.</h2>

                <div className="profile-skill-group">
                  <span className="profile-skill-label">
                    Core
                  </span>

                  <div className="tag-row">
                    {profile.core_skills.map((skill) => (
                      <span
                        className="tag tag-positive"
                        key={skill}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="profile-skill-group">
                  <span className="profile-skill-label">
                    Secondary
                  </span>

                  <div className="tag-row">
                    {profile.secondary_skills.map((skill) => (
                      <span
                        className="profile-neutral-tag"
                        key={skill}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {profile.cloud_platforms.length ? (
                  <div className="profile-skill-group">
                    <span className="profile-skill-label">
                      Cloud
                    </span>

                    <div className="tag-row">
                      {profile.cloud_platforms.map((skill) => (
                        <span
                          className="profile-cloud-tag"
                          key={skill}
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            </div>

            <aside className="profile-side-column">
              <article className="panel">
                <div className="panel-kicker">
                  Search preferences
                </div>

                <h2>Ranking controls</h2>

                <label className="profile-field">
                  <span>Preferred locations</span>

                  <input
                    value={profile.preferences.preferred_locations.join(
                      ", ",
                    )}
                    placeholder="Bengaluru, Hyderabad"
                    onChange={(event) =>
                      updateLocations(event.target.value)
                    }
                  />

                  <small>
                    Separate locations with commas.
                  </small>
                </label>

                <label className="profile-field">
                  <span>Total experience</span>

                  <div className="profile-field-unit">
                    <input
                      type="number"
                      min="0"
                      max="50"
                      step="0.5"
                      value={
                        profile.total_experience_years ?? ""
                      }
                      placeholder="e.g. 3"
                      onChange={(event) =>
                        updateExperience(
                          event.target.value,
                        )
                      }
                    />

                    <span>years</span>
                  </div>

                  <small>
                    This will later be extracted automatically and verified.
                  </small>
                </label>
              </article>

              <article className="panel profile-next-card">
                <div className="panel-kicker">
                  Extraction quality
                </div>

                <h2>Baseline parser</h2>

                <p>
                  This first version intentionally uses deterministic
                  extraction. Structured enrichment will add experience,
                  companies, projects, education, and richer role evidence.
                </p>

                <div className="profile-quality-item">
                  <Check size={14} />
                  PDF text extraction
                </div>

                <div className="profile-quality-item">
                  <Check size={14} />
                  Deterministic skill extraction
                </div>

                <div className="profile-quality-item">
                  <Check size={14} />
                  Explainable role detection
                </div>

                <div className="profile-quality-item profile-quality-pending">
                  <RefreshCw size={14} />
                  Structured enrichment next
                </div>
              </article>
            </aside>
          </section>
        </>
      )}
    </div>
  );
}
