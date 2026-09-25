import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { apiRequest } from "../../lib/api";

type AuthState = { authenticated: boolean; auth_enabled: boolean; username?: string };

export function AuthGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<"loading" | "login" | "ready">("loading");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    void apiRequest<AuthState>("/auth/me")
      .then(() => setState("ready"))
      .catch(() => setState("login"));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true); setError("");
    try {
      await apiRequest<AuthState>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      setState("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally { setSubmitting(false); }
  }

  if (state === "loading") {
    return <div className="auth-screen"><div className="auth-card"><strong>Securing workspace…</strong></div></div>;
  }
  if (state === "login") {
    return (
      <div className="auth-screen">
        <form className="auth-card" onSubmit={submit}>
          <div className="auth-mark">JI</div>
          <p className="panel-kicker">PRIVATE WORKSPACE</p>
          <h1>Job Intelligence</h1>
          <p>Your ranked job search, application intelligence, and automation console.</p>
          <label>Username<input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} /></label>
          <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
          {error ? <div className="auth-error">{error}</div> : null}
          <button className="primary-action auth-submit" disabled={submitting} type="submit">
            {submitting ? "Signing in…" : "Enter workspace"}
          </button>
        </form>
      </div>
    );
  }
  return <>{children}</>;
}
