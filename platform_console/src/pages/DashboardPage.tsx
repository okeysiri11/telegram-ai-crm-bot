import { StatusCard } from "../components/StatusCard";
import { useRuntime } from "../context/RuntimeContext";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function formatUptime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${h}h ${m}m ${s}s`;
}

export function DashboardPage() {
  const { status, metrics, health, connected, socket } = useRuntime();
  const st = status.data;
  const m = metrics.data;
  const ready = st?.systemStatus === "READY";

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-[var(--muted)]">
          Live ADOS Runtime · refresh 2s · WebSocket {socket.status}
          {!connected ? " · waiting for Runtime Server on :3000" : ""}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        <StatusCard
          title="System Status"
          value={st?.systemStatus ?? "…"}
          subtitle={health.data?.status === "ok" ? "health ok" : "health unavailable"}
          ok={ready}
        />
        <StatusCard
          title="Runtime Status"
          value={st?.runtimeServer ?? (connected ? "OK" : "DOWN")}
          ok={Boolean(st?.runtimeServer === "OK" || connected)}
        />
        <StatusCard title="Kernel" value={st?.kernel ?? "…"} ok={st?.kernel === "OK"} />
        <StatusCard title="Event Bus" value={st?.eventBus ?? "…"} ok={st?.eventBus === "OK"} />
        <StatusCard
          title="Service Mesh"
          value={st?.serviceMesh ?? "…"}
          ok={st?.serviceMesh === "OK"}
        />
        <StatusCard
          title="Workflow Engine"
          value={st?.workflowEngine ?? "…"}
          ok={st?.workflowEngine === "OK"}
        />
        <StatusCard
          title="AI Orchestrator"
          value={st?.orchestrator ?? "…"}
          subtitle={
            st
              ? `${st.agents ?? 0} agents · ${st.runningTasks ?? 0} running · queue ${st.queueSize ?? 0}`
              : undefined
          }
          ok={st?.orchestrator === "OK"}
        />
        <StatusCard
          title="Provider Gateway"
          value={st?.providerGateway ?? "…"}
          subtitle={
            st
              ? `${st.providersConnected ?? 0}/${st.providers ?? 0} connected`
              : undefined
          }
          ok={st?.providerGateway === "OK"}
        />
        <StatusCard
          title="ChatGPT Bridge"
          value={st?.chatBridge ?? "…"}
          subtitle="ChatGPT → Cursor middleware"
          ok={st?.chatBridge === "OK"}
        />
        <StatusCard
          title="Voice Module"
          value={st?.voice ?? "…"}
          subtitle="Speech → Intent → Bridge"
          ok={st?.voice === "OK"}
        />
        <StatusCard
          title="MCP Gateway"
          value={st?.mcp ?? "…"}
          subtitle="Claude Desktop → Runtime"
          ok={st?.mcp === "OK"}
        />
        <StatusCard
          title="Execution Planner"
          value={st?.execution ?? "…"}
          subtitle="Specs → Agent work packages"
          ok={st?.execution === "OK"}
        />
        <StatusCard
          title="AI Overview"
          value={`${st?.agents ?? 0} agents`}
          subtitle={`queue ${st?.queueSize ?? 0} · tasks ${st?.runningTasks ?? 0}`}
          ok={(st?.agents ?? 0) >= 7}
        />
        <StatusCard
          title="Memory Usage"
          value={m ? formatBytes(m.memory.heapUsed) : "…"}
          subtitle={m ? `RSS ${formatBytes(m.memory.rss)}` : undefined}
        />
        <StatusCard
          title="CPU Usage"
          value={
            m
              ? `${((m.cpu.userMicros + m.cpu.systemMicros) / 1000).toFixed(1)} ms`
              : "…"
          }
          subtitle="process cpu delta"
        />
        <StatusCard
          title="Uptime"
          value={m ? formatUptime(m.uptimeSec) : "…"}
          subtitle={m?.startedAt}
        />
      </div>
    </div>
  );
}
