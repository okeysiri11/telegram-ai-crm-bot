/**
 * Voice Command Center — Sprint 36.6.
 * Voice Dashboard · Live Microphone · Sessions · Command History · Device Manager · Voice Profiles · Statistics
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const VOICE_API = "/api/voice";

type SectionId =
  | "voice-dashboard"
  | "live-microphone"
  | "sessions"
  | "command-history"
  | "device-manager"
  | "voice-profiles"
  | "statistics";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "voice-dashboard", label: "Voice Dashboard" },
  { id: "live-microphone", label: "Live Microphone" },
  { id: "sessions", label: "Sessions" },
  { id: "command-history", label: "Command History" },
  { id: "device-manager", label: "Device Manager" },
  { id: "voice-profiles", label: "Voice Profiles" },
  { id: "statistics", label: "Statistics" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${VOICE_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function VoiceCommandCenterPage() {
  const [section, setSection] = useState<SectionId>("voice-dashboard");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [providers, setProviders] = useState<Array<Record<string, unknown>>>([]);
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const [commands, setCommands] = useState<Array<Record<string, unknown>>>([]);
  const [devices, setDevices] = useState<Array<Record<string, unknown>>>([]);
  const [profiles, setProfiles] = useState<Array<Record<string, unknown>>>([]);
  const [statistics, setStatistics] = useState<Record<string, unknown> | null>(null);
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [transcript, setTranscript] = useState("open CRM");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [st, prov, sess, cmds, devs, profs, stats] = await Promise.all([
      api<Record<string, unknown>>("/status"),
      api<{ providers: Array<Record<string, unknown>> }>("/providers"),
      api<{ sessions: Array<Record<string, unknown>> }>("/sessions"),
      api<{ commands: Array<Record<string, unknown>> }>("/commands"),
      api<{ devices: Array<Record<string, unknown>> }>("/devices"),
      api<{ profiles: Array<Record<string, unknown>> }>("/profiles"),
      api<Record<string, unknown>>("/statistics"),
    ]);
    setStatus(st);
    setProviders(prov.providers || []);
    setSessions(sess.sessions || []);
    setCommands(cmds.commands || []);
    setDevices(devs.devices || []);
    setProfiles(profs.profiles || []);
    setStatistics(stats);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const startSession = async () => {
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>("/sessions", {
        method: "POST",
        body: JSON.stringify({ mode: "push_to_talk", profile_id: "vprof_default" }),
      });
      setSessionId(String(data.session_id || ""));
      await refresh();
      setSection("sessions");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const processVoice = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api<Record<string, unknown>>("/process", {
        method: "POST",
        body: JSON.stringify({
          transcript,
          session_id: sessionId || undefined,
          confirmed: true,
        }),
      });
      setLastResult(data);
      if (data.session && typeof data.session === "object") {
        const sid = (data.session as Record<string, unknown>).session_id;
        if (sid) setSessionId(String(sid));
      }
      await refresh();
      setSection("live-microphone");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Voice Command Center" subtitle="Sprint 36.6 · speak · parse · execute">
      <div className="space-y-4" data-testid="voice-command-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="eds-type-small text-[var(--eds-muted)]">
            Control the enterprise platform with natural-language voice commands.
          </p>
          <div className="flex gap-2 items-center">
            {busy ? <Badge>busy…</Badge> : <Badge tone="success">ready</Badge>}
            <Button type="button" onClick={() => refresh().catch((e) => setError(String(e.message || e)))}>
              Refresh
            </Button>
          </div>
        </header>

        {error ? (
          <Card className="p-3 text-[var(--eds-danger)]" role="alert">
            {error}
          </Card>
        ) : null}

        <nav className="flex flex-wrap gap-2" aria-label="Voice Command Center sections">
          {SECTIONS.map((s) => (
            <Button
              key={s.id}
              type="button"
              variant={section === s.id ? "primary" : "ghost"}
              onClick={() => setSection(s.id)}
            >
              {s.label}
            </Button>
          ))}
        </nav>

        {section === "voice-dashboard" && (
          <Card className="p-4 space-y-3" aria-label="Voice Dashboard">
            <h2 className="text-lg font-medium">Voice Dashboard</h2>
            <p className="text-sm text-[var(--eds-muted)]">
              Providers {providers.length} · Sessions {sessions.length} · Commands {commands.length}
            </p>
            <pre className="text-xs overflow-auto max-h-80 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(status || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "live-microphone" && (
          <Card className="p-4 space-y-3" aria-label="Live Microphone">
            <h2 className="text-lg font-medium">Live Microphone</h2>
            <div className="flex gap-2 flex-wrap">
              <Input
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                aria-label="Transcript"
              />
              <Button type="button" onClick={startSession} disabled={busy}>
                Start Session
              </Button>
              <Button type="button" onClick={processVoice} disabled={busy}>
                Push to Talk
              </Button>
            </div>
            <p className="text-xs text-[var(--eds-muted)]">Session: {sessionId || "—"}</p>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(lastResult || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "sessions" && (
          <Card className="p-4 space-y-2" aria-label="Sessions">
            <h2 className="text-lg font-medium">Sessions</h2>
            <ul className="space-y-1 text-sm">
              {sessions.map((s) => (
                <li key={String(s.session_id)} className="flex justify-between gap-2">
                  <span>
                    {String(s.session_id)} · {String(s.mode)} · {String(s.principal)}
                  </span>
                  <Badge>{String(s.status)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "command-history" && (
          <Card className="p-4 space-y-2" aria-label="Command History">
            <h2 className="text-lg font-medium">Command History</h2>
            <ul className="space-y-1 text-sm">
              {commands.map((c) => (
                <li key={String(c.command_id)} className="flex justify-between gap-2">
                  <span>
                    {String(c.intent)} · {String(c.transcript).slice(0, 48)}
                  </span>
                  <Badge>{String(c.status)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "device-manager" && (
          <Card className="p-4 space-y-2" aria-label="Device Manager">
            <h2 className="text-lg font-medium">Device Manager</h2>
            <ul className="space-y-1 text-sm">
              {devices.map((d) => (
                <li key={String(d.device_id)} className="flex justify-between gap-2">
                  <span>
                    {String(d.name)} · {String(d.kind)}
                  </span>
                  <Badge tone={d.online ? "success" : "warning"}>{d.online ? "online" : "offline"}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "voice-profiles" && (
          <Card className="p-4 space-y-2" aria-label="Voice Profiles">
            <h2 className="text-lg font-medium">Voice Profiles</h2>
            <ul className="space-y-1 text-sm">
              {profiles.map((p) => (
                <li key={String(p.profile_id)}>
                  {String(p.name)} · wake “{String(p.wake_word)}” · {String(p.mode)}
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "statistics" && (
          <Card className="p-4 space-y-2" aria-label="Statistics">
            <h2 className="text-lg font-medium">Statistics</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(statistics || {}, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
