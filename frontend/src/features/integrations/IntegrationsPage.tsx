
import { useState } from "react";
import { FileUp, Link2, ScanSearch, ShieldCheck, Sparkles } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import {
  extractHiringPost,
  importPortalFile,
  type HiringPostResult,
  type PortalImportResult,
  type PortalName,
} from "./integrationsApi";

const portals: PortalName[] = ["linkedin", "naukri", "foundit", "indeed"];

export function IntegrationsPage() {
  const [portal, setPortal] = useState<PortalName>("linkedin");
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<PortalImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [postText, setPostText] = useState("");
  const [postUrl, setPostUrl] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [postResult, setPostResult] = useState<HiringPostResult | null>(null);
  const [postError, setPostError] = useState<string | null>(null);

  async function handlePortalImport() {
    if (!file) {
      setImportError("Choose a CSV or JSON export first.");
      return;
    }
    setImporting(true);
    setImportError(null);
    setImportResult(null);
    try {
      setImportResult(await importPortalFile(portal, file));
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Portal import failed.");
    } finally {
      setImporting(false);
    }
  }

  async function handlePostExtract() {
    if (postText.trim().length < 10) {
      setPostError("Paste a hiring post with at least 10 characters.");
      return;
    }
    setExtracting(true);
    setPostError(null);
    setPostResult(null);
    try {
      setPostResult(await extractHiringPost(postText, postUrl));
    } catch (error) {
      setPostError(
        error instanceof Error ? error.message : "Hiring-post extraction failed.",
      );
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="page">
      <PageHeader
        eyebrow="Integrations"
        title="Portal imports and hiring-post intelligence."
        description="Bring user-provided job exports and visible hiring posts into the workspace without credential scraping or blind auto-submit."
      />

      <div className="completion-grid">
        <section className="panel completion-panel">
          <div className="completion-panel-heading">
            <div className="settings-icon"><FileUp size={19} /></div>
            <div>
              <div className="panel-kicker">Portal import</div>
              <h2>LinkedIn, Naukri, Foundit & Indeed</h2>
            </div>
          </div>

          <p className="completion-copy">
            Upload CSV or JSON exports. Existing normalization, dedupe and provenance
            logic persists the resulting jobs into the database.
          </p>

          <label className="completion-label">
            Portal
            <select
              className="completion-input"
              value={portal}
              onChange={(event) => setPortal(event.target.value as PortalName)}
            >
              {portals.map((value) => (
                <option key={value} value={value}>
                  {value[0].toUpperCase() + value.slice(1)}
                </option>
              ))}
            </select>
          </label>

          <label className="completion-label">
            Export file
            <input
              className="completion-input"
              type="file"
              accept=".csv,.json,application/json,text/csv"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setImportResult(null);
                setImportError(null);
              }}
            />
          </label>

          <button
            className="primary-action"
            type="button"
            disabled={importing || !file}
            onClick={() => void handlePortalImport()}
          >
            {importing ? "Importing..." : "Import jobs"}
          </button>

          {importError ? (
            <div className="completion-message completion-error">{importError}</div>
          ) : null}

          {importResult ? (
            <div className="completion-result">
              <strong>Import complete</strong>
              <div className="completion-metrics">
                <span>{importResult.valid_rows} valid rows</span>
                <span>{importResult.new_jobs} new jobs</span>
                <span>{importResult.matched_existing} matched existing</span>
                <span>{importResult.existing_source} already known</span>
              </div>
            </div>
          ) : null}
        </section>

        <section className="panel completion-panel">
          <div className="completion-panel-heading">
            <div className="settings-icon"><ScanSearch size={19} /></div>
            <div>
              <div className="panel-kicker">Hiring-post intelligence</div>
              <h2>Capture a visible LinkedIn hiring post</h2>
            </div>
          </div>

          <label className="completion-label">
            Source URL
            <div className="completion-input-with-icon">
              <Link2 size={16} />
              <input
                value={postUrl}
                onChange={(event) => setPostUrl(event.target.value)}
                placeholder="https://www.linkedin.com/posts/..."
              />
            </div>
          </label>

          <label className="completion-label">
            Hiring post
            <textarea
              className="completion-textarea"
              value={postText}
              onChange={(event) => setPostText(event.target.value)}
              placeholder="Paste the visible hiring post text here..."
            />
          </label>

          <button
            className="primary-action"
            type="button"
            disabled={extracting || postText.trim().length < 10}
            onClick={() => void handlePostExtract()}
          >
            <Sparkles size={16} />
            {extracting ? "Extracting..." : "Extract intelligence"}
          </button>

          {postError ? (
            <div className="completion-message completion-error">{postError}</div>
          ) : null}

          {postResult ? (
            <div className="completion-result">
              <strong>{postResult.role ?? "Role needs review"}</strong>
              <div className="completion-metrics">
                <span>{postResult.company ?? "Company not detected"}</span>
                <span>{postResult.location ?? "Location not detected"}</span>
                <span>
                  {postResult.minimum_experience_years === null
                    ? "Experience not detected"
                    : `${postResult.minimum_experience_years}+ years`}
                </span>
              </div>
              <div className="completion-tags">
                {postResult.skills.map((skill) => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>
              {postResult.contact_emails.length > 0 ? (
                <small>Contact: {postResult.contact_emails.join(", ")}</small>
              ) : null}
            </div>
          ) : null}
        </section>

        <section className="panel completion-panel completion-wide">
          <div className="completion-panel-heading">
            <div className="settings-icon"><ShieldCheck size={19} /></div>
            <div>
              <div className="panel-kicker">Application assistant</div>
              <h2>Review-first automation stays enforced</h2>
            </div>
          </div>

          <div className="completion-safety-grid">
            <div>
              <strong>Profile answer bank</strong>
              <span>Identity, experience, notice period, links and reusable answers feed the existing assist APIs.</span>
            </div>
            <div>
              <strong>Workday assistance</strong>
              <span>Field aliases, resume upload and required-field detection remain available through the existing Playwright workflow.</span>
            </div>
            <div>
              <strong>Sensitive fields</strong>
              <span>Compensation and review-required answers stay explicitly review-first.</span>
            </div>
            <div>
              <strong>Final submission</strong>
              <span>Auto-submit remains disabled. You review the browser state before submitting.</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
