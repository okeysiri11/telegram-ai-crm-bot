/**
 * Recruiting infrastructure diagnostics — states stay truthful.
 * NOT_CONFIGURED is never shown as ERROR.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Card } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { recruitingOpsGet, recruitingOpsPost, recruitingOpsUserError, recruitingWorkspaceHeaders } from "./recruitingApi";
import { mapUiRoleToRecruiting } from "./recruitingLabels";
import { RecruitingOpsFrame } from "./RecruitingOpsFrame";

type Chip = {
  code?: string;
  label_ru?: string;
  tone?: string;
  reason_ru?: string;
  missing?: string[];
  backend?: string;
  shared?: boolean;
  required_env?: string[];
};

type Diagnostics = {
  components?: Record<string, Chip>;
  tracking?: {
    delivered?: number;
    retrying?: number;
    failed?: number;
    pending?: number;
    processing?: number;
    waiting_provider?: number;
    dead_letter?: number;
    provider_not_configured?: number;
    oldest_pending?: string | null;
    last_delivery?: string | null;
  };
};

const ROWS: { id: string; label: string }[] = [
  { id: "postgresql", label: "PostgreSQL" },
  { id: "redis", label: "Redis" },
  { id: "rate_limit_store", label: "Rate Limit Store" },
  { id: "replay_store", label: "Replay Store" },
  { id: "tracking_worker", label: "Tracking Worker" },
  { id: "vanguard_integration", label: "Интеграция Vanguard" },
  { id: "vanguard_website", label: "Сайт Vanguard" },
  { id: "meta_ads", label: "Meta Ads" },
  { id: "google_ads", label: "Google Ads" },
  { id: "tiktok_ads", label: "TikTok Ads" },
  { id: "telegram", label: "Telegram" },
  { id: "whatsapp", label: "WhatsApp" },
  { id: "email", label: "Email" },
  { id: "anti_bot", label: "Антибот" },
  { id: "ci_e2e", label: "CI E2E" },
];

function asRecord(json: unknown): Diagnostics {
  return json && typeof json === "object" ? (json as Diagnostics) : {};
}

function toneFor(chip: Chip): "success" | "info" | "warning" | "danger" | "default" {
  const code = chip.code || "";
  const label = chip.label_ru || "";
  if (code === "NOT_CONFIGURED" || label === "Не настроено") return "info";
  if (code === "CONNECTED" || label === "Работает") return "success";
  if (code === "ERROR" || code === "DISCONNECTED" || label === "Ошибка") return "danger";
  if (code === "DEGRADED" || code === "CONFIGURED" || label === "Ограничено") return "warning";
  if (chip.tone === "success" || chip.tone === "info" || chip.tone === "warning" || chip.tone === "danger") {
    return chip.tone;
  }
  return "default";
}

export function RecruitingInfraPage() {
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Diagnostics>({});

  const headers = useMemo(
    () => recruitingWorkspaceHeaders(organizationId, recruitingRole),
    [organizationId, recruitingRole],
  );

  const load = useCallback(async () => {
    setError(null);
    const res = await recruitingOpsGet("/ops/diagnostics", headers);
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      setData({});
      return;
    }
    setData(asRecord(res.json));
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const recover = async () => {
    await recruitingOpsPost("/tracking/recover", {}, headers);
    await load();
  };

  const components = data.components || {};
  const tracking = data.tracking || {};

  return (
    <RecruitingOpsFrame
      title="Инфраструктура"
      subtitle="Состояния честные: «Не настроено» не показывается как ошибка."
      testId="recruiting-infra-page"
      error={error}
      onRefresh={() => void load()}
    >
      <div className="grid gap-3" data-testid="recruiting-infra-grid">
        {ROWS.map((row) => {
          const chip = components[row.id] || {};
          const label = chip.label_ru || "Не настроено";
          return (
            <Card key={row.id} title={row.label}>
              <div data-testid={`infra-row-${row.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={toneFor(chip)}>{label}</Badge>
                  {chip.backend ? <span className="eds-type-small">backend={String(chip.backend)}</span> : null}
                  {chip.shared === true ? <span className="eds-type-small">SHARED=YES</span> : null}
                  {chip.shared === false && chip.backend ? <span className="eds-type-small">SHARED=NO</span> : null}
                </div>
                {chip.reason_ru ? <p className="mt-2 eds-type-helper">{chip.reason_ru}</p> : null}
                {chip.missing && chip.missing.length ? (
                  <p className="mt-1 eds-type-small">Не задано: {chip.missing.join(", ")}</p>
                ) : null}
                {chip.required_env ? (
                  <p className="mt-1 eds-type-small">Нужно: {chip.required_env.join(", ")}</p>
                ) : null}
              </div>
            </Card>
          );
        })}
      </div>
      <Card title="Трекинг">
        <dl className="grid grid-cols-2 gap-2 eds-type-small" data-testid="infra-tracking-counts">
          <dt>pending</dt>
          <dd>{displayNum(tracking.pending)}</dd>
          <dt>processing</dt>
          <dd>{displayNum(tracking.processing)}</dd>
          <dt>retrying</dt>
          <dd>{displayNum(tracking.retrying)}</dd>
          <dt>waiting_provider</dt>
          <dd>{displayNum(tracking.waiting_provider)}</dd>
          <dt>delivered</dt>
          <dd>{displayNum(tracking.delivered)}</dd>
          <dt>dead_letter</dt>
          <dd>{displayNum(tracking.dead_letter)}</dd>
          <dt>provider_not_configured</dt>
          <dd>{displayNum(tracking.provider_not_configured)}</dd>
          <dt>oldest_pending</dt>
          <dd>{tracking.oldest_pending || "—"}</dd>
          <dt>last_delivery</dt>
          <dd>{tracking.last_delivery || "—"}</dd>
        </dl>
        <button type="button" className="mt-3 eds-type-small underline" onClick={() => void recover()}>
          Восстановить статусы durable-событий
        </button>
      </Card>
    </RecruitingOpsFrame>
  );
}

function displayNum(value: unknown): string {
  if (value === null || value === undefined || value === "") return "0";
  return String(value);
}
