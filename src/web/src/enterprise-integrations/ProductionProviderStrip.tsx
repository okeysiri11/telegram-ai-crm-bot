/**
 * Sprint 31.2 — Production Studio AI provider selector + cost + n8n launch.
 * Reads providerRegistry (APH-aligned). No studio-local provider engine.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import {
  aiFailoverChain,
  estimateCostUsd,
  providersByCategory,
  type ProviderEntry,
} from "./providerRegistry";
import {
  launchN8nWorkflow,
  listN8nExecutions,
  listWorkflowTemplates,
  n8nMonitorSnapshot,
  N8N_UI,
  completeN8nExecution,
} from "./n8nBridge";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";

type Props = {
  /** Compact strip for Production / AI Studio headers */
  compact?: boolean;
};

export function ProductionProviderStrip({ compact = false }: Props) {
  const push = useNotificationStore((s) => s.push);
  const aiProviders = useMemo(() => providersByCategory("ai").filter((p) => p.ready), []);
  const chain = useMemo(() => aiFailoverChain(), []);
  const [providerId, setProviderId] = useState(aiProviders[0]?.id || "openai");
  const [tokens, setTokens] = useState(2000);
  const [tick, setTick] = useState(0);
  const cost = estimateCostUsd(providerId, tokens);
  const selected: ProviderEntry | undefined = aiProviders.find((p) => p.id === providerId);
  const monitor = useMemo(() => {
    void tick;
    return n8nMonitorSnapshot();
  }, [tick]);
  const recent = useMemo(() => {
    void tick;
    return listN8nExecutions().slice(0, 3);
  }, [tick]);
  const templates = listWorkflowTemplates().filter((t) => t.tags.includes("production") || t.tags.includes("media") || t.tags.includes("ai"));

  function launch(templateId: string) {
    const ex = launchN8nWorkflow(templateId);
    void telemetry.userActivity(`n8n_launch:${templateId}`);
    push({
      kind: "workflow",
      title: "n8n workflow запущен",
      body: `${templateId} · Runtime остаётся SoR · ${ex.id}`,
      level: "info",
    });
    // Demo callback settle — production would use real webhook
    window.setTimeout(() => {
      completeN8nExecution(ex.id, "success");
      setTick((t) => t + 1);
    }, 600);
    setTick((t) => t + 1);
  }

  return (
    <Card
      title="AI Providers · Cost · n8n"
      status={<Badge tone="success">APH</Badge>}
      data-testid="production-provider-strip"
    >
      <div className={`grid gap-3 ${compact ? "lg:grid-cols-2" : "lg:grid-cols-3"}`}>
        <div>
          <p className="eds-type-caption mb-1">Провайдер (через APH)</p>
          <select
            className="w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1.5 eds-type-small"
            value={providerId}
            onChange={(e) => setProviderId(e.target.value)}
            aria-label="AI provider"
            data-testid="provider-selector"
          >
            {aiProviders.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
          <p className="eds-type-helper mt-1">
            Failover: {chain.slice(0, 4).map((p) => p.title).join(" → ")}
          </p>
        </div>
        <div>
          <p className="eds-type-caption mb-1">Оценка стоимости</p>
          <label className="eds-type-helper block">
            Токены{" "}
            <input
              type="number"
              min={100}
              step={100}
              value={tokens}
              onChange={(e) => setTokens(Number(e.target.value) || 0)}
              className="ml-1 w-24 rounded border border-[var(--ew-border)] bg-transparent px-1"
            />
          </label>
          <p className="mt-1 font-semibold eds-type-small" data-testid="cost-estimate">
            ≈ ${cost.toFixed(4)} · {selected?.title}
          </p>
        </div>
        <div>
          <p className="eds-type-caption mb-1">n8n Launch</p>
          <div className="flex flex-wrap gap-2">
            {templates.map((t) => (
              <Button key={t.id} size="sm" variant="secondary" onClick={() => launch(t.id)}>
                {t.name}
              </Button>
            ))}
            <a href={N8N_UI.defaultUrl} target="_blank" rel="noreferrer">
              <Button size="sm" variant="ghost">
                Открыть n8n
              </Button>
            </a>
          </div>
          <p className="eds-type-helper mt-1">
            Exec {monitor.executions} · SoR {monitor.systemOfRecord}
          </p>
        </div>
      </div>
      {!compact ? (
        <div className="mt-3 flex flex-wrap gap-3 eds-type-small">
          <Link className="text-[var(--eds-primary)]" to="/integrations">
            Integration Hub →
          </Link>
          <Link className="text-[var(--eds-primary)]" to="/platform-builder/workflow-center">
            Workflow Builder →
          </Link>
          <span className="eds-type-helper">
            Недавние:{" "}
            {recent.map((e) => `${e.templateId}:${e.status}`).join(" · ") || "нет"}
          </span>
        </div>
      ) : null}
    </Card>
  );
}
