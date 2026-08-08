/**
 * Sprint 28.5 / 41.3 / 42.2 — Runtime bar: Expanded · Compact · Hidden.
 */

import { useRuntimeEngine } from "@/enterprise-runtime/useRuntimeEngine";
import { StatusBar } from "./StatusBar";
import { useI18n } from "@/i18n";
import { useAdaptiveShellStore } from "./adaptiveShellStore";
import { Button } from "@/ui";
import { cn } from "@/utils/cn";

export function ShellRuntimeBar() {
  const t = useI18n((s) => s.t);
  const mode = useAdaptiveShellStore((s) => s.runtimeMode);
  const cycleRuntime = useAdaptiveShellStore((s) => s.cycleRuntime);
  const setRuntimeMode = useAdaptiveShellStore((s) => s.setRuntimeMode);
  const snap = useRuntimeEngine();
  const m = snap.metrics;

  if (mode === "hidden") {
    return (
      <div className="ews-runtime-peek" data-testid="runtime-bar">
        <Button size="sm" variant="ghost" onClick={() => setRuntimeMode("compact")} aria-label={t("shell.runtime.show")}>
          {t("runtime.bar")} ▴
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn("ews-runtime-bar ews-runtime--anim", mode === "compact" && "ews-runtime-bar--compact")}
      aria-label={t("runtime.bar")}
      data-mode={mode}
      data-testid="runtime-bar"
    >
      <div className="ews-runtime-bar-head">
        <Button size="sm" variant="ghost" onClick={() => cycleRuntime()} data-testid="runtime-cycle" title={t("shell.runtime.cycle")}>
          {mode === "expanded" ? "▾" : "▴"}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setRuntimeMode("hidden")} aria-label={t("shell.runtime.hide")}>
          ×
        </Button>
      </div>
      {mode === "expanded" ? (
        <div
          className="ews-runtime-metrics eds-type-helper"
          style={{ display: "flex", gap: 12, flexWrap: "wrap", padding: "0.25rem 0.75rem" }}
        >
          <span>CPU {m.cpuPct}%</span>
          <span>Mem {m.memoryPct}%</span>
          <span>Queue G{m.queueGeneration ?? 0}/R{m.queueRender ?? 0}</span>
          <span>
            {t("runtime.jobs")} {m.jobsRunning}/{m.jobsWaiting}
          </span>
          <span>AI {m.agentsActive}</span>
          <span>
            {t("runtime.providers")} {m.providersOnline}/{m.providersTotal}
          </span>
          <span>
            {t("runtime.workers")} {m.workers}
          </span>
          <span title={m.heartbeatAt}>
            {t("runtime.heartbeat")} {m.tick}
          </span>
        </div>
      ) : null}
      <StatusBar />
    </div>
  );
}
