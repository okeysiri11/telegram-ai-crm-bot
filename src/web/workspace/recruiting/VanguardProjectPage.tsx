/**
 * Vanguard Control Center — a Recruiting project, not a separate CRM.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Table } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { asList, recruitingOpsGet, pick } from "../business-ops/opsApi";
import { PIPELINE_LABELS, PIPELINE_STAGES, mapUiRoleToRecruiting, ruLeadStatus } from "./recruitingLabels";
import { RecruitingOpsFrame, displayMetric } from "./RecruitingOpsFrame";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "website", label: "Сайт" },
  { id: "leads", label: "Лиды" },
  { id: "candidates", label: "Кандидаты" },
  { id: "vacancies", label: "Вакансии" },
  { id: "pipeline", label: "Воронка" },
  { id: "campaigns", label: "Кампании" },
  { id: "analytics", label: "Аналитика" },
  { id: "integration", label: "Интеграция" },
] as const;

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

function SimpleTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  if (!rows.length) return <p>Нет данных</p>;
  return (
    <Table headers={headers}>
      {rows.map((row, i) => (
        <tr key={row[0] || String(i)}>
          {row.map((cell, j) => (
            <td key={`${i}-${j}`}>{cell}</td>
          ))}
        </tr>
      ))}
    </Table>
  );
}

function statusLabel(value: unknown): string {
  const rec = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return displayMetric(rec.status_label_ru || rec.label_ru || rec.code);
}

export function VanguardProjectPage() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some((item) => item.id === params.get("tab")) ? String(params.get("tab")) : "overview";
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<Row>({});
  const [integration, setIntegration] = useState<Row>({});
  const [leads, setLeads] = useState<Row[]>([]);
  const [candidates, setCandidates] = useState<Row[]>([]);
  const [vacancies, setVacancies] = useState<Row[]>([]);
  const [campaigns, setCampaigns] = useState<Row[]>([]);
  const [analytics, setAnalytics] = useState<Row>({});
  const [pipeline, setPipeline] = useState<Record<string, Row[]>>({});
  const [lookupHit, setLookupHit] = useState<Row | null>(null);

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
    const q = "project=vanguard";
    const [ov, integ, leadRes, candRes, vacRes, campRes, an, lookup] = await Promise.all([
      recruitingOpsGet("/projects/vanguard", headers),
      recruitingOpsGet("/projects/vanguard/integration", headers),
      recruitingOpsGet(`/leads?${q}`, headers),
      recruitingOpsGet(`/candidates?${q}`, headers),
      recruitingOpsGet(`/vacancies?${q}`, headers),
      recruitingOpsGet(`/campaigns?${q}`, headers),
      recruitingOpsGet(`/analytics?${q}`, headers),
      recruitingOpsGet("/lookup?q=VG-ZT9TH2", headers),
    ]);
    if (![ov, integ, leadRes].some((x) => x.ok)) {
      setError("Recruiting Ops API недоступен. Запустите backend (:8080).");
      return;
    }
    const candJson = asRecord(candRes.json);
    setOverview(asRecord(ov.json));
    setIntegration(asRecord(integ.json));
    setLeads(asList(leadRes.json) as Row[]);
    setCandidates(asList(candRes.json) as Row[]);
    setVacancies(asList(vacRes.json) as Row[]);
    setCampaigns(asList(campRes.json) as Row[]);
    setAnalytics(asRecord(an.json));
    setPipeline((candJson.pipeline && typeof candJson.pipeline === "object" ? candJson.pipeline : {}) as Record<string, Row[]>);
    const found = asList(asRecord(lookup.json).items) as Row[];
    setLookupHit(found[0] || null);
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const cards = asRecord(overview.cards);
  const website = asRecord(integration.website);
  const stages = Array.isArray(integration.stages) ? (integration.stages as Row[]) : [];
  const funnel = asRecord(analytics.funnel || overview.funnel);
  const pipelineStages = asRecord(overview.pipeline || analytics.pipeline_stages);
  const publicUrl = website.public_url ? String(website.public_url) : "";

  return (
    <RecruitingOpsFrame
      title="VANGUARD"
      subtitle="Recruiting Project — сайт отправляет заявки в Рекрутинг"
      testId="vanguard-project-page"
      error={error}
      onRefresh={() => void load()}
      headerExtra={
        <Badge>{statusLabel(integration.overall || integration.integration_status)}</Badge>
      }
    >
      <p className="mb-4 eds-type-helper" data-testid="vanguard-relationship">
        Сайт Vanguard → Рекрутинг → Лиды → Кандидаты
      </p>
      <nav className="mb-4 flex flex-wrap gap-1" aria-label="Разделы Vanguard" data-testid="vanguard-tabs">
        {TABS.map((item) => (
          <Button
            key={item.id}
            size="sm"
            variant={tab === item.id ? "primary" : "secondary"}
            onClick={() => {
              const next = new URLSearchParams(params);
              if (item.id === "overview") next.delete("tab");
              else next.set("tab", item.id);
              setParams(next);
            }}
          >
            {item.label}
          </Button>
        ))}
      </nav>

      {tab === "overview" ? (
        <div className="grid gap-3" data-testid="vanguard-overview">
          <div className="grid gap-3 md:grid-cols-3">
            {[
              ["Новые лиды", cards.new_leads],
              ["Кандидаты", cards.candidates],
              ["Активные вакансии", cards.active_vacancies],
              ["Заявки сегодня", cards.applications_today],
              ["Конверсия Lead → Candidate", cards.lead_to_candidate],
              ["Последняя заявка", cards.last_application_at],
            ].map(([label, value]) => (
              <Card key={String(label)} title={String(label)}>
                <p>{displayMetric(value)}</p>
              </Card>
            ))}
          </div>
          <Card title="Последние заявки">
            <SimpleTable
              headers={["Имя", "Reference", "Статус"]}
              rows={leads.slice(0, 8).map((l) => [pick(l, "name"), pick(l, "external_id"), ruLeadStatus(String(l.status || ""))])}
            />
          </Card>
          <Card title="Воронка Vanguard">
            <div className="flex flex-wrap gap-3">
              {PIPELINE_STAGES.map((stage) => (
                <div key={stage}>
                  <p className="eds-type-caption">{PIPELINE_LABELS[stage]}</p>
                  <p>{displayMetric(pipelineStages[stage] ?? (pipeline[stage] || []).length)}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      ) : null}

      {tab === "website" ? (
        <div data-testid="vanguard-website-card">
        <Card title="Сайт Vanguard">
          <dl className="grid grid-cols-2 gap-2 eds-type-small">
            <dt>Website name</dt>
            <dd>{displayMetric(website.name)}</dd>
            <dt>Public URL</dt>
            <dd>{displayMetric(publicUrl)}</dd>
            <dt>Environment</dt>
            <dd>{displayMetric(website.environment)}</dd>
            <dt>Website status</dt>
            <dd>{statusLabel(integration.website_status)}</dd>
            <dt>Last health check</dt>
            <dd>{displayMetric(integration.last_check_at)}</dd>
          </dl>
          <div className="mt-3">
            {publicUrl ? (
              <Button onClick={() => window.open(publicUrl, "_blank", "noopener")}>Открыть сайт</Button>
            ) : (
              <Button disabled>Открыть сайт</Button>
            )}
          </div>
        </Card>
        </div>
      ) : null}

      {tab === "leads" ? (
        <div data-testid="vanguard-leads">
        <Card title="Лиды Vanguard">
          {lookupHit ? (
            <p className="mb-2 eds-type-helper" data-testid="vanguard-ref-hit">
              Найден reference {pick(lookupHit, "external_id")} — {pick(lookupHit, "name")}
            </p>
          ) : (
            <p className="mb-2 eds-type-helper" data-testid="vanguard-ref-miss">
              VG-ZT9TH2 в Рекрутинге не найден
            </p>
          )}
          <SimpleTable
            headers={["Имя", "Источник", "Проект", "Reference", "Вакансия", "UTM", "Статус"]}
            rows={leads.map((l) => [
              pick(l, "name"),
              pick(l, "source"),
              pick(l, "project_key"),
              pick(l, "external_id"),
              pick(l, "vacancy_id", "vacancy"),
              [pick(l, "utm_source"), pick(l, "utm_medium"), pick(l, "utm_campaign")].filter((x) => x && x !== "—").join(" / ") || "—",
              ruLeadStatus(String(l.status || "")),
            ])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "candidates" ? (
        <div data-testid="vanguard-candidates">
        <Card title="Кандидаты Vanguard">
          <SimpleTable
            headers={["Имя", "Этап", "Источник"]}
            rows={candidates.map((c) => [
              pick(c, "name"),
              PIPELINE_LABELS[String(c.pipeline_stage || "")] || pick(c, "pipeline_stage"),
              pick(c, "source"),
            ])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "vacancies" ? (
        <div data-testid="vanguard-vacancies">
        <Card title="Вакансии Vanguard">
          <SimpleTable
            headers={["Вакансия", "Статус"]}
            rows={vacancies.map((v) => [pick(v, "title", "name"), pick(v, "status")])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "pipeline" ? (
        <div data-testid="vanguard-pipeline">
        <Card title="Воронка Vanguard">
          <div className="grid gap-3 md:grid-cols-3">
            {PIPELINE_STAGES.map((stage) => (
              <div key={stage}>
                <p className="eds-type-caption">{PIPELINE_LABELS[stage]}</p>
                {(pipeline[stage] || []).length ? (
                  (pipeline[stage] || []).map((c) => <p key={String(c.id)}>{pick(c, "name")}</p>)
                ) : (
                  <p>Нет данных</p>
                )}
              </div>
            ))}
          </div>
        </Card>
        </div>
      ) : null}

      {tab === "campaigns" ? (
        <div data-testid="vanguard-campaigns">
        <Card title="Кампании Vanguard">
          <p className="mb-2 eds-type-helper">Кампании ведут трафик на сайт Vanguard. Рекламные API не подключены.</p>
          <SimpleTable
            headers={["Кампания", "Источник", "Статус"]}
            rows={campaigns.map((c) => [pick(c, "name"), pick(c, "source"), pick(c, "status")])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "analytics" ? (
        <div data-testid="vanguard-analytics">
        <Card title="Аналитика Vanguard">
          <dl className="grid grid-cols-2 gap-2 eds-type-small">
            <dt>Лиды</dt>
            <dd>{displayMetric(funnel.leads)}</dd>
            <dt>Квалифицированы</dt>
            <dd>{displayMetric(funnel.qualified)}</dd>
            <dt>Интервью</dt>
            <dd>{displayMetric(funnel.interviews)}</dd>
            <dt>Наняты</dt>
            <dd>{displayMetric(funnel.hired)}</dd>
            <dt>Посещения</dt>
            <dd>Нет данных</dd>
          </dl>
        </Card>
        </div>
      ) : null}

      {tab === "integration" ? (
        <div data-testid="vanguard-integration">
        <Card title="Статус интеграции">
          <ol className="mb-3 eds-type-small">
            {stages.map((stage, index) => (
              <li key={String(stage.id)}>
                {String(stage.label_ru || stage.id)}: {displayMetric(stage.status_label_ru || stage.code)}
                {index < stages.length - 1 ? <span className="block pl-3">↓</span> : null}
              </li>
            ))}
          </ol>
          <p>Последняя успешная заявка: {displayMetric(integration.last_success_at)}</p>
          <p>
            Последняя ошибка:{" "}
            {integration.last_error
              ? displayMetric(asRecord(integration.last_error).message_ru || asRecord(integration.last_error).error)
              : "Нет данных"}
          </p>
          <p>Последняя проверка: {displayMetric(integration.last_check_at)}</p>
          <Button className="mt-3" variant="secondary" onClick={() => void load()}>
            Проверить интеграцию
          </Button>
        </Card>
        </div>
      ) : null}

      <p className="mt-4 eds-type-caption">
        <Link to="/workspace/recruiting">Назад в Рекрутинг</Link>
      </p>
    </RecruitingOpsFrame>
  );
}
