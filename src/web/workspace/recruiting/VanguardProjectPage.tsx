/**
 * Vanguard Control Center — a Recruiting project, not a separate CRM.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input, Table } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { asList, recruitingOpsFirstError, recruitingOpsGet, recruitingOpsPost, pick } from "./recruitingApi";
import {
  PIPELINE_LABELS,
  PIPELINE_STAGES,
  mapUiRoleToRecruiting,
  recruitingClickLabel,
  recruitingConsentLabel,
  recruitingUtmLabel,
  ruLeadStatus,
} from "./recruitingLabels";
import { RecruitingOpsFrame, displayMetric } from "./RecruitingOpsFrame";
import { RecruitingApplicationDetails } from "./RecruitingApplicationDetails";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "traffic", label: "Трафик" },
  { id: "attribution", label: "Атрибуция" },
  { id: "recruiting", label: "Рекрутинг" },
  { id: "leads", label: "Лиды" },
  { id: "candidates", label: "Кандидаты" },
  { id: "vacancies", label: "Вакансии" },
  { id: "pipeline", label: "Воронка" },
  { id: "campaigns", label: "Кампании" },
  { id: "marketing", label: "Маркетинг" },
  { id: "activity", label: "Активность" },
  { id: "website", label: "Сайт" },
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
  const [adsCenter, setAdsCenter] = useState<Row>({});
  const [campaignForm, setCampaignForm] = useState({
    name: "",
    channel: "Meta",
    source: "vanguard",
    medium: "cpc",
    campaign_code: "",
    landing_url: "/vanguard",
    spend: "",
  });

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
    const [ov, integ, leadRes, candRes, vacRes, campRes, an, ads] = await Promise.all([
      recruitingOpsGet("/projects/vanguard", headers),
      recruitingOpsGet("/projects/vanguard/integration", headers),
      recruitingOpsGet(`/leads?${q}`, headers),
      recruitingOpsGet(`/candidates?${q}`, headers),
      recruitingOpsGet(`/vacancies?${q}`, headers),
      recruitingOpsGet(`/campaigns?${q}`, headers),
      recruitingOpsGet(`/analytics?${q}`, headers),
      recruitingOpsGet("/ads/control-center?project=vanguard", headers),
    ]);
    if (![ov, integ, leadRes].some((x) => x.ok)) {
      setError(recruitingOpsFirstError([ov, integ, leadRes]));
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
    setAdsCenter(asRecord(ads.json));
    setPipeline((candJson.pipeline && typeof candJson.pipeline === "object" ? candJson.pipeline : {}) as Record<string, Row[]>);
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const cards = asRecord(overview.cards);
  const website = asRecord(integration.website);
  const stages = Array.isArray(integration.stages) ? (integration.stages as Row[]) : [];
  const funnel = asRecord(analytics.funnel || overview.funnel);
  const funnelSteps = Array.isArray(funnel.steps) ? (funnel.steps as Row[]) : [];
  const pipelineStages = asRecord(overview.pipeline || analytics.pipeline_stages);
  const traffic = asRecord(overview.traffic);
  const attribution = asRecord(overview.attribution);
  const recruiting = asRecord(overview.recruiting);
  const marketing = asRecord(overview.marketing);
  const diagnostics = asRecord(integration.diagnostics);
  const sourceAnalytics = asRecord(overview.source_analytics || adsCenter.source_analytics);
  const publicUrl = website.public_url ? String(website.public_url) : "";
  const sitePath = website.site_path ? String(website.site_path) : "/vanguard";

  async function act(path: string, body: Record<string, unknown> = {}) {
    await recruitingOpsPost(path, body, headers);
    await load();
  }

  async function checkIntegration() {
    const res = await recruitingOpsPost("/projects/vanguard/integration/check", {}, headers);
    if (res.ok) setIntegration(asRecord(res.json));
    else setError("Проверка интеграции не выполнена.");
  }

  function uiState(value: unknown): string {
    const rec = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
    return displayMetric(rec.ui_state || rec.status_label_ru || rec.label_ru || rec.code);
  }

  function cardValue(value: unknown): string {
    if (value && typeof value === "object") return statusLabel(value);
    return displayMetric(value);
  }

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
      <div data-testid="vanguard-diagnostics">
      <Card title="Интеграция" className="mb-4">
        <dl className="grid grid-cols-1 gap-2 eds-type-small sm:grid-cols-2 md:grid-cols-4">
          <dt>Сайт</dt>
          <dd>{uiState(diagnostics.website || integration.website_status)}</dd>
          <dt>Интеграция</dt>
          <dd>{uiState(diagnostics.integration || integration.integration_status)}</dd>
          <dt>База данных</dt>
          <dd>{uiState(diagnostics.database || integration.database_status)}</dd>
          <dt>Трекинг</dt>
          <dd>{uiState(diagnostics.tracking || integration.tracking_status)}</dd>
          <dt>Последняя заявка</dt>
          <dd>{displayMetric(diagnostics.last_application || cards.last_application_at)}</dd>
          <dt>Последняя синхронизация</dt>
          <dd>{displayMetric(diagnostics.last_synchronization || integration.last_success_at)}</dd>
          <dt>Последняя успешная проверка</dt>
          <dd>{displayMetric(diagnostics.last_successful_health_check || integration.last_successful_check_at)}</dd>
          <dt>Последняя проверка</dt>
          <dd>{displayMetric(diagnostics.last_checked || integration.last_check_at)}</dd>
        </dl>
        {diagnostics.failure_reason ? <p className="mt-2 eds-type-helper">{String(diagnostics.failure_reason)}</p> : null}
        <Button className="mt-3" size="sm" variant="secondary" onClick={() => void checkIntegration()}>
          Проверить интеграцию
        </Button>
      </Card>
      </div>
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
              ["URL сайта", cards.website_url || sitePath],
              ["Здоровье сайта", cards.website_health],
              ["Здоровье интеграции", cards.integration_health],
              ["Последнее успешное соединение", cards.last_successful_connection],
              ["Последняя заявка", cards.last_application_at],
              ["Заявки сегодня", cards.applications_today],
              ["Заявки 7 дней", cards.applications_7d],
              ["Заявки 30 дней", cards.applications_30d],
              ["Лиды", cards.leads],
              ["Кандидаты", cards.candidates],
              ["Конверсия Lead → Candidate", cards.conversion_rate],
            ].map(([label, value]) => (
              <Card key={String(label)} title={String(label)}>
                <p>{cardValue(value)}</p>
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
          <dl className="grid grid-cols-1 gap-2 eds-type-small sm:grid-cols-2">
            <dt>Название сайта</dt>
            <dd>{displayMetric(website.name)}</dd>
            <dt>Публичный URL</dt>
            <dd>{displayMetric(publicUrl || sitePath)}</dd>
            <dt>Окружение</dt>
            <dd>{displayMetric(website.environment)}</dd>
            <dt>Статус сайта</dt>
            <dd>{statusLabel(integration.website_status)}</dd>
            <dt>Последняя проверка</dt>
            <dd>{displayMetric(integration.last_check_at)}</dd>
          </dl>
          <div className="mt-3">
            <Button onClick={() => window.open(publicUrl || sitePath, "_blank", "noopener")}>Открыть сайт</Button>
          </div>
        </Card>
        </div>
      ) : null}

      {tab === "leads" ? (
        <div data-testid="vanguard-leads">
        <Card title="Лиды Vanguard">
          <SimpleTable
            headers={["Имя", "Телефон", "Email", "Возраст", "Согласие", "Источник", "Проект", "Reference", "Программа", "Страна", "UTM", "Клики", "Статус"]}
            rows={leads.map((l) => [
              pick(l, "name"),
              pick(l, "phone"),
              pick(l, "email"),
              pick(l, "age"),
              recruitingConsentLabel(l.contact_consent),
              pick(l, "source"),
              pick(l, "project_key"),
              pick(l, "external_id"),
              pick(l, "program_of_interest", "vacancy", "vacancy_id"),
              pick(l, "country"),
              recruitingUtmLabel(l),
              recruitingClickLabel(l),
              ruLeadStatus(String(l.status || "")),
            ])}
          />
          <RecruitingApplicationDetails row={leads[0]} testId="vanguard-lead-details" />
          {leads[0] ? (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => void act(`/leads/${leads[0].id}/notes`, { notes: "Заметка рекрутера Vanguard" })}>
                Заметка
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void act("/tasks", { title: "Позвонить", lead_id: leads[0].id, project_key: "vanguard" })}>
                Задача
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void act(`/leads/${leads[0].id}/qualify`, {})}>
                Квалифицировать
              </Button>
              <Button size="sm" onClick={() => void act(`/leads/${leads[0].id}/convert`, {})}>
                В кандидаты
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void act("/communications", { channel: "MANUAL", body: "Запись звонка", lead_id: leads[0].id, project_key: "vanguard", sent: false })}>
                Коммуникация
              </Button>
            </div>
          ) : null}
        </Card>
        </div>
      ) : null}

      {tab === "candidates" ? (
        <div data-testid="vanguard-candidates">
        <Card title="Кандидаты Vanguard">
          <SimpleTable
            headers={["Имя", "Телефон", "Email", "Возраст", "Согласие", "Этап", "Источник"]}
            rows={candidates.map((c) => [
              pick(c, "name"),
              pick(c, "phone"),
              pick(c, "email"),
              pick(c, "age"),
              recruitingConsentLabel(c.contact_consent),
              PIPELINE_LABELS[String(c.pipeline_stage || "")] || pick(c, "pipeline_stage"),
              pick(c, "source"),
            ])}
          />
          <RecruitingApplicationDetails row={candidates[0]} testId="vanguard-candidate-details" />
          {candidates.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => void act(`/candidates/${candidates[0].id}/stage`, { pipeline_stage: "INTERVIEW" })}>
                В интервью
              </Button>
            </div>
          ) : null}
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
          <p className="mb-2 eds-type-helper">Кампании ведут трафик на сайт Vanguard. Meta Ads / Google Ads / TikTok Ads: Провайдер не подключен.</p>
          <form
            className="mb-4 grid gap-2 sm:grid-cols-2 md:grid-cols-3"
            data-testid="vanguard-campaign-form"
            onSubmit={(e) => {
              e.preventDefault();
              void act("/campaigns", {
                ...campaignForm,
                project_key: "vanguard",
                spend: campaignForm.spend ? Number(campaignForm.spend) : null,
              });
            }}
          >
            <Input placeholder="Название" value={campaignForm.name} onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })} />
            <Input placeholder="Код кампании" value={campaignForm.campaign_code} onChange={(e) => setCampaignForm({ ...campaignForm, campaign_code: e.target.value })} />
            <Input placeholder="Источник" value={campaignForm.source} onChange={(e) => setCampaignForm({ ...campaignForm, source: e.target.value })} />
            <Input placeholder="Канал" value={campaignForm.medium} onChange={(e) => setCampaignForm({ ...campaignForm, medium: e.target.value })} />
            <Input placeholder="Посадочная страница" value={campaignForm.landing_url} onChange={(e) => setCampaignForm({ ...campaignForm, landing_url: e.target.value })} />
            <Input placeholder="Расход" value={campaignForm.spend} onChange={(e) => setCampaignForm({ ...campaignForm, spend: e.target.value })} />
            <Button type="submit">Сохранить кампанию</Button>
          </form>
          <SimpleTable
            headers={["Кампания", "Канал", "Источник", "Код", "Статус", "Расход", "Лиды", "Стоимость лида"]}
            rows={(asList(marketing.campaigns).length ? (marketing.campaigns as Row[]) : campaigns).map((c) => [
              pick(c, "name"),
              pick(c, "channel"),
              pick(c, "source"),
              pick(c, "campaign_code"),
              pick(c, "status"),
              displayMetric(c.spend),
              displayMetric(c.leads),
              displayMetric(c.cpl),
            ])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "traffic" ? (
        <div data-testid="vanguard-traffic">
          <Card title="Трафик">
            <dl className="grid grid-cols-2 gap-2 eds-type-small">
              <dt>Визиты</dt>
              <dd>{displayMetric(traffic.visits)}</dd>
              <dt>Уникальные посетители</dt>
              <dd>{displayMetric(traffic.unique_visitors)}</dd>
              <dt>Сессии</dt>
              <dd>{displayMetric(traffic.sessions)}</dd>
              <dt>Открытие заявки</dt>
              <dd>{displayMetric(traffic.application_opens)}</dd>
              <dt>Старт заявки</dt>
              <dd>{displayMetric(traffic.application_starts)}</dd>
              <dt>Завершённые заявки</dt>
              <dd>{displayMetric(traffic.completed_applications)}</dd>
            </dl>
          </Card>
        </div>
      ) : null}

      {tab === "attribution" ? (
        <div data-testid="vanguard-attribution">
          <Card title="Атрибуция">
            <dl className="grid grid-cols-1 gap-2 eds-type-small sm:grid-cols-2">
              <dt>Источник</dt>
              <dd>{displayMetric(attribution.source)}</dd>
              <dt>Канал</dt>
              <dd>{displayMetric(attribution.medium)}</dd>
              <dt>Кампания</dt>
              <dd>{displayMetric(attribution.campaign)}</dd>
              <dt>Контент</dt>
              <dd>{displayMetric(attribution.content)}</dd>
              <dt>Источник перехода</dt>
              <dd>{displayMetric(attribution.referrer)}</dd>
              <dt>Посадочная страница</dt>
              <dd>{displayMetric(attribution.landing_page)}</dd>
              <dt>Первый контакт</dt>
              <dd>{displayMetric(asRecord(attribution.first_touch).source)}</dd>
              <dt>Последний контакт</dt>
              <dd>{displayMetric(asRecord(attribution.last_touch).source)}</dd>
              <dt>utm_source</dt>
              <dd>{displayMetric(asRecord(attribution.utm).utm_source)}</dd>
              <dt>utm_medium</dt>
              <dd>{displayMetric(asRecord(attribution.utm).utm_medium)}</dd>
              <dt>utm_campaign</dt>
              <dd>{displayMetric(asRecord(attribution.utm).utm_campaign)}</dd>
              <dt>utm_content</dt>
              <dd>{displayMetric(asRecord(attribution.utm).utm_content)}</dd>
              <dt>utm_term</dt>
              <dd>{displayMetric(asRecord(attribution.utm).utm_term)}</dd>
            </dl>
            <p className="mt-3 eds-type-caption">Аналитика по источнику</p>
            <SimpleTable
              headers={["Источник", "Лиды", "Кандидаты", "Конверсия"]}
              rows={(asList(sourceAnalytics.items || attribution.by_source) as Row[]).map((row) => [
                pick(row, "source"),
                displayMetric(row.leads ?? row.count),
                displayMetric(row.candidates),
                row.conversion != null ? `${Math.round(Number(row.conversion) * 100)}%` : "Нет данных",
              ])}
            />
          </Card>
        </div>
      ) : null}

      {tab === "recruiting" ? (
        <div data-testid="vanguard-recruiting">
          <Card title="Рекрутинг">
            <dl className="grid grid-cols-2 gap-2 eds-type-small">
              <dt>Новые лиды</dt>
              <dd>{displayMetric(recruiting.new_leads)}</dd>
              <dt>Квалифицированы</dt>
              <dd>{displayMetric(recruiting.qualified_leads)}</dd>
              <dt>Кандидаты</dt>
              <dd>{displayMetric(recruiting.candidates)}</dd>
              <dt>Интервью</dt>
              <dd>{displayMetric(recruiting.interviews)}</dd>
              <dt>Приняты</dt>
              <dd>{displayMetric(recruiting.accepted)}</dd>
              <dt>Отказ</dt>
              <dd>{displayMetric(recruiting.rejected)}</dd>
            </dl>
          </Card>
        </div>
      ) : null}

      {tab === "marketing" || tab === "analytics" ? (
        <div data-testid="vanguard-analytics">
        <Card title="Маркетинговая воронка">
          {funnelSteps.length ? (
            <ol className="eds-type-small">
              {funnelSteps.map((step) => (
                <li key={String(step.id)}>
                  {String(step.label_ru)}: {displayMetric(step.count)}
                  {step.conversion != null ? ` (${Math.round(Number(step.conversion) * 100)}%)` : ""}
                </li>
              ))}
            </ol>
          ) : (
            <p>Нет данных</p>
          )}
          <p className="mt-2 eds-type-helper">CPL показывается только если указан spend. Рекламные API не подключены.</p>
          <p className="mt-3 eds-type-caption">Конверсия по кампании</p>
          <SimpleTable
            headers={["Кампания", "Лиды", "Кандидаты", "Конверсия", "CPL"]}
            rows={(asList(marketing.campaigns) as Row[]).map((c) => [
              pick(c, "name"),
              displayMetric(c.leads),
              displayMetric(c.candidates),
              c.conversion != null ? `${Math.round(Number(c.conversion) * 100)}%` : "Нет данных",
              displayMetric(c.cpl),
            ])}
          />
        </Card>
        </div>
      ) : null}

      {tab === "activity" ? (
        <div data-testid="vanguard-activity">
          <Card title="Последние заявки">
            <SimpleTable
              headers={["Имя", "Reference", "Когда"]}
              rows={(asList(overview.recent_leads) as Row[]).map((a) => [pick(a, "name"), pick(a, "external_id"), pick(a, "submitted_at", "created_at")])}
            />
          </Card>
          <Card title="Коммуникации" className="mt-3">
            <SimpleTable
              headers={["Канал", "Запись", "Доставка"]}
              rows={(asList(overview.recent_communications) as Row[]).map((a) => [
                pick(a, "channel"),
                pick(a, "body"),
                a.sent === true ? "отправлено" : "только журнал",
              ])}
            />
          </Card>
          <Card title="Действия рекрутера" className="mt-3">
            <SimpleTable
              headers={["Действие", "Описание"]}
              rows={(asList(overview.recent_activity) as Row[])
                .filter((a) => !String(a.action || "").includes("ingest") && !String(a.action || "").includes("integration"))
                .map((a) => [pick(a, "action"), pick(a, "summary")])}
            />
          </Card>
          <Card title="События интеграции" className="mt-3">
            <SimpleTable
              headers={["Действие", "Описание"]}
              rows={(asList(overview.recent_activity) as Row[])
                .filter((a) => String(a.action || "").includes("ingest") || String(a.action || "").includes("vanguard"))
                .map((a) => [pick(a, "action"), pick(a, "summary")])}
            />
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
                {stage.reason_ru ? ` — ${String(stage.reason_ru)}` : ""}
                {index < stages.length - 1 ? <span className="block pl-3">↓</span> : null}
              </li>
            ))}
          </ol>
          <p>Сайт и интеграция независимы. Интеграция не включает статус сайта.</p>
          <p>Последняя успешная заявка: {displayMetric(integration.last_success_at)}</p>
          <p>
            Последняя ошибка:{" "}
            {integration.last_error
              ? displayMetric(asRecord(integration.last_error).message_ru || asRecord(integration.last_error).error)
              : "Нет данных"}
          </p>
          <p>Последняя проверка: {displayMetric(integration.last_check_at)}</p>
          <Button className="mt-3" variant="secondary" onClick={() => void checkIntegration()}>
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
