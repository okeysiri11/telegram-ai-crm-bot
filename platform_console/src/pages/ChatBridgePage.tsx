import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useRuntime } from "../context/RuntimeContext";
import { runtimeApi, type ChatTaskDto } from "../services/runtimeApi";

function statusTone(status: string): string {
  if (status === "Done") return "text-emerald-300";
  if (status === "Failed" || status === "Cancelled") return "text-rose-300";
  if (status === "Running" || status === "Review") return "text-sky-300";
  if (status === "PartialSuccess") return "text-amber-300";
  return "text-[var(--muted)]";
}

export function ChatBridgePage() {
  const { status, socket } = useRuntime();
  const qc = useQueryClient();
  const [prompt, setPrompt] = useState(
    "Implement a health check endpoint for the ChatGPT Bridge module",
  );

  const bridgeStatus = useQuery({
    queryKey: ["runtime", "chat-status"],
    queryFn: runtimeApi.chatStatus,
    refetchInterval: 2000,
  });
  const tasks = useQuery({
    queryKey: ["runtime", "chat-tasks"],
    queryFn: runtimeApi.chatTasks,
    refetchInterval: 2000,
  });
  const history = useQuery({
    queryKey: ["runtime", "chat-history"],
    queryFn: () => runtimeApi.chatHistory(40),
    refetchInterval: 3000,
  });
  const session = useQuery({
    queryKey: ["runtime", "chat-session"],
    queryFn: runtimeApi.chatSession,
    refetchInterval: 3000,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["runtime"] });
  };

  const createTask = useMutation({
    mutationFn: () =>
      runtimeApi.chatCreateTask({ prompt, autoRun: false }),
    onSuccess: invalidate,
  });
  const runTask = useMutation({
    mutationFn: (taskId?: string) => runtimeApi.chatRun(taskId),
    onSuccess: invalidate,
  });
  const cancelTask = useMutation({
    mutationFn: (taskId: string) => runtimeApi.chatCancel(taskId),
    onSuccess: invalidate,
  });
  const rollbackTask = useMutation({
    mutationFn: (taskId: string) => runtimeApi.chatRollback(taskId),
    onSuccess: invalidate,
  });

  const st = bridgeStatus.data;
  const queue = tasks.data?.queue;
  const rows = tasks.data?.tasks ?? [];
  const running = rows.filter((t) => t.status === "Running" || t.status === "Review");

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">ChatGPT Bridge</h1>
          <p className="text-sm text-[var(--muted)]">
            ChatGPT → ADOS → Cursor · WebSocket {socket.status} · system{" "}
            {status.data?.chatBridge ?? "…"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-white/5"
            onClick={() => createTask.mutate()}
            disabled={createTask.isPending || !prompt.trim()}
          >
            Ingest prompt
          </button>
          <button
            type="button"
            className="rounded-lg bg-sky-500/20 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/30"
            onClick={() => runTask.mutate(undefined)}
            disabled={runTask.isPending}
          >
            Run next
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card title="Current Provider" value={st?.currentProvider ?? "…"} />
        <Card title="Current Agent" value={st?.currentAgent ?? "—"} />
        <Card
          title="Queue"
          value={`${queue?.queued ?? 0}Q · ${queue?.running ?? 0}R · ${queue?.done ?? 0}✓`}
        />
        <Card
          title="Voice Ready"
          value={st?.voiceReady ? "Module ready" : "…"}
          ok={Boolean(st?.voiceReady)}
        />
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-2 text-sm font-medium">Current Prompt</h2>
        <textarea
          className="min-h-24 w-full rounded-xl border border-[var(--border)] bg-black/20 p-3 text-sm outline-none focus:border-sky-500/50"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Paste ChatGPT response / task here…"
        />
        <p className="mt-2 text-xs text-[var(--muted)]">
          Active: {st?.currentPrompt?.slice(0, 160) || "none"}
          {st?.currentTask?.durationMs
            ? ` · last duration ${st.currentTask.durationMs} ms`
            : ""}
        </p>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Running Tasks</h2>
          <TaskList
            tasks={running.length ? running : rows.slice(0, 8)}
            onRun={(id) => runTask.mutate(id)}
            onCancel={(id) => cancelTask.mutate(id)}
            onRollback={(id) => rollbackTask.mutate(id)}
          />
        </section>
        <section className="glass rounded-2xl border border-[var(--border)] p-4">
          <h2 className="mb-3 text-sm font-medium">Generated Files</h2>
          <ul className="max-h-64 space-y-1 overflow-y-auto text-xs text-[var(--muted)]">
            {(st?.generatedFiles ?? session.data?.session.generatedFiles ?? []).map(
              (f) => (
                <li key={f} className="font-mono text-sky-200/90">
                  {f}
                </li>
              ),
            )}
            {(st?.generatedFiles?.length ?? 0) === 0 &&
              (session.data?.session.generatedFiles.length ?? 0) === 0 && (
                <li>No files yet</li>
              )}
          </ul>
        </section>
      </div>

      <section className="glass rounded-2xl border border-[var(--border)] p-4">
        <h2 className="mb-3 text-sm font-medium">Prompt History</h2>
        <div className="max-h-72 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[var(--muted)]">
              <tr>
                <th className="py-1 pr-2">Time</th>
                <th className="py-1 pr-2">Provider</th>
                <th className="py-1 pr-2">Status</th>
                <th className="py-1 pr-2">Duration</th>
                <th className="py-1">Prompt</th>
              </tr>
            </thead>
            <tbody>
              {(history.data?.history ?? []).map((h) => (
                <tr key={h.id} className="border-t border-[var(--border)]/60">
                  <td className="py-1.5 pr-2 whitespace-nowrap text-[var(--muted)]">
                    {new Date(h.at).toLocaleTimeString()}
                  </td>
                  <td className="py-1.5 pr-2">{h.provider}</td>
                  <td className={`py-1.5 pr-2 ${statusTone(String(h.status))}`}>
                    {h.status}
                  </td>
                  <td className="py-1.5 pr-2">
                    {h.durationMs != null ? `${h.durationMs} ms` : "—"}
                  </td>
                  <td className="py-1.5 max-w-md truncate">{h.prompt}</td>
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

function TaskList({
  tasks,
  onRun,
  onCancel,
  onRollback,
}: {
  tasks: ChatTaskDto[];
  onRun: (id: string) => void;
  onCancel: (id: string) => void;
  onRollback: (id: string) => void;
}) {
  if (!tasks.length) {
    return <p className="text-xs text-[var(--muted)]">No tasks in queue</p>;
  }
  return (
    <ul className="max-h-72 space-y-2 overflow-y-auto">
      {tasks.map((t) => (
        <li
          key={t.id}
          className="rounded-xl border border-[var(--border)]/70 bg-black/10 p-3"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="text-sm font-medium">{t.title}</div>
              <div className="text-[10px] text-[var(--muted)]">
                {t.kind} · {t.preferredAgent} ·{" "}
                <span className={statusTone(t.status)}>{t.status}</span>
                {t.durationMs != null ? ` · ${t.durationMs} ms` : ""}
              </div>
            </div>
            <div className="flex shrink-0 gap-1">
              {t.status === "Queued" && (
                <button
                  type="button"
                  className="rounded px-2 py-0.5 text-[10px] text-sky-200 hover:bg-sky-500/20"
                  onClick={() => onRun(t.id)}
                >
                  Run
                </button>
              )}
              {(t.status === "Queued" || t.status === "Running") && (
                <button
                  type="button"
                  className="rounded px-2 py-0.5 text-[10px] text-rose-200 hover:bg-rose-500/20"
                  onClick={() => onCancel(t.id)}
                >
                  Cancel
                </button>
              )}
              {(t.status === "Done" ||
                t.status === "Failed" ||
                t.status === "PartialSuccess") && (
                <button
                  type="button"
                  className="rounded px-2 py-0.5 text-[10px] text-amber-200 hover:bg-amber-500/20"
                  onClick={() => onRollback(t.id)}
                >
                  Rollback
                </button>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
