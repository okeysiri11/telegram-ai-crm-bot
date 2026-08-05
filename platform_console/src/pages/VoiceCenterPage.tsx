import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi } from "../services/runtimeApi";

export function VoiceCenterPage() {
  const { status, socket } = useRuntime();
  const qc = useQueryClient();
  const [text, setText] = useState("Hey ADOS generate code for voice badge");
  const [wakeWord, setWakeWord] = useState("Hey ADOS");

  const voiceStatus = useQuery({
    queryKey: ["runtime", "voice-status"],
    queryFn: runtimeApi.voiceStatus,
    refetchInterval: 2000,
  });
  const history = useQuery({
    queryKey: ["runtime", "voice-history"],
    queryFn: () => runtimeApi.voiceHistory(40),
    refetchInterval: 3000,
  });
  const settings = useQuery({
    queryKey: ["runtime", "voice-settings"],
    queryFn: runtimeApi.voiceSettings,
    refetchInterval: 5000,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["runtime"] });
  };

  const start = useMutation({
    mutationFn: () => runtimeApi.voiceStart(),
    onSuccess: invalidate,
  });
  const stop = useMutation({
    mutationFn: () => runtimeApi.voiceStop(),
    onSuccess: invalidate,
  });
  const process = useMutation({
    mutationFn: () =>
      runtimeApi.voiceProcess({
        text,
        bypassWakeWord: !(settings.data?.settings.wakeWordEnabled ?? true),
      }),
    onSuccess: invalidate,
  });
  const saveSettings = useMutation({
    mutationFn: () =>
      runtimeApi.voiceUpdateSettings({
        wakeWord,
        autoExecute: settings.data?.settings.autoExecute ?? true,
      }),
    onSuccess: invalidate,
  });

  const st = voiceStatus.data;
  const last = process.data ?? null;
  const mic = st?.microphone;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Voice Center</h1>
          <p className="text-sm text-[var(--muted)]">
            Enterprise Voice · WS {socket.status} · module{" "}
            {status.data?.voice ?? "…"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => start.mutate()}
          >
            Start session
          </button>
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => stop.mutate()}
          >
            Stop
          </button>
          <button
            type="button"
            className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
            onClick={() => process.mutate()}
            disabled={process.isPending || !text.trim()}
          >
            Process voice
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          title="Microphone"
          value={
            mic?.permissionGranted
              ? mic.recording
                ? "Recording"
                : "Ready"
              : "No access"
          }
          ok={Boolean(mic?.permissionGranted)}
        />
        <Card
          title="Session"
          value={st?.session?.state ?? "idle"}
        />
        <Card title="Provider" value={st?.speechProvider ?? "…"} />
        <Card title="Agent" value={st?.currentAgent ?? "—"} />
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-2 text-sm font-medium">Utterance</h2>
        <textarea
          className="min-h-24 w-full rounded-xl border border-[var(--border)] bg-black/20 p-3 text-sm outline-none focus:border-sky-500/50"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Speak or type a command…"
        />
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <label className="text-xs text-[var(--muted)]">
            Wake word
            <input
              className="mt-1 block rounded-lg border border-[var(--border)] bg-black/20 px-3 py-1.5 text-sm text-white"
              value={wakeWord}
              onChange={(e) => setWakeWord(e.target.value)}
            />
          </label>
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => saveSettings.mutate()}
          >
            Save settings
          </button>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Recognition</h2>
          <dl className="space-y-2 text-sm">
            <Row
              label="Recognized text"
              value={last?.transcription.text ?? "—"}
            />
            <Row label="Intent" value={last?.intent ?? st?.lastCommand?.intent ?? "—"} />
            <Row
              label="Confidence"
              value={
                last
                  ? `${Math.round(last.confidence * 100)}%`
                  : st?.lastCommand
                    ? `${Math.round(st.lastCommand.confidence * 100)}%`
                    : "—"
              }
            />
            <Row
              label="Execution"
              value={
                last
                  ? last.executed
                    ? "Executed"
                    : last.command.status
                  : st?.lastCommand?.status ?? "—"
              }
            />
            <Row label="Response" value={last?.responseText ?? st?.lastCommand?.responseText ?? "—"} />
          </dl>
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Settings</h2>
          <dl className="space-y-2 text-sm">
            <Row label="Language" value={settings.data?.settings.language ?? "…"} />
            <Row label="Wake word" value={settings.data?.settings.wakeWord ?? "…"} />
            <Row
              label="Auto execute"
              value={String(settings.data?.settings.autoExecute ?? "…")}
            />
            <Row
              label="Push to talk"
              value={String(settings.data?.settings.pushToTalk ?? "…")}
            />
            <Row
              label="Continuous"
              value={String(settings.data?.settings.continuousListening ?? "…")}
            />
            <Row
              label="TTS"
              value={settings.data?.settings.ttsProvider ?? "…"}
            />
          </dl>
        </section>
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-3 text-sm font-medium">Voice History</h2>
        <div className="max-h-72 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[var(--muted)]">
              <tr>
                <th className="py-1 pr-2">Time</th>
                <th className="py-1 pr-2">Intent</th>
                <th className="py-1 pr-2">Status</th>
                <th className="py-1">Text</th>
              </tr>
            </thead>
            <tbody>
              {(history.data?.history ?? []).map((h) => (
                <tr key={h.id} className="border-t border-[var(--border)]/60">
                  <td className="py-1.5 pr-2 whitespace-nowrap text-[var(--muted)]">
                    {new Date(h.at).toLocaleTimeString()}
                  </td>
                  <td className="py-1.5 pr-2">{h.intent}</td>
                  <td className="py-1.5 pr-2">{h.status}</td>
                  <td className="py-1.5 max-w-md truncate">{h.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Card({
  title,
  value,
  ok,
}: {
  title: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="glass rounded-2xl border border-[var(--border)] p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">
        {title}
      </div>
      <div
        className={`mt-1 truncate text-lg font-semibold ${
          ok === undefined ? "" : ok ? "text-emerald-300" : "text-rose-300"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-32 shrink-0 text-[var(--muted)]">{label}</dt>
      <dd className="min-w-0 flex-1 break-words">{value}</dd>
    </div>
  );
}
