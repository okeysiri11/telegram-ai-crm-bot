/**
 * Advertising Control Center — overview through AI optimization.
 * Provider metrics stay «Нет живых данных» until a LIVE provider exists.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { asList, recruitingOpsGet, recruitingOpsPost } from "../business-ops/opsApi";
import { mapUiRoleToRecruiting } from "./recruitingLabels";
import { RecruitingOpsFrame } from "./RecruitingOpsFrame";

const SECTIONS = [
  { id: "overview", label: "Обзор" },
  { id: "providers", label: "Провайдеры" },
  { id: "campaigns", label: "Кампании" },
  { id: "leads", label: "Лиды" },
  { id: "funnel", label: "Воронка" },
  { id: "attribution", label: "Атрибуция" },
  { id: "source_analytics", label: "Источники" },
  { id: "automation", label: "Автоматизация" },
  { id: "ai_optimization", label: "AI-оптимизация" },
  { id: "diagnostics", label: "Диагностика" },
] as const;

type Row = Record<string, unknown>;

function asRecord(json: unknown): Row {
  return json && typeof json === "object" ? (json as Row) : {};
}

function liveLabel(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Нет живых данных";
  return String(value);
}

export function AdsControlCenterPage() {
  const [params, setParams] = useSearchParams();
  const section = SECTIONS.some((item) => item.id === params.get("section")) ? String(params.get("section")) : "overview";
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Row>({});
  const [campaignName, setCampaignName] = useState("");
  const [aiType, setAiType] = useState("pause_campaign");

  const headers = useMemo(
    () => ({
      "X-Organization-Id": organizationId,
      "X-Tenant-Id": organizationId,
      "X-Role": recruitingRole,
    }),
    [organizationId, recruitingRole],
  );

  const load = useCallback(async () => {
    setError(null);
    const res = await recruitingOpsGet("/ads/control-center?project=vanguard", headers);
    if (!res.ok) {
      setError("Recruiting Ops API недоступен.");
      setData({});
      return;
    }
    setData(asRecord(res.json));
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const overview = asRecord(data.overview);
  const providers = asRecord(data.providers);
  const campaigns = asList(data.campaigns);
  const funnel = asRecord(data.funnel);
  const attribution = asRecord(data.attribution);
  const sources = asRecord(data.source_analytics);
  const automation = asRecord(data.automation);
  const ai = asRecord(data.ai_optimization);
  const health = asRecord(data.provider_health);

  return (
    <RecruitingOpsFrame
      title="Рекламный центр"
      subtitle="Живые метрики провайдера не выдумываются. AI только советует."
      testId="ads-control-center-page"
      error={error}
      onRefresh={() => void load()}
    >
      <div className="mb-3 flex flex-wrap gap-2" data-testid="ads-sections">
        {SECTIONS.map((item) => (
          <Button
            key={item.id}
            size="sm"
            variant={section === item.id ? "primary" : "secondary"}
            onClick={() => setParams({ section: item.id, embed: params.get("embed") || "" })}
          >
            {item.label}
          </Button>
        ))}
      </div>
      {section === "overview" ? (
        <Card title="Обзор">
          <dl className="grid grid-cols-2 gap-2 eds-type-small" data-testid="ads-overview-metrics">
            <dt>Подключенные провайдеры</dt>
            <dd>{liveLabel(overview.connected_providers)}</dd>
            <dt>Активные кампании</dt>
            <dd>{liveLabel(overview.active_campaigns)}</dd>
            <dt>Расход</dt>
            <dd>{liveLabel(overview.spend)}</dd>
            <dt>Показы</dt>
            <dd>{liveLabel(overview.impressions)}</dd>
            <dt>Клики</dt>
            <dd>{liveLabel(overview.clicks)}</dd>
            <dt>Лиды</dt>
            <dd>{String(overview.leads ?? 0)}</dd>
            <dt>Квалифицированные</dt>
            <dd>{String(overview.qualified_candidates ?? 0)}</dd>
            <dt>Интервью</dt>
            <dd>{String(overview.interviews ?? 0)}</dd>
            <dt>Наймы</dt>
            <dd>{String(overview.hires ?? 0)}</dd>
            <dt>CPL</dt>
            <dd>{liveLabel(overview.cost_per_lead)}</dd>
            <dt>Стоимость квалификации</dt>
            <dd>{liveLabel(overview.cost_per_qualified_candidate)}</dd>
            <dt>Стоимость интервью</dt>
            <dd>{liveLabel(overview.cost_per_interview)}</dd>
            <dt>Стоимость найма</dt>
            <dd>{liveLabel(overview.cost_per_hire)}</dd>
          </dl>
          {overview.no_live_data ? <p className="mt-2 eds-type-helper" data-testid="ads-no-live-data">Нет живых данных</p> : null}
        </Card>
      ) : null}
      {section === "providers" ? (
        <Card title="Провайдеры">
          <p>
            <Link to="/workspace/recruiting/integrations">Открыть подключения</Link>
          </p>
          {Object.entries(providers).map(([key, value]) => {
            const rec = asRecord(value);
            return (
              <div key={key} className="mt-2" data-testid={`ads-provider-${key}`}>
                <Badge tone="info">{key}</Badge> {String(rec.status || rec.readiness || "not_connected")}
              </div>
            );
          })}
        </Card>
      ) : null}
      {section === "campaigns" ? (
        <Card title="Кампании">
          <div className="mb-3 flex gap-2">
            <Input value={campaignName} onChange={(e) => setCampaignName(e.target.value)} placeholder="Название" />
            <Button
              size="sm"
              onClick={async () => {
                if (!campaignName) return;
                await recruitingOpsPost("/campaigns", { name: campaignName, project_key: "vanguard", status: "DRAFT" }, headers);
                setCampaignName("");
                await load();
              }}
            >
              Создать черновик
            </Button>
          </div>
          <ul data-testid="ads-campaign-list">
            {campaigns.map((raw) => {
            const row = asRecord(raw);
            return (
              <li key={String(row.id)}>{String(row.name || row.id)} — {String(row.status || "DRAFT")}</li>
            );
          })}
          </ul>
        </Card>
      ) : null}
      {section === "leads" ? <Card title="Лиды">Лиды нормализуются из провайдера без перезаписи истории.</Card> : null}
      {section === "funnel" ? (
        <Card title="Воронка">
          <ul data-testid="ads-funnel">
            {asList(funnel.steps).map((raw) => {
            const step = asRecord(raw);
            return <li key={String(step.id)}>{String(step.label_ru)}: {String(step.count ?? "—")}</li>;
          })}
          </ul>
        </Card>
      ) : null}
      {section === "attribution" ? (
        <Card title="Атрибуция">
          <p data-testid="ads-attribution-first">First-touch: {String(asRecord(attribution.first_touch).source || "—")}</p>
          <p data-testid="ads-attribution-last">Last-touch: {String(asRecord(attribution.last_touch).source || asRecord(attribution).source || "—")}</p>
        </Card>
      ) : null}
      {section === "source_analytics" ? (
        <Card title="Источники">
          <ul>
            {asList(sources.items).map((raw) => {
            const row = asRecord(raw);
            return <li key={String(row.source)}>{String(row.source)} — лиды {String(row.leads)}</li>;
          })}
          </ul>
        </Card>
      ) : null}
      {section === "automation" ? (
        <Card title="Автоматизация">
          <p data-testid="ads-automation-approval">Новые правила требуют подтверждения.</p>
          <Button
            size="sm"
            onClick={async () => {
              await recruitingOpsPost("/automation/rules", { rule_type: "pause_if_cpl_exceeded", threshold: 50 }, headers);
              await load();
            }}
          >
            Добавить правило CPL
          </Button>
          <ul>
            {asList(automation.items).map((raw) => {
            const row = asRecord(raw);
            return <li key={String(row.id)}>{String(row.name || row.rule_type)} — {row.approval_required ? "нужно подтверждение" : "авто"}</li>;
          })}
          </ul>
        </Card>
      ) : null}
      {section === "ai_optimization" ? (
        <Card title="AI-оптимизация">
          <p data-testid="ads-ai-advisory">Рекомендации только консультативные. AI не меняет live-кампании.</p>
          <div className="flex gap-2">
            <Input value={aiType} onChange={(e) => setAiType(e.target.value)} />
            <Button
              size="sm"
              onClick={async () => {
                await recruitingOpsPost("/ai/recommendations", { recommendation: aiType, reason: "Анализ воронки" }, headers);
                await load();
              }}
            >
              Создать рекомендацию
            </Button>
          </div>
          <ul data-testid="ads-ai-list">
            {asList(ai.items).map((raw) => {
            const row = asRecord(raw);
            return (
              <li key={String(row.id)}>
                {String(row.recommendation)} — {String(row.status)}
                <Button size="sm" variant="secondary" onClick={() => void recruitingOpsPost(`/ai/recommendations/${row.id}/decision`, { decision: "APPROVE" }, headers).then(load)}>
                  Одобрить
                </Button>
                <Button size="sm" variant="ghost" onClick={() => void recruitingOpsPost(`/ai/recommendations/${row.id}/decision`, { decision: "REJECT" }, headers).then(load)}>
                  Отклонить
                </Button>
              </li>
            );
          })}
          </ul>
        </Card>
      ) : null}
      {section === "diagnostics" ? (
        <Card title="Диагностика">
          <p>Провайдеры не роняют ядро инфраструктуры.</p>
          <pre className="eds-type-small whitespace-pre-wrap">{JSON.stringify(health, null, 2)}</pre>
        </Card>
      ) : null}
    </RecruitingOpsFrame>
  );
}
