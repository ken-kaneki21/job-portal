import { Clock3, MailCheck, Play, ShieldCheck, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { PageHeader } from "../../components/ui/PageHeader";
import { ensureSchedule, getOpsStatus, testEmail, triggerSchedule } from "./opsApi";

export function AutomationsPage() {
  const query = useQuery({ queryKey: ["ops-status"], queryFn: getOpsStatus, staleTime: 30_000 });
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  async function act(name: string, fn: () => Promise<unknown>) {
    setBusy(name); setMessage("");
    try { await fn(); setMessage(`${name} completed successfully.`); await query.refetch(); }
    catch (err) { setMessage(err instanceof Error ? err.message : `${name} failed.`); }
    finally { setBusy(""); }
  }
  const data = query.data;
  return (
    <div className="page">
      <PageHeader eyebrow="Automations" title="A job search that keeps running."
        description="Production orchestration, daily discovery, notifications, and reliability controls." />
      <div className="automation-grid">
        <section className="panel automation-card">
          <div className="panel-kicker">DAILY INTELLIGENCE</div><Clock3 size={22} />
          <h2>{data?.schedule.enabled ? "Scheduled" : "Schedule disabled"}</h2>
          <p>{data?.schedule.cron ?? "0 8 * * *"} · {data?.schedule.timezone ?? "Asia/Kolkata"}</p>
          <button className="secondary-button" disabled={!!busy} onClick={() => void act("Schedule ensure", ensureSchedule)}>Ensure schedule</button>
        </section>
        <section className="panel automation-card">
          <div className="panel-kicker">ON DEMAND</div><Play size={22} /><h2>Run now</h2>
          <p>Trigger the durable Temporal schedule without waiting for tomorrow.</p>
          <button className="primary-action" disabled={!!busy} onClick={() => void act("Pipeline trigger", triggerSchedule)}>Run intelligence</button>
        </section>
        <section className="panel automation-card">
          <div className="panel-kicker">NOTIFICATIONS</div><MailCheck size={22} />
          <h2>{data?.notifications.daily_digest_enabled ? "Daily digest on" : "Digest off"}</h2>
          <p>{data?.notifications.resend_configured ? "Resend configured" : "Email provider incomplete"}</p>
          <button className="secondary-button" disabled={!!busy} onClick={() => void act("Test email", testEmail)}>Send test email</button>
        </section>
        <section className="panel automation-card">
          <div className="panel-kicker">PRODUCT READINESS</div><ShieldCheck size={22} />
          <h2>{data?.security.auth_configured ? "Private access" : "Auth not configured"}</h2>
          <p>Browser companion: {data?.security.companion_token_configured ? "ready" : "not configured"}</p>
          <div className="automation-inline"><Zap size={15} /> Embedding batch {data?.performance.embedding_batch_size ?? 32}</div>
        </section>
      </div>
      {message ? <div className="panel automation-message">{message}</div> : null}
    </div>
  );
}
