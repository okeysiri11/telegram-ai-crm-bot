/**
 * Advertising Control Center — Vanguard campaign economics.
 * Provider impressions/clicks stay «Нет живых данных» until a LIVE provider exists.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input, Table } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { asList, recruitingOpsGet, recruitingOpsPost, recruitingOpsUserError, recruitingWorkspaceHeaders } from "./recruitingApi";
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

const DATE_PRESETS = [
  { id: "today", label: "Сегодня" },
  { id: "7d", label: "7 дней" },
  { id: "30d", label: "30 дней" },
  { id: "this_month", label: "Этот месяц" },
  { id: "last_month", label: "Прошлый месяц" },
  { id: "custom", label: "Период" },
] as const;

const SOURCES = [
  { id: "instagram", label: "Instagram" },
  { id: "facebook", label: "Facebook" },
  { id: "meta", label: "Meta" },
  { id: "google", label: "Google" },
  { id: "tiktok", label: "TikTok" },
  { id: "organic", label: "Organic" },
  { id: "direct", label: "Direct" },
  { id: "referral", label: "Referral" },
  { id: "other", label: "Other" },
] as const;

type Row = Record<string, unknown>;

function asRecord(json: unknown): Row {
  return json && typeof json === "object" ? (json as Row) : {};
}

function liveLabel(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Нет живых данных";
  return String(value);
}

function metricLabel(value: unknown, empty = "Нет данных"): string {
  if (value === null || value === undefined || value === "") return empty;
  return String(value);
}

function pctLabel(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Нет данных";
  const n = Number(value);
  if (!Number.isFinite(n)) return "Нет данных";
  return `${(n * 100).toFixed(1)}%`;
}

export function AdsControlCenterPage() {
  const [params, setParams] = useSearchParams();
  const section = SECTIONS.some((item) => item.id === params.get("section")) ? String(params.get("section")) : "overview";
  const range = DATE_PRESETS.some((item) => item.id === params.get("range")) ? String(params.get("range")) : "30d";
  const customFrom = params.get("from") || "";
  const customTo = params.get("to") || "";
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Row>({});
  const [campaignName, setCampaignName] = useState("");
  const [aiType, setAiType] = useState("pause_campaign");
  const [form, setForm] = useState({
    name: "",
    source: "instagram",
    country: "EE",
    program: "logistics",
    utm_source: "instagram",
    utm_medium: "paid_social",
    utm_campaign: "",
    utm_content: "",
    utm_term: "",
    start_date: "",
    end_date: "",
    planned_budget: "",
    comment: "",
  });
  const [detail, setDetail] = useState<Row | null>(null);
  const [spendForm, setSpendForm] = useState({ amount: "", currency: "EUR", spent_on: "", comment: "" });
  const [connectHint, setConnectHint] = useState<string | null>(null);

  const headers = useMemo(
    () => recruitingWorkspaceHeaders(organizationId, recruitingRole),
    [organizationId, recruitingRole],
  );

  const query = useMemo(() => {
    const q = new URLSearchParams({ project: "vanguard", range });
    if (range === "custom") {
      if (customFrom) q.set("from", customFrom);
      if (customTo) q.set("to", customTo);
    }
    return q.toString();
  }, [range, customFrom, customTo]);

  const load = useCallback(async () => {
    setError(null);
    const res = await recruitingOpsGet(`/ads/control-center?${query}`, headers);
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      setData({});
      return;
    }
    setData(asRecord(res.json));
  }, [headers, query]);

  useEffect(() => {
    void load();
  }, [load]);

  const overview = asRecord(data.overview);
  const kpis = asRecord(data.kpis);
  const providers = asRecord(data.providers);
  const campaigns = asList(data.campaigns);
  const funnel = asRecord(data.funnel);
  const attribution = asRecord(data.attribution);
  const sources = asRecord(data.source_analytics);
  const sourceEconomics = asList(data.source_economics);
  const automation = asRecord(data.automation);
  const ai = asRecord(data.ai_optimization);
  const writes = asRecord(data.campaign_writes);
  const messages = asRecord(data.outbound_messages);
  const health = asRecord(data.provider_health);
  const connect = asList(data.provider_connect);

  function setRange(next: string) {
    const copy = new URLSearchParams(params);
    copy.set("range", next);
    if (next !== "custom") {
      copy.delete("from");
      copy.delete("to");
    }
    setParams(copy);
  }

  async function openDetail(id: string) {
    const res = await recruitingOpsGet(`/campaigns/${id}?${query}`, headers);
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      return;
    }
    setDetail(asRecord(res.json));
  }

  async function createInternalCampaign() {
    const name = form.name || campaignName;
    if (!name) return;
    const res = await recruitingOpsPost(
      "/campaigns",
      {
        name,
        source: form.source,
        country: form.country,
        program: form.program,
        utm_source: form.utm_source || form.source,
        utm_medium: form.utm_medium,
        utm_campaign: form.utm_campaign || name,
        utm_content: form.utm_content,
        utm_term: form.utm_term,
        start_date: form.start_date,
        end_date: form.end_date,
        planned_budget: form.planned_budget ? Number(form.planned_budget) : undefined,
        budget: form.planned_budget ? Number(form.planned_budget) : undefined,
        comment: form.comment,
        project_key: "vanguard",
        status: "ACTIVE",
        origin: "INTERNAL",
      },
      headers,
    );
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      return;
    }
    setCampaignName("");
    setForm((prev) => ({ ...prev, name: "", utm_campaign: "", comment: "" }));
    await load();
    const created = asRecord(asRecord(res.json).item);
    if (created.id) await openDetail(String(created.id));
  }

  async function addSpend() {
    const campaign = asRecord(detail?.campaign || detail?.item);
    if (!campaign.id || !spendForm.amount) return;
    const res = await recruitingOpsPost(
      `/campaigns/${campaign.id}/spend`,
      {
        amount: Number(spendForm.amount),
        currency: spendForm.currency,
        spent_on: spendForm.spent_on,
        comment: spendForm.comment,
      },
      headers,
    );
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      return;
    }
    setSpendForm({ amount: "", currency: spendForm.currency, spent_on: "", comment: "" });
    await load();
    await openDetail(String(campaign.id));
  }

  async function tryConnect(provider: string) {
    const res = await recruitingOpsGet(`/providers/${provider}/oauth/start`, headers);
    const body = asRecord(res.json);
    setConnectHint(String(body.message_ru || "Провайдер не настроен. OAuth не запускается без учётных данных."));
  }

  const kpiCards = [
    { label: "Расход", value: liveLabel(kpis.spend ?? overview.spend), testId: "ads-kpi-spend" },
    { label: "Заявки", value: String(kpis.applications ?? overview.applications ?? overview.leads ?? 0), testId: "ads-kpi-applications" },
    { label: "Стоимость заявки", value: liveLabel(kpis.cpl ?? overview.cost_per_lead), testId: "ads-kpi-cpl" },
    { label: "Квалифицированы", value: String(kpis.qualified ?? overview.qualified_candidates ?? 0), testId: "ads-kpi-qualified" },
    { label: "Интервью", value: String(kpis.interviews ?? overview.interviews ?? 0), testId: "ads-kpi-interviews" },
    { label: "Одобрены", value: String(kpis.approved ?? overview.approved ?? 0), testId: "ads-kpi-approved" },
    { label: "Наняты", value: String(kpis.hired ?? overview.hires ?? 0), testId: "ads-kpi-hired" },
    { label: "Стоимость найма", value: liveLabel(kpis.cost_per_hire ?? overview.cost_per_hire), testId: "ads-kpi-cph" },
  ];

  return (
    <RecruitingOpsFrame
      title="РЕКЛАМА VANGUARD"
      subtitle="Внутренняя экономика рекрутинга. Кабинет Meta/Google/TikTok не подключён."
      testId="ads-control-center-page"
      error={error}
      onRefresh={() => void load()}
    >
      <p className="mb-3 eds-type-helper" data-testid="ads-internal-note">
        Внутренняя кампания — рекламный кабинет не подключён.
      </p>
      <div className="mb-3 flex flex-wrap gap-2" data-testid="ads-date-filters">
        {DATE_PRESETS.map((item) => (
          <Button key={item.id} size="sm" variant={range === item.id ? "primary" : "secondary"} onClick={() => setRange(item.id)}>
            {item.label}
          </Button>
        ))}
        {range === "custom" ? (
          <>
            <Input type="date" value={customFrom} onChange={(e) => setParams((prev) => { const n = new URLSearchParams(prev); n.set("from", e.target.value); return n; })} />
            <Input type="date" value={customTo} onChange={(e) => setParams((prev) => { const n = new URLSearchParams(prev); n.set("to", e.target.value); return n; })} />
          </>
        ) : null}
      </div>
      <div className="mb-3 flex flex-wrap gap-2" data-testid="ads-sections">
        {SECTIONS.map((item) => (
          <Button
            key={item.id}
            size="sm"
            variant={section === item.id ? "primary" : "secondary"}
            onClick={() => {
              const next = new URLSearchParams(params);
              next.set("section", item.id);
              setParams(next);
            }}
          >
            {item.label}
          </Button>
        ))}
      </div>
      {section === "overview" ? (
        <Card title="Обзор">
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="ads-kpi-cards">
            {kpiCards.map((card) => (
              <div key={card.label} data-testid={card.testId}>
                <p className="eds-type-helper">{card.label}</p>
                <p className="eds-type-title text-xl">{card.value}</p>
              </div>
            ))}
          </div>
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
          <p className="mt-2 eds-type-helper" data-testid="ads-data-sources">
            Источники: расход {String(asRecord(overview.data_source).spend || "UNAVAILABLE")}, лиды INTERNAL, CPL {String(asRecord(overview.data_source).cost_per_lead || "UNAVAILABLE")}
          </p>
          <p className="mt-2 eds-type-helper" data-testid="ads-test-exclusion">
            TEST-трафик исключён из экономики. Исключено заявок: {String(asRecord(data.traffic).excluded_test_leads ?? 0)}
          </p>
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
          <div className="mt-4 space-y-3" data-testid="ads-provider-connect">
            {connect.map((raw) => {
              const row = asRecord(raw);
              return (
                <div key={String(row.provider)} data-testid={`ads-connect-${row.provider}`}>
                  <p>
                    <Badge tone="info">{String(row.status || "NOT_CONFIGURED")}</Badge> {String(row.label)}
                  </p>
                  <Button size="sm" className="mt-1" variant="secondary" onClick={() => void tryConnect(String(row.provider))}>
                    {String(row.button_ru || `Подключить ${row.label}`)}
                  </Button>
                </div>
              );
            })}
          </div>
          {connectHint ? <p className="mt-3 eds-type-helper" data-testid="ads-connect-hint">{connectHint}</p> : null}
        </Card>
      ) : null}
      {section === "campaigns" ? (
        <Card title="Кампании">
          <p className="mb-3 eds-type-helper">Внутренняя кампания — рекламный кабинет не подключён.</p>
          <div className="mb-4 grid gap-2 md:grid-cols-2" data-testid="ads-campaign-form">
            <Input value={form.name || campaignName} onChange={(e) => { setForm({ ...form, name: e.target.value }); setCampaignName(e.target.value); }} placeholder="Название кампании" />
            <select className="eds-input" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value, utm_source: e.target.value })} data-testid="ads-campaign-source">
              {SOURCES.map((item) => (
                <option key={item.id} value={item.id}>{item.label}</option>
              ))}
            </select>
            <Input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} placeholder="Страна" />
            <Input value={form.program} onChange={(e) => setForm({ ...form, program: e.target.value })} placeholder="Программа" />
            <Input value={form.utm_source} onChange={(e) => setForm({ ...form, utm_source: e.target.value })} placeholder="UTM source" />
            <Input value={form.utm_medium} onChange={(e) => setForm({ ...form, utm_medium: e.target.value })} placeholder="UTM medium" />
            <Input value={form.utm_campaign} onChange={(e) => setForm({ ...form, utm_campaign: e.target.value })} placeholder="UTM campaign" />
            <Input value={form.utm_content} onChange={(e) => setForm({ ...form, utm_content: e.target.value })} placeholder="UTM content" />
            <Input value={form.utm_term} onChange={(e) => setForm({ ...form, utm_term: e.target.value })} placeholder="UTM term" />
            <Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
            <Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
            <Input value={form.planned_budget} onChange={(e) => setForm({ ...form, planned_budget: e.target.value })} placeholder="Плановый бюджет" />
            <Input value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} placeholder="Комментарий" />
            <Button size="sm" onClick={() => void createInternalCampaign()}>Создать внутреннюю кампанию</Button>
          </div>
          <Table
            headers={["Кампания", "Источник", "Статус", "UTM Source", "UTM Medium", "UTM Campaign", "Расход", "Заявки", "CPL", "Квалифицированы", "Интервью", "Одобрены", "Наняты", "Стоимость найма", "Конверсия"]}
          >
            {campaigns.map((raw) => {
              const row = asRecord(raw);
              return (
                <tr key={String(row.id)} data-testid={`ads-campaign-row-${row.id}`} onClick={() => void openDetail(String(row.id))} className="cursor-pointer">
                  <td>{String(row.name || row.id)}</td>
                  <td>
                    {String(row.source_label_ru || row.source || "—")}
                    {row.provider_backed ? <span className="ml-1 eds-type-helper">НЕ ПОДКЛЮЧЕНО</span> : null}
                  </td>
                  <td>{String(row.status_label_ru || row.status || "DRAFT")}</td>
                  <td>{String(row.utm_source || asRecord(row.utm).source || "—")}</td>
                  <td>{String(row.utm_medium || asRecord(row.utm).medium || "—")}</td>
                  <td>{String(row.utm_campaign || asRecord(row.utm).campaign || row.campaign_code || "—")}</td>
                  <td>{metricLabel(row.spend)}</td>
                  <td>{String(row.applications ?? 0)}</td>
                  <td>{metricLabel(row.cpl)}</td>
                  <td>{String(row.qualified ?? 0)}</td>
                  <td>{String(row.interviews ?? 0)}</td>
                  <td>{String(row.approved ?? 0)}</td>
                  <td>{String(row.hired ?? 0)}</td>
                  <td>{metricLabel(row.cost_per_hire)}</td>
                  <td>{pctLabel(row.conversion)}</td>
                </tr>
              );
            })}
          </Table>
          <ul className="sr-only" data-testid="ads-campaign-list">
            {campaigns.map((raw) => {
              const row = asRecord(raw);
              return <li key={String(row.id)}>{String(row.name || row.id)} — {String(row.status || "DRAFT")}</li>;
            })}
          </ul>
          {detail ? (
            <div className="mt-6" data-testid="ads-campaign-detail">
              <h3 className="eds-type-title">{String(asRecord(detail.campaign || detail.item).name || "Кампания")}</h3>
              <p className="eds-type-helper">{String(detail.origin_label_ru || "Внутренняя кампания — рекламный кабинет не подключён.")}</p>
              <ol className="mt-3 space-y-2" data-testid="ads-campaign-funnel">
                {asList(asRecord(detail.funnel).steps).map((raw) => {
                  const step = asRecord(raw);
                  return (
                    <li key={String(step.id)}>
                      {String(step.label_ru)}: {metricLabel(step.count)} · от предыдущего {pctLabel(step.conversion_from_previous)} · общая {pctLabel(step.conversion_overall)}
                    </li>
                  );
                })}
              </ol>
              <Table headers={["Рекрутер", "Назначено", "Квалифицированы", "Интервью", "Одобрены", "Наняты"]}>
                {asList(detail.recruiters).map((raw) => {
                  const row = asRecord(raw);
                  return (
                    <tr key={String(row.recruiter_label)}>
                      <td>{String(row.recruiter_label)}</td>
                      <td>{String(row.assigned_candidates ?? 0)}</td>
                      <td>{String(row.qualified ?? 0)}</td>
                      <td>{String(row.interviews ?? 0)}</td>
                      <td>{String(row.approved ?? 0)}</td>
                      <td>{String(row.hired ?? 0)}</td>
                    </tr>
                  );
                })}
              </Table>
              <div className="mt-4" data-testid="ads-manual-spend">
                <p className="eds-type-helper">Расход внесён оператором. Это не синхронизация с рекламным кабинетом.</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Input value={spendForm.amount} onChange={(e) => setSpendForm({ ...spendForm, amount: e.target.value })} placeholder="Сумма" />
                  <Input value={spendForm.currency} onChange={(e) => setSpendForm({ ...spendForm, currency: e.target.value })} placeholder="Валюта" />
                  <Input type="date" value={spendForm.spent_on} onChange={(e) => setSpendForm({ ...spendForm, spent_on: e.target.value })} />
                  <Input value={spendForm.comment} onChange={(e) => setSpendForm({ ...spendForm, comment: e.target.value })} placeholder="Комментарий" />
                  <Button size="sm" onClick={() => void addSpend()}>Внести расход</Button>
                </div>
                <ul className="mt-2" data-testid="ads-spend-history">
                  {asList(detail.spend_entries).map((raw) => {
                    const row = asRecord(raw);
                    return (
                      <li key={String(row.id)}>
                        {String(row.amount)} {String(row.currency)} — {String(row.label_ru || "Расход внесён оператором")} — {String(row.entered_by || "—")}
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          ) : null}
          <p className="mt-3 eds-type-helper" data-testid="ads-campaign-approval">Live-изменения кампании только после согласования.</p>
          <ul data-testid="ads-campaign-writes">
            {asList(writes.items).map((raw) => {
              const row = asRecord(raw);
              return (
                <li key={String(row.id)}>
                  {String(row.action)} — {String(row.status)}
                  <Button size="sm" variant="secondary" onClick={() => void recruitingOpsPost(`/campaign-writes/${row.id}/decision`, { decision: "APPROVE" }, headers).then(load)}>
                    Одобрить
                  </Button>
                </li>
              );
            })}
          </ul>
        </Card>
      ) : null}
      {section === "leads" ? (
        <Card title="Лиды">
          <p>Лиды нормализуются из провайдера без перезаписи истории.</p>
          <p className="mt-2 eds-type-helper" data-testid="ads-messaging-approval">Сообщения требуют согласования. Неподключенный канал остаётся WAITING_PROVIDER.</p>
          <ul>
            {asList(messages.items).map((raw) => {
              const row = asRecord(raw);
              return (
                <li key={String(row.id)}>
                  {String(row.channel)} — {String(row.status)}
                  <Button size="sm" variant="secondary" onClick={() => void recruitingOpsPost(`/messages/${row.id}/decision`, { decision: "APPROVE" }, headers).then(load)}>
                    Одобрить отправку
                  </Button>
                </li>
              );
            })}
          </ul>
        </Card>
      ) : null}
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
          <Table headers={["Источник", "Заявки", "Квалифицированы", "Интервью", "Одобрены", "Наняты", "Расход", "CPL", "Стоимость найма"]}>
            {(sourceEconomics.length ? sourceEconomics : asList(sources.items)).map((raw) => {
              const row = asRecord(raw);
              return (
                <tr key={String(row.source)}>
                  <td>{String(row.label_ru || row.source)}</td>
                  <td>{String(row.applications ?? row.leads ?? 0)}</td>
                  <td>{metricLabel(row.qualified, "0")}</td>
                  <td>{metricLabel(row.interviews, "0")}</td>
                  <td>{metricLabel(row.approved, "0")}</td>
                  <td>{metricLabel(row.hired, "0")}</td>
                  <td>{metricLabel(row.spend)}</td>
                  <td>{metricLabel(row.cpl)}</td>
                  <td>{metricLabel(row.cost_per_hire)}</td>
                </tr>
              );
            })}
          </Table>
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
