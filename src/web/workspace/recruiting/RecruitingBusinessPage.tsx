/**
 * Sprint Recruiting 1.0 — operational recruiting cabinet via /api/recruiting-ops/v1.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useAuthStore } from "@/auth/authStore";
import {
  BusinessCabinetShell,
  type OpsNavItem,
  type OpsSection,
} from "../business-ops/BusinessCabinetShell";
import { asList, recruitingOpsFirstError, recruitingOpsGet, recruitingOpsPost, pick, recruitingWorkspaceHeaders } from "./recruitingApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";
import { displayMetric } from "./RecruitingOpsFrame";
import {
  COMM_CHANNELS,
  COMM_LABELS,
  PIPELINE_LABELS,
  PIPELINE_STAGES,
  RECRUITING_NAV,
  TASK_TEMPLATES,
  mapUiRoleToRecruiting,
  ruLeadStatus,
} from "./recruitingLabels";
import { CandidateEmailComposer } from "./CandidateEmailComposer";
import { WhatsAppConversation } from "./WhatsAppConversation";
import { LeadWorkflowPanel } from "./LeadWorkflowPanel";
import { CandidateWorkflowPanel } from "./CandidateWorkflowPanel";
import {
  attentionHref,
  buildRecruiterOptions,
  createdLabel,
  recruiterLabel,
  vacancyLabelForLead,
  type RecruiterOption,
} from "./recruitingWorkflow";

type Row = Record<string, unknown>;

type Bundle = {
  dashboard: Record<string, unknown>;
  leads: Row[];
  candidates: Row[];
  vacancies: Row[];
  campaigns: Row[];
  tasks: Row[];
  communications: Row[];
  activity: Row[];
  analytics: Record<string, unknown>;
  overdue: Row[];
  nextTasks: Row[];
  pipeline: Record<string, Row[]>;
};

const emptyBundle = (): Bundle => ({
  dashboard: {},
  leads: [],
  candidates: [],
  vacancies: [],
  campaigns: [],
  tasks: [],
  communications: [],
  activity: [],
  analytics: {},
  overdue: [],
  nextTasks: [],
  pipeline: {},
});

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

export function RecruitingBusinessPage() {
  const caps = resolveCabinetCaps("recruiting");
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const organizationId = useOrgSelector((s) => s.organizationId);
  const orgLabel = useOrgSelector((s) => s.label());
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const roleLabel = useRoleSwitcher((s) => s.activeOption()?.label || activeRoleId);
  const recruitingRole = mapUiRoleToRecruiting(activeRoleId);
  const currentUser = useAuthStore((s) => s.user);
  const canConvert = caps.canOperate && recruitingRole !== "hiring_manager";
  const selectedId = searchParams.get("id") || "";

  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>(emptyBundle);
  const [panel, setPanel] = useState<null | "lead" | "vacancy" | "campaign" | "task" | "comm">(null);
  const [leadForm, setLeadForm] = useState({ name: "", phone: "", email: "", source: "manual", vacancy_id: "", campaign_id: "" });
  const [vacancyForm, setVacancyForm] = useState({ title: "", department: "", location: "" });
  const [campaignForm, setCampaignForm] = useState({
    name: "",
    source: "vanguard",
    project_key: "vanguard",
    channel: "Organic",
    medium: "website",
    campaign_code: "",
    landing_url: "/vanguard",
    vacancy_id: "",
    budget: "",
    spend: "",
    start_date: "",
    end_date: "",
    status: "active",
  });
  const [taskForm, setTaskForm] = useState({ title: "Позвонить", assignee: "", due_date: "", lead_id: "", candidate_id: "", notes: "" });
  const [commForm, setCommForm] = useState({ channel: "PHONE", body: "", lead_id: "", candidate_id: "" });
  const [emailCandidate, setEmailCandidate] = useState<Row | null>(null);
  const [whatsappCandidate, setWhatsappCandidate] = useState<Row | null>(null);

  const headers = useMemo(
    () => recruitingWorkspaceHeaders(organizationId, recruitingRole),
    [organizationId, recruitingRole],
  );

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    setError(null);
    try {
      const health = await recruitingOpsGet("/health", headers);
      const [d, leads, cands, vacs, camps, tasks, comms, act, an] = await Promise.all([
        recruitingOpsGet("/dashboard", headers),
        recruitingOpsGet("/leads", headers),
        recruitingOpsGet("/candidates", headers),
        recruitingOpsGet("/vacancies", headers),
        recruitingOpsGet("/campaigns", headers),
        recruitingOpsGet("/tasks", headers),
        recruitingOpsGet("/communications", headers),
        recruitingOpsGet("/activity", headers),
        recruitingOpsGet("/analytics", headers),
      ]);
      if (!health.ok || ![d, leads].some((x) => x.ok || x.status === 404)) {
        setError(recruitingOpsFirstError([health, d, leads, cands, vacs]));
        setBundle(emptyBundle());
        return;
      }
      const dash = asRecord(d.json);
      const candJson = asRecord(cands.json);
      const taskJson = asRecord(tasks.json);
      setBundle({
        dashboard: dash,
        leads: asList(leads.json) as Row[],
        candidates: asList(cands.json) as Row[],
        vacancies: asList(vacs.json) as Row[],
        campaigns: asList(camps.json) as Row[],
        tasks: asList(tasks.json) as Row[],
        communications: asList(comms.json) as Row[],
        activity: asList(act.json) as Row[],
        analytics: asRecord(an.json),
        overdue: (Array.isArray(dash.overdue_tasks) ? dash.overdue_tasks : asList(taskJson.overdue_tasks)) as Row[],
        nextTasks: (Array.isArray(dash.next_tasks) ? dash.next_tasks : asList(taskJson.next_tasks)) as Row[],
        pipeline: (candJson.pipeline && typeof candJson.pipeline === "object" ? candJson.pipeline : {}) as Record<string, Row[]>,
      });
    } finally {
      setLoading(false);
      setHydrated(true);
    }
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (searchParams.get("view") === "projects") {
      navigate("/workspace/recruiting/projects", { replace: true });
    }
  }, [navigate, searchParams]);

  async function post(path: string, body: Record<string, unknown>) {
    setFormMsg(null);
    const res = await recruitingOpsPost(path, body, headers);
    const json = asRecord(res.json);
    if (!res.ok) {
      setFormMsg(String(json.message_ru || json.error || "Не удалось сохранить"));
      return { ok: false, json };
    }
    setPanel(null);
    await load({ silent: true });
    return { ok: true, json };
  }

  function openView(view: string, id?: string) {
    const next = new URLSearchParams(searchParams);
    if (view === "home") next.delete("view");
    else next.set("view", view);
    if (id) next.set("id", id);
    else next.delete("id");
    setSearchParams(next);
  }

  const cards = asRecord(bundle.dashboard.cards);
  const visits = asRecord(bundle.dashboard.visits || asRecord(bundle.analytics.visits));
  const funnel = asRecord(bundle.analytics.funnel);
  const attention = Array.isArray(bundle.dashboard.attention) ? (bundle.dashboard.attention as Row[]) : [];
  const attentionItems = Array.isArray(bundle.dashboard.attention_items)
    ? (bundle.dashboard.attention_items as Row[])
    : [];
  const selectedLead = bundle.leads.find((row) => String(row.id) === selectedId) || null;
  const selectedCandidate = bundle.candidates.find((row) => String(row.id) === selectedId) || null;
  const linkedLead = selectedCandidate
    ? bundle.leads.find((row) => String(row.id) === String(selectedCandidate.lead_id) || String(row.candidate_id) === String(selectedCandidate.id))
    : null;
  const recruiters: RecruiterOption[] = buildRecruiterOptions(
    [...bundle.leads, ...bundle.candidates, ...bundle.tasks],
    Array.isArray(bundle.dashboard.recruiters) ? (bundle.dashboard.recruiters as RecruiterOption[]) : [],
    currentUser,
  );

  const leadPanel = caps.canCreate ? (
    <form
      data-testid="recruiting-lead-form"
      className="grid gap-2 md:grid-cols-2"
      onSubmit={(e) => {
        e.preventDefault();
        void post("/leads", { ...leadForm });
      }}
    >
      <Input placeholder="Имя лида" value={leadForm.name} onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })} />
      <Input placeholder="Телефон" value={leadForm.phone} onChange={(e) => setLeadForm({ ...leadForm, phone: e.target.value })} />
      <Input placeholder="Email" value={leadForm.email} onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })} />
      <Input placeholder="Источник" value={leadForm.source} onChange={(e) => setLeadForm({ ...leadForm, source: e.target.value })} />
      <select
        className="eds-input"
        value={leadForm.vacancy_id}
        onChange={(e) => setLeadForm({ ...leadForm, vacancy_id: e.target.value })}
      >
        <option value="">Вакансия</option>
        {bundle.vacancies.map((v) => (
          <option key={String(v.id)} value={String(v.id)}>
            {pick(v, "title", "name")}
          </option>
        ))}
      </select>
      <select
        className="eds-input"
        value={leadForm.campaign_id}
        onChange={(e) => setLeadForm({ ...leadForm, campaign_id: e.target.value })}
      >
        <option value="">Кампания</option>
        {bundle.campaigns.map((c) => (
          <option key={String(c.id)} value={String(c.id)}>
            {pick(c, "name", "title")}
          </option>
        ))}
      </select>
      <div className="md:col-span-2">
        <Button type="submit" data-testid="recruiting-lead-submit">
          Сохранить лид
        </Button>
      </div>
    </form>
  ) : null;

  const sections: Record<string, OpsSection> = {
    home: {
      id: "home",
      title: "Рабочий стол рекрутера",
      description: "Новые заявки, квалификация и воронка найма — без внутренних кодов.",
      columns: [],
      rows: [],
      cards: [
        { label: "Новые лиды", value: error ? "Нет данных" : String(cards.new_leads ?? bundle.leads.filter((l) => String(l.status) === "new").length) },
        { label: "Квалифицированные", value: error ? "Нет данных" : String(cards.qualified ?? bundle.leads.filter((l) => ["qualified", "converted"].includes(String(l.status))).length) },
        { label: "Кандидаты", value: error ? "Нет данных" : String(cards.candidates ?? bundle.candidates.length) },
        { label: "Интервью", value: error ? "Нет данных" : String(cards.interviews ?? bundle.candidates.filter((c) => String(c.pipeline_stage) === "INTERVIEW").length) },
        { label: "Наняты", value: error ? "Нет данных" : String(cards.hired ?? bundle.candidates.filter((c) => String(c.pipeline_stage) === "HIRED").length) },
      ],
      emptyTitle: undefined,
      emptyDescription: undefined,
      quickActions: caps.canCreate
        ? [
            { label: "Создать лид", onClick: () => { setPanel("lead"); openView("leads"); } },
            { label: "Новая задача", onClick: () => setPanel("task") },
          ]
        : [],
      panel: (
        <div className="grid gap-3">
          <div data-testid="recruiting-projects-home">
          <Card title="ПРОЕКТЫ РЕКРУТИНГА">
            {(() => {
              const projects = Array.isArray(bundle.dashboard.projects) ? (bundle.dashboard.projects as Row[]) : [];
              const vanguard = projects.find((p) => String(p.project_key || p.id) === "vanguard") || projects[0];
              if (!vanguard) {
                return (
                  <div>
                    <p>Vanguard</p>
                    <p className="eds-type-helper">Нет данных</p>
                    <Button className="mt-2" onClick={() => navigate("/workspace/recruiting/projects/vanguard")}>
                      Открыть Vanguard
                    </Button>
                  </div>
                );
              }
              const integ = vanguard.integration_status && typeof vanguard.integration_status === "object"
                ? (vanguard.integration_status as Row)
                : {};
              return (
                <div>
                  <p className="eds-type-section">Vanguard</p>
                  <p className="eds-type-helper">Сайт заявок внутри Рекрутинга</p>
                  <p className="mt-1 eds-type-small">Статус: {String(integ.label_ru || integ.code || "Нет данных")}</p>
                  <p className="eds-type-small">Новые лиды: {String(vanguard.new_leads ?? "Нет данных")}</p>
                  <p className="eds-type-small">Последняя заявка: {String(vanguard.last_application_at || "Нет данных")}</p>
                  <Button className="mt-2" data-testid="open-vanguard-project" onClick={() => navigate("/workspace/recruiting/projects/vanguard")}>
                    Открыть Vanguard
                  </Button>
                </div>
              );
            })()}
          </Card>
          </div>
          <Card title="Требуют внимания" data-testid="recruiting-attention">
            {attentionItems.length || attention.length || bundle.overdue.length ? (
              <ul className="grid gap-2">
                {attentionItems.map((item, idx) => (
                  <li key={`${item.kind}-${item.entity_id}-${idx}`}>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => navigate(attentionHref(item))}
                    >
                      {String(item.message_ru || item.name || item.kind)}
                    </Button>
                  </li>
                ))}
                {!attentionItems.length
                  ? attention.map((item) => (
                      <li key={String(item.kind)}>{String(item.message_ru || item.kind)}</li>
                    ))
                  : null}
                {bundle.overdue.map((task) => (
                  <li key={String(task.id)}>
                    Просрочено: {pick(task, "title")}
                  </li>
                ))}
                {bundle.nextTasks.slice(0, 3).map((task) => (
                  <li key={`next-${String(task.id)}`}>
                    Ближайшие задачи: {pick(task, "title")}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="eds-type-helper">Нет записей, требующих внимания</p>
            )}
          </Card>
          <Card title="Посещения">
            <p data-testid="recruiting-visits-empty">{String(visits.message_ru || "Нет данных о посещениях")}</p>
          </Card>
          {panel === "lead" ? leadPanel : null}
        </div>
      ),
    },
    leads: {
      id: "leads",
      title: "Лиды",
      description: "Заявка → ответственный → вакансия → квалификация → кандидат.",
      columns: [
        { key: "name", label: "Имя" },
        { key: "phone", label: "Телефон" },
        { key: "email", label: "Email" },
        { key: "vacancy", label: "Вакансия" },
        { key: "assignee", label: "Ответственный" },
        { key: "status", label: "Статус" },
        { key: "created", label: "Создана" },
      ],
      rows: bundle.leads.map((l) => ({
        id: String(l.id || ""),
        name: pick(l, "name"),
        phone: pick(l, "phone"),
        email: pick(l, "email"),
        vacancy: vacancyLabelForLead(l, bundle.vacancies),
        assignee: recruiterLabel(l.assignee),
        status: ruLeadStatus(String(l.status || "")),
        created: createdLabel(l),
      })),
      statusFilterKey: "status",
      emptyTitle: "Лидов пока нет.",
      emptyDescription: "Новые заявки Vanguard появятся здесь автоматически.",
      emptyCtaLabel: caps.canCreate ? "Создать лид вручную" : undefined,
      emptyCtaOnClick: caps.canCreate ? () => setPanel("lead") : undefined,
      quickActions: caps.canCreate ? [{ label: "Создать лид вручную", onClick: () => setPanel("lead") }] : [],
      onRowOpen: (row) => openView("leads", String(row.id || "")),
      panel: panel === "lead" ? leadPanel : selectedLead ? (
        <LeadWorkflowPanel
          lead={selectedLead}
          vacancies={bundle.vacancies}
          recruiters={recruiters}
          canOperate={caps.canOperate}
          canConvert={canConvert}
          canCreate={caps.canCreate}
          onAssign={async (assignee) => (await post(`/leads/${selectedLead.id}/assign`, { assignee })).ok}
          onVacancy={async (vacancyId) => (await post(`/leads/${selectedLead.id}/vacancy`, { vacancy_id: vacancyId })).ok}
          onStatus={async (status) => (await post(`/leads/${selectedLead.id}/status`, { status })).ok}
          onQualify={async () => (await post(`/leads/${selectedLead.id}/qualify`, {})).ok}
          onConvert={async () => {
            const res = await post(`/leads/${selectedLead.id}/convert`, {});
            return res.ok || Boolean(res.json.already_converted || res.json.duplicate);
          }}
          onNote={async (notes) => (await post(`/leads/${selectedLead.id}/notes`, { notes })).ok}
          onOpenCandidate={(candidateId) => openView("candidates", candidateId)}
          onCreateVacancy={() => {
            setPanel("vacancy");
            openView("vacancies");
          }}
        />
      ) : bundle.leads.length ? (
        <p className="eds-type-helper" data-testid="lead-select-hint">
          Откройте лид в таблице, чтобы назначить ответственного и перевести в кандидаты.
        </p>
      ) : null,
      rowActions: (row) => (
        <Button size="sm" variant="secondary" onClick={() => openView("leads", String(row.id || ""))}>
          Открыть
        </Button>
      ),
    },
    candidates: {
      id: "candidates",
      title: "Кандидаты",
      description: "Люди в найме после перевода из лида.",
      columns: [
        { key: "name", label: "Имя" },
        { key: "phone", label: "Телефон" },
        { key: "email", label: "Email" },
        { key: "vacancy", label: "Вакансия" },
        { key: "assignee", label: "Ответственный" },
        { key: "stage", label: "Этап" },
        { key: "source", label: "Источник" },
      ],
      rows: bundle.candidates.map((c) => ({
        id: String(c.id || ""),
        name: pick(c, "name"),
        phone: pick(c, "phone"),
        email: pick(c, "email"),
        vacancy: vacancyLabelForLead(c, bundle.vacancies),
        assignee: recruiterLabel(c.assignee),
        stage: PIPELINE_LABELS[String(c.pipeline_stage || "")] || pick(c, "pipeline_stage"),
        source: pick(c, "source"),
      })),
      emptyTitle: "Кандидатов пока нет.",
      emptyDescription: "Откройте лид и нажмите «Перевести в кандидаты».",
      onRowOpen: (row) => openView("candidates", String(row.id || "")),
      rowActions: (row) => (
        <div className="flex flex-wrap gap-1">
          <Button size="sm" variant="secondary" onClick={() => openView("candidates", String(row.id || ""))}>
            Открыть
          </Button>
          {caps.canOperate ? (
            <>
              <Button size="sm" variant="ghost" onClick={() => setEmailCandidate(bundle.candidates.find((c) => String(c.id) === String(row.id)) || row)}>
                Письмо
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setWhatsappCandidate(bundle.candidates.find((c) => String(c.id) === String(row.id)) || row)}>
                WhatsApp
              </Button>
            </>
          ) : null}
        </div>
      ),
      panel: (
        <div className="grid gap-3">
          {selectedCandidate ? (
            <CandidateWorkflowPanel
              candidate={selectedCandidate}
              lead={linkedLead}
              vacancies={bundle.vacancies}
              canOperate={caps.canOperate}
              onStage={async (stage) => (await post(`/candidates/${selectedCandidate.id}/stage`, { pipeline_stage: stage })).ok}
              onOpenLead={(leadId) => openView("leads", leadId)}
            />
          ) : bundle.candidates.length ? (
            <p className="eds-type-helper">Откройте кандидата, чтобы увидеть воронку и исходную заявку.</p>
          ) : null}
          {emailCandidate ? (
            <CandidateEmailComposer
              candidateId={String(emailCandidate.id || "")}
              candidateName={pick(emailCandidate, "name")}
              candidateEmail={pick(emailCandidate, "email")}
              headers={headers}
            />
          ) : null}
          {whatsappCandidate ? (
            <WhatsAppConversation
              candidateId={String(whatsappCandidate.id || "")}
              candidateName={pick(whatsappCandidate, "name")}
              candidatePhone={pick(whatsappCandidate, "phone")}
              headers={headers}
            />
          ) : null}
        </div>
      ),
    },
    vacancies: {
      id: "vacancies",
      title: "Вакансии",
      description: "Открытые позиции, к которым привязываются лиды и кампании.",
      columns: [
        { key: "title", label: "Вакансия" },
        { key: "department", label: "Отдел" },
        { key: "location", label: "Локация" },
        { key: "status", label: "Статус" },
      ],
      rows: bundle.vacancies.map((v) => ({
        id: String(v.id || ""),
        title: pick(v, "title", "name"),
        department: pick(v, "department"),
        location: pick(v, "location"),
        status: pick(v, "status"),
      })),
      emptyTitle: "Вакансий пока нет.",
      emptyDescription: "Создайте вакансию, чтобы привязывать к ней заявки.",
      emptyCtaLabel: caps.canCreate ? "Создать вакансию" : undefined,
      emptyCtaOnClick: caps.canCreate ? () => setPanel("vacancy") : undefined,
      quickActions: caps.canCreate ? [{ label: "Создать вакансию", onClick: () => setPanel("vacancy") }] : [],
      panel:
        panel === "vacancy" ? (
          <form
            className="grid gap-2 md:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              void post("/vacancies", { ...vacancyForm });
            }}
          >
            <Input placeholder="Название" value={vacancyForm.title} onChange={(e) => setVacancyForm({ ...vacancyForm, title: e.target.value })} />
            <Input placeholder="Отдел" value={vacancyForm.department} onChange={(e) => setVacancyForm({ ...vacancyForm, department: e.target.value })} />
            <Input placeholder="Локация" value={vacancyForm.location} onChange={(e) => setVacancyForm({ ...vacancyForm, location: e.target.value })} />
            <Button type="submit">Сохранить вакансию</Button>
          </form>
        ) : bundle.vacancies[0] && caps.canOperate ? (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void post(`/vacancies/${String(bundle.vacancies[0].id)}`, { status: "closed" })}
          >
            Закрыть {pick(bundle.vacancies[0], "title", "name")}
          </Button>
        ) : null,
    },
    pipeline: {
      id: "pipeline",
      title: "Воронка",
      description: "NEW → QUALIFIED → INTERVIEW → APPROVED → HIRED. Состояние сохраняется после обновления.",
      columns: [
        { key: "name", label: "Кандидат" },
        { key: "stage", label: "Этап" },
        { key: "assignee", label: "Рекрутер" },
      ],
      rows: bundle.candidates.map((c) => ({
        id: String(c.id || ""),
        name: pick(c, "name"),
        stage: PIPELINE_LABELS[String(c.pipeline_stage || "")] || String(c.pipeline_stage || ""),
        assignee: pick(c, "assignee"),
      })),
      emptyTitle: "Воронка пуста",
      emptyDescription: "Преобразуйте квалифицированный лид — кандидат появится на доске.",
      panel: (
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6" data-testid="recruiting-pipeline-board">
          {PIPELINE_STAGES.map((stage) => {
            const items = bundle.pipeline[stage] || bundle.candidates.filter((c) => c.pipeline_stage === stage);
            return (
              <Card key={stage} title={`${PIPELINE_LABELS[stage]} (${items.length})`}>
                {items.length === 0 ? (
                  <p className="eds-type-helper">Пусто</p>
                ) : (
                  items.map((c) => (
                    <div key={String(c.id)} className="mb-2 flex flex-col gap-1">
                      <strong>{pick(c, "name")}</strong>
                      {caps.canOperate && stage !== "HIRED" && stage !== "REJECTED" ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            const idx = PIPELINE_STAGES.indexOf(stage);
                            const next = PIPELINE_STAGES[Math.min(idx + 1, PIPELINE_STAGES.length - 1)];
                            void post(`/candidates/${c.id}/stage`, { pipeline_stage: next });
                          }}
                        >
                          Дальше
                        </Button>
                      ) : null}
                    </div>
                  ))
                )}
              </Card>
            );
          })}
        </div>
      ),
    },
    campaigns: {
      id: "campaigns",
      title: "Кампании",
      description: "Маркировка источника трафика. Рекламные API не подключены.",
      columns: [
        { key: "name", label: "Кампания" },
        { key: "channel", label: "Канал" },
        { key: "source", label: "Источник" },
        { key: "medium", label: "Канал" },
        { key: "campaign_code", label: "Код" },
        { key: "status", label: "Статус" },
        { key: "spend", label: "Расход" },
      ],
      rows: bundle.campaigns.map((c) => ({
        id: String(c.id || ""),
        name: pick(c, "name", "title"),
        channel: pick(c, "channel"),
        source: pick(c, "source"),
        medium: pick(c, "medium"),
        campaign_code: pick(c, "campaign_code"),
        status: pick(c, "status"),
        spend: displayMetric(c.spend),
      })),
      emptyTitle: "Кампаний нет",
      emptyDescription: "Создайте кампанию вручную. Meta/Google/TikTok Ads не подключаются в этом спринте.",
      emptyCtaLabel: caps.canCreate ? "Создать кампанию" : undefined,
      emptyCtaOnClick: caps.canCreate ? () => setPanel("campaign") : undefined,
      quickActions: caps.canCreate ? [{ label: "Создать кампанию", onClick: () => setPanel("campaign") }] : [],
      panel:
        panel === "campaign" ? (
          <form
            className="grid gap-2 md:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              void post("/campaigns", {
                ...campaignForm,
                project_key: "vanguard",
                utm_url: `${campaignForm.landing_url}?utm_source=${encodeURIComponent(campaignForm.source)}&utm_medium=${encodeURIComponent(campaignForm.medium)}&utm_campaign=${encodeURIComponent(campaignForm.campaign_code || campaignForm.name)}`,
              });
            }}
          >
            <Input placeholder="Название" value={campaignForm.name} onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })} />
            <select className="eds-input" value={campaignForm.channel} onChange={(e) => setCampaignForm({ ...campaignForm, channel: e.target.value })}>
              {["Google", "Meta", "Instagram", "TikTok", "Telegram", "YouTube", "Organic", "Referral", "Direct", "Other"].map((ch) => (
                <option key={ch} value={ch}>{ch}</option>
              ))}
            </select>
            <Input placeholder="Источник" value={campaignForm.source} onChange={(e) => setCampaignForm({ ...campaignForm, source: e.target.value })} />
            <Input placeholder="Канал" value={campaignForm.medium} onChange={(e) => setCampaignForm({ ...campaignForm, medium: e.target.value })} />
            <Input placeholder="Код кампании" value={campaignForm.campaign_code} onChange={(e) => setCampaignForm({ ...campaignForm, campaign_code: e.target.value })} />
            <Input placeholder="Посадочная страница" value={campaignForm.landing_url} onChange={(e) => setCampaignForm({ ...campaignForm, landing_url: e.target.value })} />
            <Input placeholder="Статус (active/paused)" value={campaignForm.status} onChange={(e) => setCampaignForm({ ...campaignForm, status: e.target.value })} />
            <Input type="date" placeholder="Начало" value={campaignForm.start_date} onChange={(e) => setCampaignForm({ ...campaignForm, start_date: e.target.value })} />
            <Input type="date" placeholder="Окончание" value={campaignForm.end_date} onChange={(e) => setCampaignForm({ ...campaignForm, end_date: e.target.value })} />
            <Input placeholder="Бюджет" value={campaignForm.budget} onChange={(e) => setCampaignForm({ ...campaignForm, budget: e.target.value })} />
            <Input placeholder="Расход" value={campaignForm.spend} onChange={(e) => setCampaignForm({ ...campaignForm, spend: e.target.value })} />
            <Button type="submit">Сохранить кампанию</Button>
          </form>
        ) : null,
    },
    tasks: {
      id: "tasks",
      title: "Задачи",
      description: "Позвонить, написать, провести интервью — с исполнителем и сроком.",
      columns: [
        { key: "title", label: "Задача" },
        { key: "assignee", label: "Исполнитель" },
        { key: "due_date", label: "Срок" },
        { key: "status", label: "Статус" },
      ],
      rows: bundle.tasks.map((t) => ({
        id: String(t.id || ""),
        title: pick(t, "title"),
        assignee: pick(t, "assignee"),
        due_date: pick(t, "due_date"),
        status: pick(t, "status"),
      })),
      statusFilterKey: "status",
      emptyTitle: "Задач нет",
      emptyDescription: "Создайте задачу по лиду или кандидату. Просроченные появятся на главной.",
      emptyCtaLabel: caps.canCreate ? "Создать задачу" : undefined,
      emptyCtaOnClick: caps.canCreate ? () => setPanel("task") : undefined,
      quickActions: caps.canCreate ? [{ label: "Создать задачу", onClick: () => setPanel("task") }] : [],
      panel:
        panel === "task" ? (
          <form
            className="grid gap-2 md:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              void post("/tasks", { ...taskForm });
            }}
          >
            <select className="eds-input" value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}>
              {TASK_TEMPLATES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <Input placeholder="Исполнитель" value={taskForm.assignee} onChange={(e) => setTaskForm({ ...taskForm, assignee: e.target.value })} />
            <Input type="date" value={taskForm.due_date} onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })} />
            <select className="eds-input" value={taskForm.lead_id} onChange={(e) => setTaskForm({ ...taskForm, lead_id: e.target.value })}>
              <option value="">Лид</option>
              {bundle.leads.map((l) => (
                <option key={String(l.id)} value={String(l.id)}>
                  {pick(l, "name")}
                </option>
              ))}
            </select>
            <Input placeholder="Заметки" value={taskForm.notes} onChange={(e) => setTaskForm({ ...taskForm, notes: e.target.value })} />
            <Button type="submit">Сохранить задачу</Button>
          </form>
        ) : null,
      rowActions: caps.canOperate
        ? (row) =>
            String(row.status) !== "done" ? (
              <Button size="sm" variant="secondary" onClick={() => void post(`/tasks/${row.id}/complete`, {})}>
                Закрыть
              </Button>
            ) : null
        : undefined,
    },
    comms: {
      id: "comms",
      title: "Коммуникации",
      description: "Журнал вручную. WhatsApp — отдельный диалог с подтверждением человеком. Telegram заморожен.",
      columns: [
        { key: "channel", label: "Канал" },
        { key: "body", label: "Запись" },
        { key: "delivery", label: "Доставка" },
      ],
      rows: bundle.communications.map((c) => ({
        id: String(c.id || ""),
        channel: COMM_LABELS[String(c.channel || "")] || pick(c, "channel"),
        body: pick(c, "body"),
        delivery: c.sent === true ? "отправлено" : "только журнал",
      })),
      emptyTitle: "Журнал пуст",
      emptyDescription: "Пример: «Позвонили кандидату — ожидает решение.» Реальные мессенджеры не подключены.",
      emptyCtaLabel: caps.canCreate ? "Добавить запись" : undefined,
      emptyCtaOnClick: caps.canCreate ? () => setPanel("comm") : undefined,
      quickActions: caps.canCreate ? [{ label: "Добавить запись", onClick: () => setPanel("comm") }] : [],
      panel:
        panel === "comm" ? (
          <form
            className="grid gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void post("/communications", { ...commForm });
            }}
          >
            <select className="eds-input" value={commForm.channel} onChange={(e) => setCommForm({ ...commForm, channel: e.target.value })}>
              {COMM_CHANNELS.map((ch) => (
                <option key={ch} value={ch}>
                  {COMM_LABELS[ch]}
                </option>
              ))}
            </select>
            <Input
              placeholder="Позвонили кандидату — ожидает решение."
              value={commForm.body}
              onChange={(e) => setCommForm({ ...commForm, body: e.target.value })}
            />
            <Button type="submit">Сохранить в журнал</Button>
          </form>
        ) : null,
    },
    activity: {
      id: "activity",
      title: "История",
      description: "Все действия по лидам, кандидатам и задачам.",
      columns: [
        { key: "summary", label: "Событие" },
        { key: "action", label: "Действие" },
        { key: "created_at", label: "Когда" },
      ],
      rows: bundle.activity.map((a) => ({
        id: String(a.id || ""),
        summary: pick(a, "summary"),
        action: pick(a, "action"),
        created_at: pick(a, "created_at"),
      })),
      emptyTitle: "История пуста",
      emptyDescription: "Создание лида, заметки, квалификация и движение по воронке появятся здесь.",
    },
    analytics: {
      id: "analytics",
      title: "Атрибуция",
      description: "Воронка по сохранённым лидам. Визиты не выдумываются.",
      columns: [
        { key: "label", label: "Разрез" },
        { key: "count", label: "Лиды" },
      ],
      rows: (Array.isArray(bundle.analytics.by_source) ? (bundle.analytics.by_source as Row[]) : []).map((row) => ({
        id: String(row.id || row.label || ""),
        label: pick(row, "label", "id"),
        count: String(row.count ?? 0),
      })),
      cards: [
        { label: "Лиды", value: String(funnel.leads ?? bundle.leads.length) },
        { label: "Квалификация", value: String(funnel.qualified ?? 0) },
        { label: "Интервью", value: String(funnel.interviews ?? 0) },
        { label: "Одобрены", value: String(funnel.approved ?? 0) },
        { label: "Наняты", value: String(funnel.hired ?? 0) },
      ],
      emptyTitle: "Нет лидов для атрибуции",
      emptyDescription: "Метрики считаются только из сохранённых заявок.",
      panel: (
        <Card title="Посещения">
          <p data-testid="recruiting-analytics-visits">{String(asRecord(bundle.analytics.visits).message_ru || "Нет данных о посещениях")}</p>
        </Card>
      ),
    },
  };

  return (
    <BusinessCabinetShell
      verticalId="recruiting"
      title="Рекрутинг"
      subtitle={`${orgLabel} · операционный найм, без выдуманных визитов`}
      nav={RECRUITING_NAV as unknown as OpsNavItem[]}
      sections={sections}
      defaultSection="home"
      loading={loading && !hydrated}
      error={error}
      onRefresh={() => void load()}
      testId="recruiting-business-cabinet"
      roleHint={roleLabel}
      headerExtra={<span data-testid="recruiting-header-context">{orgLabel}</span>}
      banner={
        formMsg ? (
          <p className="eds-type-helper" data-testid="recruiting-form-msg">
            {formMsg}
          </p>
        ) : null
      }
    />
  );
}
