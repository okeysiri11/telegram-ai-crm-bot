/**
 * Sprint 51.0 — Lawyer Operator Desk: durable CRM cabinet via /api/legal-ops/v1.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import {
  BusinessCabinetShell,
  type OpsNavItem,
  type OpsSection,
} from "../business-ops/BusinessCabinetShell";
import { asList, legalOpsFileUrl, legalOpsGet, legalOpsPost, legalOpsUpload, pick } from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";
import { LawyerCalendarBoard } from "./LawyerCalendarBoard";
import { LawyerCrmCard } from "./LawyerCrmCard";
import { LawyerDetailDrawer, type AiHandoffContext, type DrawerKind } from "./LawyerDetailDrawer";
import { LawyerAiAnalysisPanel } from "./LawyerAiAnalysisPanel";
import { LawyerAiHistoryPanel, LawyerAiLawyerPanel } from "./LawyerAiLawyerPanel";
import { IntegrationHealthCard, LawyerMonitoringPanel } from "./LawyerMonitoringPanel";
import { LawyerConfirm, LawyerRowMenu } from "./LawyerRowMenu";
import { EVENT_TYPES, REMINDERS, TASK_PRIORITIES, TASK_STATUSES, TASK_VIEWS, ruStatus } from "./lawyerLabels";

const NAV_BASE: OpsNavItem[] = [
  { id: "home", label: "Главная" },
  { id: "clients", label: "Клиенты" },
  { id: "cases", label: "Дела" },
  { id: "contracts", label: "Договоры" },
  { id: "documents", label: "Документы" },
  { id: "tasks", label: "Задачи/Сроки" },
  { id: "hearings", label: "Суды/Заседания" },
  { id: "calendar", label: "Календарь" },
  { id: "monitoring", label: "Мониторинг" },
  { id: "inbox", label: "Входящие" },
  { id: "archive", label: "Архив" },
  { id: "ai-analysis", label: "AI-анализ" },
  { id: "ai", label: "AI-юрист" },
  { id: "ai-history", label: "История AI" },
  { id: "activity", label: "Активность" },
  { id: "settings", label: "Настройки" },
];

function mapUiRoleToLegal(roleId: string): string {
  const r = roleId.toLowerCase();
  if (r === "owner" || r.includes("platform_owner")) return "platform_owner";
  if (r === "administrator" || r === "admin") return "admin";
  if (r === "viewer" || r === "observer") return "observer";
  if (r === "manager" || r === "partner") return "managing_partner";
  if (r.includes("paralegal") || r.includes("помощник")) return "paralegal";
  if (r.includes("lawyer") || r.includes("юрист")) return "lawyer";
  return "lawyer";
}

type Bundle = {
  clients: Record<string, unknown>[];
  cases: Record<string, unknown>[];
  contracts: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  hearings: Record<string, unknown>[];
  calendar: Record<string, unknown>[];
  activity: Record<string, unknown>[];
  files: Record<string, unknown>[];
  inbox: Record<string, unknown>[];
  archive: Record<string, unknown>[];
  integrations: Record<string, unknown>[];
  aiAnalyses: Record<string, unknown>[];
  dashboard: Record<string, unknown>;
  gcal: Record<string, unknown>;
};

const emptyBundle = (): Bundle => ({
  clients: [],
  cases: [],
  contracts: [],
  documents: [],
  tasks: [],
  hearings: [],
  calendar: [],
  activity: [],
  files: [],
  inbox: [],
  archive: [],
  integrations: [],
  aiAnalyses: [],
  dashboard: {},
  gcal: {},
});

export function LawyerBusinessPage() {
  const caps = resolveCabinetCaps("legal");
  const organizationId = useOrgSelector((s) => s.organizationId);
  const orgLabel = useOrgSelector((s) => s.label());
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const roleLabel = useRoleSwitcher((s) => s.activeOption()?.label || activeRoleId);
  const legalRole = mapUiRoleToLegal(activeRoleId);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>(emptyBundle);
  const [panel, setPanel] = useState<
    null | "client" | "case" | "contract" | "document" | "task" | "hearing" | "calendar" | "ai" | "photo"
  >(null);
  const [editKind, setEditKind] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<{ kind: string; id: string } | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [archiveFilter, setArchiveFilter] = useState("all");
  const [clientQuery, setClientQuery] = useState({ q: "", client_type: "", status: "", responsible: "", tag: "" });
  const [taskView, setTaskView] = useState("all");
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);

  const [clientForm, setClientForm] = useState({
    name: "",
    email: "",
    phone: "",
    client_type: "person",
    address: "",
    city: "",
    country: "",
    company: "",
    position: "",
    responsible: "",
    status: "active",
    source: "",
    identity_data: "",
    tags: "",
    contacts: "",
    notes: "",
  });
  const [caseForm, setCaseForm] = useState({
    title: "",
    client_id: "",
    practice_area: "",
    case_type: "criminal",
    status: "open",
    responsible: "",
    court: "",
    judge: "",
    notes: "",
    priority: "normal",
    case_number: "",
    deadline_at: "",
  });
  const [contractForm, setContractForm] = useState({
    title: "",
    client_id: "",
    case_id: "",
    body: "",
    contract_number: "",
    counterparty: "",
    responsible: "",
    notes: "",
    deadline_at: "",
    end_at: "",
    amount: "",
    currency: "RUB",
    contract_type: "services",
  });
  const [docForm, setDocForm] = useState({ title: "", case_id: "", client_id: "", contract_id: "", content: "", description: "" });
  const [taskForm, setTaskForm] = useState({
    title: "",
    case_id: "",
    client_id: "",
    contract_id: "",
    kind: "deadline",
    due_at: "",
    description: "",
    priority: "normal",
    status: "new",
    assignee: "",
    reminder_minutes: "0",
  });
  const [hearingForm, setHearingForm] = useState({
    title: "",
    case_id: "",
    court_name: "",
    scheduled_at: "",
    ends_at: "",
    court_case_number: "",
    judge: "",
    room: "",
    hearing_format: "in_person",
    video_url: "",
    location: "",
    description: "",
    notes: "",
  });
  const [calForm, setCalForm] = useState({
    title: "",
    starts_at: "",
    ends_at: "",
    case_id: "",
    event_type: "meeting",
    reminder_minutes: "0",
    location: "",
    description: "",
    client_id: "",
    contract_id: "",
  });
  const [aiHandoff, setAiHandoff] = useState<(AiHandoffContext & { prompt?: string }) | null>(null);
  const [drawer, setDrawer] = useState<{ kind: DrawerKind; id: string } | null>(null);
  const [, setSearchParams] = useSearchParams();

  const headers = useMemo(
    () => ({
      "X-Organization-Id": organizationId,
      "X-Tenant-Id": organizationId,
      "X-Role": legalRole,
    }),
    [organizationId, legalRole],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, c, ca, co, doc, t, h, cal, act, g, files, inbox, arch, integ, aiHist] = await Promise.all([
        legalOpsGet("/dashboard", headers),
        legalOpsGet("/clients", headers),
        legalOpsGet("/cases", headers),
        legalOpsGet("/contracts", headers),
        legalOpsGet("/documents", headers),
        legalOpsGet("/tasks", headers),
        legalOpsGet("/hearings", headers),
        legalOpsGet("/calendar", headers),
        legalOpsGet("/activity", headers),
        legalOpsGet("/integrations/google-calendar", headers),
        legalOpsGet("/files", headers),
        legalOpsGet("/inbox", headers),
        legalOpsGet("/archive", headers),
        legalOpsGet("/integrations/calendars", headers),
        legalOpsGet("/ai/analyses", headers),
      ]);
      if (![d, c, ca].some((x) => x.ok || x.status === 404)) {
        setError("Legal Ops API недоступен. Запустите backend (:8080).");
      }
      setBundle({
        clients: asList(c.json) as Record<string, unknown>[],
        cases: asList(ca.json) as Record<string, unknown>[],
        contracts: asList(co.json) as Record<string, unknown>[],
        documents: asList(doc.json) as Record<string, unknown>[],
        tasks: asList(t.json) as Record<string, unknown>[],
        hearings: asList(h.json) as Record<string, unknown>[],
        calendar: asList(cal.json) as Record<string, unknown>[],
        activity: asList(act.json) as Record<string, unknown>[],
        files: asList(files.json) as Record<string, unknown>[],
        inbox: asList(inbox.json) as Record<string, unknown>[],
        archive: asList(arch.json) as Record<string, unknown>[],
        integrations: asList(integ.json) as Record<string, unknown>[],
        aiAnalyses: asList(aiHist.json) as Record<string, unknown>[],
        dashboard: (d.json && typeof d.json === "object" ? d.json : {}) as Record<string, unknown>,
        gcal: (g.json && typeof g.json === "object" ? g.json : {}) as Record<string, unknown>,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  async function post(path: string, body: Record<string, unknown>) {
    setFormMsg(null);
    const res = await legalOpsPost(
      path,
      { ...body, organization_id: organizationId, role: legalRole },
      headers,
    );
    if (!res.ok) {
      const j = res.json as { message_ru?: string; error?: string };
      setFormMsg(j.message_ru || j.error || "Ошибка запроса");
      return null;
    }
    await load();
    return res.json;
  }

  async function archiveKind(kind: string, id: string) {
    setArchiveTarget({ kind, id });
  }

  async function confirmArchive() {
    if (!archiveTarget) return;
    await post(`/entities/${archiveTarget.kind}/${archiveTarget.id}/archive`, {});
    setArchiveTarget(null);
  }

  async function restoreKind(kind: string, id: string) {
    await post(`/entities/${kind}/${id}/restore`, {});
  }

  const DRAWER_KINDS: DrawerKind[] = ["client", "case", "contract", "document", "task", "hearing"];

  async function openEntity(kind: string, id: string) {
    if (DRAWER_KINDS.includes(kind as DrawerKind)) {
      setDrawer({ kind: kind as DrawerKind, id });
      return;
    }
    await openEditCard(kind, id);
  }

  async function openEditCard(kind: string, id: string) {
    const res = await legalOpsGet(`/entities/${kind}/${id}`, headers);
    if (res.ok && res.json && typeof res.json === "object") {
      setDetail((res.json as { item?: Record<string, unknown> }).item || (res.json as Record<string, unknown>));
      setEditKind(kind);
      setEditId(id);
    }
  }

  function handoffToAi(ctx: AiHandoffContext) {
    setAiHandoff(ctx);
    setDrawer(null);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("view", "ai");
      return next;
    });
  }

  async function saveEdit() {
    if (!editKind || !editId) return;
    const r = await post(`/entities/${editKind}/${editId}`, editForm);
    if (r) {
      setEditKind(null);
      setEditId(null);
      setDetail(null);
    }
  }

  async function uploadSelected(file: File, entityType?: string, entityId?: string) {
    setFormMsg(null);
    const res = await legalOpsUpload(
      "/files",
      file,
      {
        entity_type: entityType || "",
        entity_id: entityId || "",
        filename: file.name,
      },
      headers,
    );
    if (!res.ok) {
      const j = res.json as { message_ru?: string; error?: string };
      setFormMsg(j.message_ru || j.error || "Ошибка загрузки");
      return;
    }
    const item = (res.json as { item?: { id?: string } })?.item;
    if (entityType === "client" && entityId && item?.id) {
      await post(`/entities/client/${entityId}`, { avatar_file_id: item.id });
    }
    await load();
  }

  async function previewFile(fileId: string, mime?: string) {
    const res = await fetch(legalOpsFileUrl(fileId), { credentials: "include", headers });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (mime && mime.startsWith("image/")) {
      setPreviewUrl(url);
      setPdfPreviewUrl(null);
    } else if (mime === "application/pdf" || String(mime || "").includes("pdf")) {
      setPdfPreviewUrl(url);
      setPreviewUrl(null);
    } else {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  }

  async function uploadMany(files: FileList | File[], entityType?: string, entityId?: string) {
    for (const f of Array.from(files)) {
      await uploadSelected(f, entityType, entityId);
    }
  }

  function downloadFile(fileId: string, filename: string) {
    const a = document.createElement("a");
    a.href = legalOpsFileUrl(fileId);
    a.download = filename || "file";
    a.rel = "noopener";
    a.click();
  }

  async function replaceFile(fileId: string, file: File) {
    await legalOpsUpload(`/files/${fileId}/replace`, file, { filename: file.name }, headers);
    await load();
  }

  function nameById(kind: "client" | "case" | "contract", id: unknown): string {
    const sid = String(id || "");
    if (!sid) return "—";
    const list = kind === "client" ? bundle.clients : kind === "case" ? bundle.cases : bundle.contracts;
    const hit = list.find((x) => pick(x, "id") === sid);
    return hit ? pick(hit, "name", "title") : sid;
  }

  const cards = (bundle.dashboard.cards || {}) as Record<string, number>;

  const clientPanel =
    panel === "client" && caps.canCreate ? (
      <Card title="Новый клиент">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-client-form">
          {(
            [
              ["name", "Имя / название"],
              ["phone", "Телефон"],
              ["email", "Email"],
              ["address", "Адрес"],
              ["city", "Город"],
              ["country", "Страна"],
              ["company", "Компания"],
              ["position", "Должность"],
              ["responsible", "Ответственный юрист"],
              ["source", "Источник"],
              ["identity_data", "Идентификационные данные"],
              ["tags", "Теги"],
              ["contacts", "Доп. контакты"],
              ["notes", "Заметки"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="eds-type-small">
              {label}
              <Input
                className="mt-1"
                value={clientForm[key]}
                onChange={(e) => setClientForm((f) => ({ ...f, [key]: e.target.value }))}
              />
            </label>
          ))}
          <label className="eds-type-small">
            Тип клиента
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={clientForm.client_type}
              onChange={(e) => setClientForm((f) => ({ ...f, client_type: e.target.value }))}
            >
              <option value="person">Физическое лицо</option>
              <option value="company">Юридическое лицо</option>
            </select>
          </label>
          <label className="eds-type-small">
            Статус
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={clientForm.status}
              onChange={(e) => setClientForm((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="active">Активен</option>
              <option value="pending">Ожидает</option>
              <option value="closed">Закрыто</option>
            </select>
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-client-submit"
            onClick={async () => {
              const r = await post("/clients", {
                ...clientForm,
                tags: clientForm.tags.split(",").map((x) => x.trim()).filter(Boolean),
                contacts: clientForm.contacts.split(",").map((x) => x.trim()).filter(Boolean),
              });
              if (r) {
                setPanel(null);
                setClientForm({
                  name: "",
                  email: "",
                  phone: "",
                  client_type: "person",
                  address: "",
                  city: "",
                  country: "",
                  company: "",
                  position: "",
                  responsible: "",
                  status: "active",
                  source: "",
                  identity_data: "",
                  tags: "",
                  contacts: "",
                  notes: "",
                });
              }
            }}
          >
            Создать клиента
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const casePanel =
    panel === "case" && caps.canCreate ? (
      <Card title="Новое дело">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-case-form">
          <label className="eds-type-small">
            Название
            <Input
              className="mt-1"
              value={caseForm.title}
              onChange={(e) => setCaseForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Клиент
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={caseForm.client_id}
              onChange={(e) => setCaseForm((f) => ({ ...f, client_id: e.target.value }))}
            >
              <option value="">Выберите</option>
              {bundle.clients.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Практика
            <Input
              className="mt-1"
              value={caseForm.practice_area}
              onChange={(e) => setCaseForm((f) => ({ ...f, practice_area: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Тип дела
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={caseForm.case_type}
              onChange={(e) => setCaseForm((f) => ({ ...f, case_type: e.target.value }))}
            >
              <option value="criminal">Уголовное</option>
              <option value="civil">Гражданское</option>
              <option value="commercial">Коммерческое</option>
            </select>
          </label>
          <label className="eds-type-small">
            Номер
            <Input className="mt-1" value={caseForm.case_number} onChange={(e) => setCaseForm((f) => ({ ...f, case_number: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Ответственный
            <Input className="mt-1" value={caseForm.responsible} onChange={(e) => setCaseForm((f) => ({ ...f, responsible: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Суд
            <Input className="mt-1" value={caseForm.court} onChange={(e) => setCaseForm((f) => ({ ...f, court: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Судья
            <Input className="mt-1" value={caseForm.judge} onChange={(e) => setCaseForm((f) => ({ ...f, judge: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Заметки
            <Input className="mt-1" value={caseForm.notes} onChange={(e) => setCaseForm((f) => ({ ...f, notes: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Срок (ISO)
            <Input className="mt-1" value={caseForm.deadline_at} onChange={(e) => setCaseForm((f) => ({ ...f, deadline_at: e.target.value }))} />
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-case-submit"
            onClick={async () => {
              const r = await post("/cases", caseForm);
              if (r) {
                setPanel(null);
                setCaseForm({
                  title: "",
                  client_id: "",
                  practice_area: "",
                  case_type: "criminal",
                  status: "open",
                  responsible: "",
                  court: "",
                  judge: "",
                  notes: "",
                  priority: "normal",
                  case_number: "",
                  deadline_at: "",
                });
              }
            }}
          >
            Создать дело
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const contractPanel =
    panel === "contract" && caps.canCreate ? (
      <Card title="Новый договор">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-contract-form">
          <label className="eds-type-small">
            Название
            <Input
              className="mt-1"
              value={contractForm.title}
              onChange={(e) => setContractForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Клиент
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={contractForm.client_id}
              onChange={(e) => setContractForm((f) => ({ ...f, client_id: e.target.value }))}
            >
              <option value="">Выберите</option>
              {bundle.clients.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Дело
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={contractForm.case_id}
              onChange={(e) => setContractForm((f) => ({ ...f, case_id: e.target.value }))}
            >
              <option value="">Опционально</option>
              {bundle.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Текст
            <Input
              className="mt-1"
              value={contractForm.body}
              onChange={(e) => setContractForm((f) => ({ ...f, body: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Номер
            <Input className="mt-1" value={contractForm.contract_number} onChange={(e) => setContractForm((f) => ({ ...f, contract_number: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Контрагент
            <Input className="mt-1" value={contractForm.counterparty} onChange={(e) => setContractForm((f) => ({ ...f, counterparty: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Сумма
            <Input className="mt-1" value={contractForm.amount} onChange={(e) => setContractForm((f) => ({ ...f, amount: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Валюта
            <Input className="mt-1" value={contractForm.currency} onChange={(e) => setContractForm((f) => ({ ...f, currency: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Тип
            <Input className="mt-1" value={contractForm.contract_type} onChange={(e) => setContractForm((f) => ({ ...f, contract_type: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Срок (ISO)
            <Input className="mt-1" value={contractForm.deadline_at} onChange={(e) => setContractForm((f) => ({ ...f, deadline_at: e.target.value }))} />
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-contract-submit"
            onClick={async () => {
              const r = await post("/contracts", {
                ...contractForm,
                amount: contractForm.amount ? Number(contractForm.amount) : null,
              });
              if (r) {
                setPanel(null);
                setContractForm({
                  title: "",
                  client_id: "",
                  case_id: "",
                  body: "",
                  contract_number: "",
                  counterparty: "",
                  responsible: "",
                  notes: "",
                  deadline_at: "",
                  end_at: "",
                  amount: "",
                  currency: "RUB",
                  contract_type: "services",
                });
              }
            }}
          >
            Создать договор
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const documentPanel =
    panel === "document" && caps.canCreate ? (
      <Card title="Загрузить документ">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-document-form">
          <label className="eds-type-small">
            Название
            <Input
              className="mt-1"
              value={docForm.title}
              onChange={(e) => setDocForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Дело
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={docForm.case_id}
              onChange={(e) => setDocForm((f) => ({ ...f, case_id: e.target.value }))}
            >
              <option value="">Опционально</option>
              {bundle.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Содержимое / текст
            <Input
              className="mt-1"
              value={docForm.content}
              onChange={(e) => setDocForm((f) => ({ ...f, content: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Файл PDF/DOC/DOCX/JPG/PNG/WebP (можно несколько)
            <input
              className="mt-1 block w-full eds-type-small"
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,application/pdf,image/*"
              data-testid="lawyer-file-input"
              onChange={(e) => {
                if (e.target.files?.length) {
                  void uploadMany(e.target.files, docForm.case_id ? "case" : docForm.client_id ? "client" : "inbox", docForm.case_id || docForm.client_id || undefined);
                }
              }}
            />
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-document-submit"
            onClick={async () => {
              const r = await post("/documents", docForm);
              if (r) {
                setPanel(null);
                setDocForm({ title: "", case_id: "", client_id: "", contract_id: "", content: "", description: "" });
              }
            }}
          >
            Загрузить
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const taskPanel =
    panel === "task" && caps.canCreate ? (
      <Card title="Задача / срок">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-task-form">
          <label className="eds-type-small">
            Название
            <Input className="mt-1" value={taskForm.title} onChange={(e) => setTaskForm((f) => ({ ...f, title: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Описание
            <Input className="mt-1" value={taskForm.description} onChange={(e) => setTaskForm((f) => ({ ...f, description: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Тип
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.kind} onChange={(e) => setTaskForm((f) => ({ ...f, kind: e.target.value }))}>
              <option value="deadline">Срок</option>
              <option value="task">Задача</option>
            </select>
          </label>
          <label className="eds-type-small">
            Статус
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.status} onChange={(e) => setTaskForm((f) => ({ ...f, status: e.target.value }))}>
              {TASK_STATUSES.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Приоритет
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.priority} onChange={(e) => setTaskForm((f) => ({ ...f, priority: e.target.value }))}>
              {TASK_PRIORITIES.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Срок (ISO)
            <Input className="mt-1" value={taskForm.due_at} onChange={(e) => setTaskForm((f) => ({ ...f, due_at: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Ответственный
            <Input className="mt-1" value={taskForm.assignee} onChange={(e) => setTaskForm((f) => ({ ...f, assignee: e.target.value }))} />
          </label>
          <label className="eds-type-small">
            Клиент
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.client_id} onChange={(e) => setTaskForm((f) => ({ ...f, client_id: e.target.value }))}>
              <option value="">Опционально</option>
              {bundle.clients.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>{pick(c, "name")}</option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Дело
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.case_id} onChange={(e) => setTaskForm((f) => ({ ...f, case_id: e.target.value }))}>
              <option value="">Опционально</option>
              {bundle.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>{pick(c, "title")}</option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Договор
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.contract_id} onChange={(e) => setTaskForm((f) => ({ ...f, contract_id: e.target.value }))}>
              <option value="">Опционально</option>
              {bundle.contracts.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>{pick(c, "title")}</option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Напоминание
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={taskForm.reminder_minutes} onChange={(e) => setTaskForm((f) => ({ ...f, reminder_minutes: e.target.value }))}>
              {REMINDERS.map((r) => (
                <option key={r.minutes} value={String(r.minutes)}>{r.label}</option>
              ))}
            </select>
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-task-submit"
            onClick={async () => {
              const r = await post("/tasks", { ...taskForm, reminder_minutes: Number(taskForm.reminder_minutes) || null });
              if (r) {
                setPanel(null);
                setTaskForm({
                  title: "",
                  case_id: "",
                  client_id: "",
                  contract_id: "",
                  kind: "deadline",
                  due_at: "",
                  description: "",
                  priority: "normal",
                  status: "new",
                  assignee: "",
                  reminder_minutes: "0",
                });
              }
            }}
          >
            Создать
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const hearingPanel =
    panel === "hearing" && caps.canCreate ? (
      <Card title="Заседание">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-hearing-form">
          {(
            [
              ["title", "Название"],
              ["court_name", "Суд"],
              ["scheduled_at", "Дата/время начала"],
              ["ends_at", "Окончание"],
              ["court_case_number", "Номер судебного дела"],
              ["judge", "Судья"],
              ["room", "Зал"],
              ["location", "Адрес"],
              ["video_url", "Ссылка видеоконференции"],
              ["description", "Описание"],
              ["notes", "Заметки"],
            ] as const
          ).map(([key, label]) => (
            <label key={key} className="eds-type-small">
              {label}
              <Input className="mt-1" value={hearingForm[key]} onChange={(e) => setHearingForm((f) => ({ ...f, [key]: e.target.value }))} />
            </label>
          ))}
          <label className="eds-type-small">
            Формат
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={hearingForm.hearing_format} onChange={(e) => setHearingForm((f) => ({ ...f, hearing_format: e.target.value }))}>
              <option value="in_person">Очно</option>
              <option value="online">Онлайн</option>
              <option value="other">Другое</option>
            </select>
          </label>
          <label className="eds-type-small">
            Дело
            <select className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1" value={hearingForm.case_id} onChange={(e) => setHearingForm((f) => ({ ...f, case_id: e.target.value }))}>
              <option value="">Опционально</option>
              {bundle.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>{pick(c, "title")}</option>
              ))}
            </select>
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-hearing-submit"
            onClick={async () => {
              const r = await post("/hearings", hearingForm);
              if (r) {
                setPanel(null);
                setHearingForm({
                  title: "",
                  case_id: "",
                  court_name: "",
                  scheduled_at: "",
                  ends_at: "",
                  court_case_number: "",
                  judge: "",
                  room: "",
                  hearing_format: "in_person",
                  video_url: "",
                  location: "",
                  description: "",
                  notes: "",
                });
              }
            }}
          >
            Создать заседание
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const calendarPanel =
    panel === "calendar" && caps.canCreate ? (
      <Card title="Событие календаря">
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-calendar-form">
          <label className="eds-type-small">
            Название
            <Input
              className="mt-1"
              value={calForm.title}
              onChange={(e) => setCalForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Начало
            <Input
              className="mt-1"
              value={calForm.starts_at}
              onChange={(e) => setCalForm((f) => ({ ...f, starts_at: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Конец
            <Input
              className="mt-1"
              value={calForm.ends_at}
              onChange={(e) => setCalForm((f) => ({ ...f, ends_at: e.target.value }))}
            />
          </label>
          <label className="eds-type-small">
            Тип
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={calForm.event_type}
              onChange={(e) => setCalForm((f) => ({ ...f, event_type: e.target.value }))}
            >
              {EVENT_TYPES.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Напоминание
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={calForm.reminder_minutes}
              onChange={(e) => setCalForm((f) => ({ ...f, reminder_minutes: e.target.value }))}
            >
              {REMINDERS.map((r) => (
                <option key={r.minutes} value={String(r.minutes)}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Дело
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={calForm.case_id}
              onChange={(e) => setCalForm((f) => ({ ...f, case_id: e.target.value }))}
            >
              <option value="">Опционально</option>
              {bundle.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Клиент
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={calForm.client_id}
              onChange={(e) => setCalForm((f) => ({ ...f, client_id: e.target.value }))}
            >
              <option value="">Опционально</option>
              {bundle.clients.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Договор
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={calForm.contract_id}
              onChange={(e) => setCalForm((f) => ({ ...f, contract_id: e.target.value }))}
            >
              <option value="">Опционально</option>
              {bundle.contracts.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
          </label>
        </div>
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-3 flex gap-2">
          <Button
            data-testid="lawyer-calendar-submit"
            onClick={async () => {
              const r = await post("/calendar", {
                ...calForm,
                reminder_minutes: Number(calForm.reminder_minutes) || null,
              });
              if (r) {
                setPanel(null);
                setCalForm({
                  title: "",
                  starts_at: "",
                  ends_at: "",
                  case_id: "",
                  event_type: "meeting",
                  reminder_minutes: "0",
                  location: "",
                  description: "",
                  client_id: "",
                  contract_id: "",
                });
              }
            }}
          >
            Создать событие
          </Button>
          <Button variant="ghost" onClick={() => setPanel(null)}>
            Отмена
          </Button>
        </div>
      </Card>
    ) : null;

  const aiPanel = (
    <LawyerAiLawyerPanel
      headers={headers}
      canOperate={caps.canOperate}
      clients={bundle.clients}
      cases={bundle.cases}
      documents={bundle.documents}
      onRefresh={() => void load()}
      initial={aiHandoff || undefined}
    />
  );

  const aiAnalysisPanel = (
    <LawyerAiAnalysisPanel
      headers={headers}
      canOperate={caps.canOperate}
      clients={bundle.clients}
      cases={bundle.cases}
      contracts={bundle.contracts}
      documents={bundle.documents}
      onRefresh={() => void load()}
      onHandoff={(p) => {
        setAiHandoff({ clientId: p.clientId, caseId: p.caseId, prompt: p.question });
      }}
    />
  );

  const aiHistoryPanel = (
    <LawyerAiHistoryPanel
      headers={headers}
      canOperate={caps.canOperate}
      items={bundle.aiAnalyses}
      onRefresh={() => void load()}
    />
  );

  const monitoringPanel = (
    <LawyerMonitoringPanel
      headers={headers}
      canOperate={caps.canOperate}
      cases={bundle.cases}
      clients={bundle.clients}
      onRefresh={() => void load()}
      onHandoffAi={(ctx) => handoffToAi(ctx)}
    />
  );

  const extraPanels = (
    <>
      {drawer ? (
        <LawyerDetailDrawer
          kind={drawer.kind}
          itemId={drawer.id}
          headers={headers}
          canOperate={caps.canOperate}
          onClose={() => setDrawer(null)}
          onNavigate={(k, id) => setDrawer({ kind: k, id })}
          onEdit={(k, id) => {
            setDrawer(null);
            void openEditCard(k, id);
          }}
          onArchive={(k, id) => {
            setDrawer(null);
            void archiveKind(k, id);
          }}
          onHandoffAi={handoffToAi}
          onPreviewFile={(id, mime) => void previewFile(id, mime)}
        />
      ) : null}
      <LawyerConfirm
        open={Boolean(archiveTarget)}
        text={
          archiveTarget
            ? `Будет удалён объект типа «${archiveTarget.kind}» (id ${archiveTarget.id}). Файлы и связанные записи будут архивированы без жёсткого удаления.`
            : "Удалить объект?"
        }
        confirmLabel="Да, удалить в архив"
        onYes={() => void confirmArchive()}
        onNo={() => setArchiveTarget(null)}
      />
      {editKind && editId && (editKind === "client" || editKind === "case") ? (
        <LawyerCrmCard
          kind={editKind}
          itemId={editId}
          headers={headers}
          editForm={editForm}
          onEditChange={(k, v) => setEditForm((f) => ({ ...f, [k]: v }))}
          onSave={() => void saveEdit()}
          onClose={() => {
            setEditKind(null);
            setEditId(null);
            setDetail(null);
          }}
          onArchive={() => void archiveKind(editKind, editId)}
          onQuick={(action) => {
            if (editKind === "case" && editId) {
              if (action === "document") setDocForm((f) => ({ ...f, case_id: editId }));
              if (action === "task") setTaskForm((f) => ({ ...f, case_id: editId }));
              if (action === "hearing") setHearingForm((f) => ({ ...f, case_id: editId }));
              if (action === "calendar") setCalForm((f) => ({ ...f, case_id: editId }));
            }
            if (editKind === "client" && editId && action === "case") {
              setCaseForm((f) => ({ ...f, client_id: editId }));
            }
            setPanel(action as typeof panel);
          }}
          onPreviewFile={(id, mime) => void previewFile(id, mime)}
        />
      ) : null}
      {editKind && detail && editKind !== "client" && editKind !== "case" ? (
        <Card title={editKind === "document" ? "Карточка документа" : "Карточка"}>
          <div data-testid="lawyer-entity-card">
          {editKind === "document" ? (
            <dl className="mb-3 grid gap-1 sm:grid-cols-2 eds-type-small" data-testid="lawyer-document-card">
              <div>Название: {pick(detail, "title")}</div>
              <div>Тип: {ruStatus(pick(detail, "doc_type"))}</div>
              <div>Связанный клиент: {nameById("client", detail.client_id)}</div>
              <div>Связанное дело: {nameById("case", detail.case_id)}</div>
              <div>Связанный договор: {nameById("contract", detail.contract_id)}</div>
              <div>Автор загрузки: {pick(detail, "uploaded_by", "created_by") || "—"}</div>
              <div>Дата: {pick(detail, "created_at")}</div>
              <div>Комментарий: {pick(detail, "notes") || String((detail.payload as { content_preview?: string } | undefined)?.content_preview || "—")}</div>
              <div>Версия: {String(detail.version ?? 1)}</div>
              <div>Файл: {pick(detail, "storage_ref") || "—"}</div>
            </dl>
          ) : null}
          {editKind === "calendar" ? (
            <div className="mb-3 flex flex-wrap gap-2 eds-type-small">
              {detail.case_id ? (
                <Button size="sm" variant="ghost" onClick={() => void openEntity("case", String(detail.case_id))}>
                  Открыть связанное дело
                </Button>
              ) : null}
              {detail.client_id ? (
                <Button size="sm" variant="ghost" onClick={() => void openEntity("client", String(detail.client_id))}>
                  Открыть клиента
                </Button>
              ) : null}
              {detail.contract_id ? (
                <Button size="sm" variant="ghost" onClick={() => void openEntity("contract", String(detail.contract_id))}>
                  Открыть договор
                </Button>
              ) : null}
            </div>
          ) : null}
          <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-edit-form">
            {Object.entries({
              title: "Название",
              status: "Статус",
              notes: "Заметки",
              case_number: "Номер дела",
              case_type: "Тип",
              responsible: "Ответственный",
              court: "Суд",
              judge: "Судья",
              priority: "Приоритет",
              participants: "Участники",
              opened_at: "Дата открытия",
              closed_at: "Дата закрытия",
              deadline_at: "Срок",
              contract_number: "Номер договора",
              counterparty: "Контрагент",
              approval_status: "Согласование",
              signing_status: "Подписание",
              start_at: "Начало",
              end_at: "Окончание",
              location: "Место",
              description: "Описание",
              reminder_minutes: "Напоминание (мин)",
              event_type: "Тип события",
            }).map(([key, label]) =>
              detail[key] !== undefined || ["title", "status", "notes"].includes(key) ? (
                <label key={key} className="eds-type-small">
                  {label}
                  <Input
                    className="mt-1"
                    value={editForm[key] ?? String(detail[key] ?? "")}
                    onChange={(e) => setEditForm((f) => ({ ...f, [key]: e.target.value }))}
                  />
                </label>
              ) : null,
            )}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" data-testid="lawyer-edit-save" onClick={() => void saveEdit()}>
              Редактировать
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setEditKind(null); setDetail(null); }}>
              Закрыть
            </Button>
            {editKind === "document" ? (
              <Button size="sm" variant="ghost" onClick={() => setPanel("ai")}>
                AI-анализ
              </Button>
            ) : null}
            {editKind === "case" && editId ? (
              <Button size="sm" variant="ghost" onClick={() => setPanel("calendar")}>
                Открыть календарь
              </Button>
            ) : null}
            {editId ? (
              <label className="eds-type-small">
                Добавить фото документа
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                  className="mt-1 block"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f && editKind && editId) void uploadSelected(f, editKind, editId);
                  }}
                />
              </label>
            ) : null}
          </div>
          <div className="mt-4" data-testid="lawyer-card-files">
            <p className="eds-type-small font-medium">Вложения</p>
            {bundle.files
              .filter((f) => !editId || pick(f, "entity_id") === editId)
              .map((f) => (
                <div key={pick(f, "id")} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--ew-border)] py-2">
                  <button
                    type="button"
                    className="flex items-center gap-2 text-left"
                    onClick={() => void previewFile(pick(f, "id"), pick(f, "mime_type"))}
                  >
                    {String(pick(f, "mime_type")).startsWith("image/") ? (
                      <img src={legalOpsFileUrl(pick(f, "id"))} alt="" className="h-10 w-10 rounded object-cover" />
                    ) : null}
                    <span className="eds-type-small">
                      {pick(f, "filename")} · {pick(f, "mime_type") || "файл"} ·{" "}
                      {Math.round(Number(f.size || 0) / 1024)} КБ · {pick(f, "created_at") || pick(f, "uploaded_at") || "—"}
                      <br />
                      Объект: {pick(f, "entity_type") || "—"} / {pick(f, "entity_id") || "—"}
                    </span>
                  </button>
                  <span className="flex flex-wrap gap-1">
                    <Button size="sm" variant="ghost" onClick={() => void previewFile(pick(f, "id"), pick(f, "mime_type"))}>
                      Открыть
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => downloadFile(pick(f, "id"), pick(f, "filename"))}>
                      Скачать
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        const name = window.prompt("Новое имя файла", pick(f, "filename"));
                        if (name) void post(`/files/${pick(f, "id")}/rename`, { filename: name });
                      }}
                    >
                      Переименовать
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        const et = window.prompt(
                          "Тип объекта (client/case/contract/document/task/hearing/enforcement/ai_analysis)",
                          pick(f, "entity_type") || editKind || "case",
                        );
                        const eid = window.prompt("ID объекта", pick(f, "entity_id") || editId || "");
                        if (et && eid) void post(`/files/${pick(f, "id")}/link`, { entity_type: et, entity_id: eid });
                      }}
                    >
                      Перепривязать
                    </Button>
                    <label className="eds-type-small">
                      Заменить версию
                      <input
                        type="file"
                        className="block"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) void replaceFile(pick(f, "id"), file);
                        }}
                      />
                    </label>
                    <Button size="sm" variant="ghost" onClick={() => void archiveKind("file", pick(f, "id"))}>
                      Удалить
                    </Button>
                  </span>
                </div>
              ))}
          </div>
          </div>
        </Card>
      ) : null}
      <Card title="Файлы">
        <p className="eds-type-caption mt-1">PDF, DOC, DOCX, JPG, PNG. Превью по клику.</p>
      </Card>
      {previewUrl ? (
        <Card title="Просмотр">
          <img src={previewUrl} alt="preview" className="max-h-80 rounded-md" data-testid="lawyer-file-preview" />
          <Button size="sm" variant="ghost" onClick={() => setPreviewUrl(null)}>
            Закрыть
          </Button>
        </Card>
      ) : null}
      {pdfPreviewUrl ? (
        <Card title="Просмотр PDF">
          <iframe title="pdf" src={pdfPreviewUrl} className="h-96 w-full rounded-md" data-testid="lawyer-pdf-preview" />
          <Button size="sm" variant="ghost" onClick={() => setPdfPreviewUrl(null)}>
            Закрыть
          </Button>
        </Card>
      ) : null}
    </>
  );

  const nav = useMemo(
    () =>
      NAV_BASE.map((n) => ({
        ...n,
        hidden: (n.id === "settings" && !caps.canConfigure) || (caps.isCustomer && n.id !== "home"),
      })),
    [caps],
  );

  const contextBadges = (
    <div className="mb-3 flex flex-wrap items-center gap-2" data-testid="lawyer-header-context">
      <span className="rounded-md border border-[var(--ew-border)] px-2 py-0.5 eds-type-small">
        Орг: {orgLabel}
      </span>
      <span className="rounded-md border border-[var(--ew-border)] px-2 py-0.5 eds-type-small">
        Роль: {roleLabel}
      </span>
      <span className="rounded-md border border-[var(--ew-border)] px-2 py-0.5 eds-type-small">
        Legal role: {legalRole}
      </span>
      <Link className="eds-type-small underline" to="/workspace/legal/pilot">
        Пилот Legal
      </Link>
      <label className="eds-type-small">
        Добавить фото документа
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
          capture="environment"
          data-testid="lawyer-photo-input"
          className="mt-1 block"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void uploadSelected(f, editKind || "inbox", editId || undefined);
          }}
        />
      </label>
    </div>
  );

  const sections = useMemo((): Record<string, OpsSection> => {
    const gcalStatus = String(
      bundle.gcal.status || (bundle.dashboard.google_calendar as { status?: string } | undefined)?.status || "needs_config",
    );
    return {
      home: {
        id: "home",
        title: "Кабинет юриста",
        description: "Нагрузка на сегодня — без приветственного баннера.",
        columns: [
          { key: "item", label: "Показатель" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "Заседания сегодня", value: String(cards.hearings_today ?? 0) },
          { label: "Открытые сроки", value: String(cards.open_deadlines ?? 0) },
          { label: "Ожидают согласования", value: String(cards.pending_approvals ?? 0) },
          { label: "Открытые дела", value: String(cards.open_cases ?? 0) },
        ],
        rows: [
          { item: "Клиенты", value: String(cards.clients ?? bundle.clients.length) },
          { item: "Google Calendar", value: gcalStatus },
        ],
        quickActions: caps.canCreate
          ? [
              { label: "Создать клиента", onClick: () => setPanel("client") },
              { label: "Создать дело", onClick: () => setPanel("case") },
              { label: "Создать договор", onClick: () => setPanel("contract") },
            ]
          : [],
        panel: (
          <>
            {contextBadges}
            {extraPanels}
            {clientPanel}
            {casePanel}
            {contractPanel}
          </>
        ),
        emptyTitle: "Нет операционных данных",
        emptyDescription: "Создайте клиента или дело — данные сохраняются в Postgres.",
        emptyCtaLabel: caps.canCreate ? "Создать клиента" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("client") : undefined,
      },
      clients: {
        id: "clients",
        title: "Клиенты",
        description: "Картотека: физлица и юрлица.",
        columns: [
          { key: "name", label: "Имя" },
          { key: "client_type", label: "Тип" },
          { key: "phone", label: "Телефон" },
          { key: "email", label: "Email" },
          { key: "responsible", label: "Ответственный" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.clients
          .filter((r) => {
            const q = clientQuery.q.trim().toLowerCase();
            if (q) {
              const hay = `${pick(r, "name")} ${pick(r, "email")} ${pick(r, "phone")}`.toLowerCase();
              if (!hay.includes(q)) return false;
            }
            if (clientQuery.client_type && pick(r, "client_type") !== clientQuery.client_type) return false;
            if (clientQuery.status && pick(r, "status") !== clientQuery.status) return false;
            if (clientQuery.responsible && pick(r, "responsible") !== clientQuery.responsible) return false;
            if (clientQuery.tag) {
              const tags = Array.isArray(r.tags) ? r.tags.map(String) : String(r.tags || "").split(",");
              if (!tags.some((t) => t.toLowerCase().includes(clientQuery.tag.toLowerCase()))) return false;
            }
            return true;
          })
          .map((r, i) => ({
          id: pick(r, "id") || String(i),
          name: pick(r, "name"),
          client_type: ruStatus(pick(r, "client_type")),
          phone: pick(r, "phone"),
          email: pick(r, "email"),
          responsible: pick(r, "responsible"),
          status: ruStatus(pick(r, "status")),
        })),
        panel: (
          <>
            <div className="mb-2 grid gap-2 sm:grid-cols-5" data-testid="lawyer-client-filters">
              <Input placeholder="Поиск имя/телефон/email" value={clientQuery.q} onChange={(e) => setClientQuery((q) => ({ ...q, q: e.target.value }))} />
              <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={clientQuery.client_type} onChange={(e) => setClientQuery((q) => ({ ...q, client_type: e.target.value }))}>
                <option value="">Все типы</option>
                <option value="person">Физлицо</option>
                <option value="company">Юрлицо</option>
              </select>
              <Input placeholder="Статус" value={clientQuery.status} onChange={(e) => setClientQuery((q) => ({ ...q, status: e.target.value }))} />
              <Input placeholder="Ответственный" value={clientQuery.responsible} onChange={(e) => setClientQuery((q) => ({ ...q, responsible: e.target.value }))} />
              <Input placeholder="Тег" value={clientQuery.tag} onChange={(e) => setClientQuery((q) => ({ ...q, tag: e.target.value }))} />
            </div>
            {extraPanels}
            {clientPanel}
          </>
        ),
        emptyTitle: "Клиентов пока нет",
        emptyDescription: "Создайте первого клиента — физлицо или юрлицо.",
        emptyCtaLabel: caps.canCreate ? "Создать клиента" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("client") : undefined,
        quickActions: caps.canCreate
          ? [{ label: "Создать клиента", onClick: () => setPanel("client") }]
          : [],
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("client", String(row.id))}
                onEdit={() => {
                  setEditKind("client");
                  setEditId(String(row.id));
                  setDetail(bundle.clients.find((c) => pick(c, "id") === String(row.id)) || row);
                  setEditForm({ name: String(row.name || "") });
                }}
                onArchive={() => void archiveKind("client", String(row.id))}
              />
            )
          : undefined,
      },
      cases: {
        id: "cases",
        title: "Дела",
        description: "Дела и статусы.",
        columns: [
          { key: "title", label: "Дело" },
          { key: "case_number", label: "Номер" },
          { key: "status", label: "Статус" },
          { key: "practice_area", label: "Практика" },
        ],
        rows: bundle.cases.map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          case_number: pick(r, "case_number"),
          status: ruStatus(pick(r, "status")),
          practice_area: pick(r, "practice_area"),
        })),
        statusFilterKey: "status",
        quickActions: caps.canCreate ? [{ label: "Создать дело", onClick: () => setPanel("case") }] : [],
        panel: (
          <>
            {casePanel}
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("case", String(row.id))}
                onEdit={() => {
                  const src = bundle.cases.find((c) => pick(c, "id") === String(row.id));
                  setDetail(src || row);
                  setEditKind("case");
                  setEditId(String(row.id));
                  setEditForm({
                    title: String(src?.title || row.title || ""),
                    status: String(src?.status || "open"),
                    notes: String(src?.notes || ""),
                  });
                }}
                onArchive={() => void archiveKind("case", String(row.id))}
              />
            )
          : undefined,
        emptyTitle: "Пока нет дел",
        emptyCtaLabel: caps.canCreate ? "Создать дело" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("case") : undefined,
      },
      contracts: {
        id: "contracts",
        title: "Договоры",
        description: "Черновики и согласования.",
        columns: [
          { key: "title", label: "Договор" },
          { key: "status", label: "Статус" },
          { key: "approval_status", label: "Согласование" },
        ],
        rows: bundle.contracts.map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          status: ruStatus(pick(r, "status")),
          approval_status: ruStatus(pick(r, "approval_status")),
        })),
        statusFilterKey: "approval_status",
        quickActions: caps.canCreate
          ? [{ label: "Создать договор", onClick: () => setPanel("contract") }]
          : [],
        panel: (
          <>
            {contractPanel}
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("contract", String(row.id))}
                onEdit={() => {
                  const src = bundle.contracts.find((c) => pick(c, "id") === String(row.id));
                  setDetail(src || row);
                  setEditKind("contract");
                  setEditId(String(row.id));
                  setEditForm({
                    title: String(src?.title || row.title || ""),
                    notes: String(src?.notes || ""),
                    status: String(src?.status || "draft"),
                  });
                }}
                onArchive={() => void archiveKind("contract", String(row.id))}
                extra={
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => void post(`/contracts/${row.id}`, { approval_status: "approved" })}
                  >
                    Согласовать
                  </Button>
                }
              />
            )
          : undefined,
        emptyTitle: "Пока нет договоров",
        emptyCtaLabel: caps.canCreate ? "Создать договор" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("contract") : undefined,
      },
      documents: {
        id: "documents",
        title: "Документы",
        description: "Метаданные и storage ref (не Telegram-only).",
        columns: [
          { key: "title", label: "Документ" },
          { key: "doc_type", label: "Тип" },
          { key: "status", label: "Статус" },
          { key: "storage_ref", label: "Storage" },
        ],
        rows: bundle.documents.map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          doc_type: pick(r, "doc_type"),
          status: ruStatus(pick(r, "status")),
          storage_ref: pick(r, "storage_ref"),
        })),
        quickActions: caps.canCreate
          ? [
              { label: "Загрузить документ", onClick: () => setPanel("document") },
              { label: "Добавить фото документа", onClick: () => setPanel("document") },
            ]
          : [],
        panel: (
          <>
            {documentPanel}
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("document", String(row.id))}
                onEdit={() => {
                  setEditKind("document");
                  setEditId(String(row.id));
                  setDetail(bundle.documents.find((d) => pick(d, "id") === String(row.id)) || row);
                }}
                onArchive={() => void archiveKind("document", String(row.id))}
                extra={
                  <Button size="sm" variant="ghost" onClick={() => setPanel("ai")}>
                    AI-анализ
                  </Button>
                }
              />
            )
          : undefined,
        emptyTitle: "Пока нет документов",
        emptyCtaLabel: caps.canCreate ? "Загрузить документ" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("document") : undefined,
      },
      tasks: {
        id: "tasks",
        title: "Задачи / сроки",
        description: "Рабочий legal task manager.",
        columns: [
          { key: "title", label: "Задача" },
          { key: "priority", label: "Приоритет" },
          { key: "due_at", label: "Срок" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.tasks
          .filter((r) => {
            const due = pick(r, "due_at");
            const st = pick(r, "status");
            const now = new Date();
            const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const endToday = new Date(startToday);
            endToday.setDate(endToday.getDate() + 1);
            const endWeek = new Date(startToday);
            endWeek.setDate(endWeek.getDate() + 7);
            const dueDate = due && due !== "—" ? new Date(due) : null;
            if (taskView === "done") return st === "done" || st === "completed";
            if (taskView === "overdue") return Boolean(dueDate && dueDate < startToday && st !== "done" && st !== "completed" && st !== "cancelled");
            if (taskView === "today") return Boolean(dueDate && dueDate >= startToday && dueDate < endToday);
            if (taskView === "week") return Boolean(dueDate && dueDate >= startToday && dueDate < endWeek);
            return true;
          })
          .map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          priority: ruStatus(pick(r, "priority")),
          due_at: pick(r, "due_at"),
          status: ruStatus(pick(r, "status")),
        })),
        quickActions: caps.canCreate
          ? [{ label: "Создать задачу", onClick: () => setPanel("task") }]
          : [],
        panel: (
          <>
            <div className="mb-2 flex flex-wrap gap-2" data-testid="lawyer-task-views">
              {TASK_VIEWS.map((v) => (
                <Button key={v.id} size="sm" variant={taskView === v.id ? "secondary" : "ghost"} onClick={() => setTaskView(v.id)}>
                  {v.label}
                </Button>
              ))}
            </div>
            {taskPanel}
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => void openEntity("task", String(row.id))}>
                  Открыть
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    const t = bundle.tasks.find((x) => pick(x, "id") === String(row.id));
                    setEditKind("task");
                    setEditId(String(row.id));
                    setDetail(t || row);
                    setEditForm({
                      title: pick(t || row, "title"),
                      status: pick(t || row, "status"),
                      priority: pick(t || row, "priority"),
                      due_at: pick(t || row, "due_at"),
                    });
                  }}
                >
                  Изменить
                </Button>
                {String(row.status) !== "Выполнена" && String(row.status) !== "done" ? (
                  <Button size="sm" variant="ghost" onClick={() => void post(`/tasks/${row.id}/complete`, {})}>
                    Выполнить
                  </Button>
                ) : null}
                <Button size="sm" variant="ghost" onClick={() => void archiveKind("task", String(row.id))}>
                  Удалить
                </Button>
              </div>
            )
          : undefined,
        emptyTitle: "Задач пока нет",
        emptyCtaLabel: caps.canCreate ? "Создать задачу" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("task") : undefined,
      },
      hearings: {
        id: "hearings",
        title: "Суды / заседания",
        description: "Внутреннее ведение заседаний (без госреестров).",
        columns: [
          { key: "title", label: "Заседание" },
          { key: "court_name", label: "Суд" },
          { key: "judge", label: "Судья" },
          { key: "scheduled_at", label: "Когда" },
          { key: "hearing_format", label: "Формат" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.hearings.map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          court_name: pick(r, "court_name"),
          judge: pick(r, "judge"),
          scheduled_at: pick(r, "scheduled_at"),
          hearing_format: ruStatus(pick(r, "hearing_format")),
          status: ruStatus(pick(r, "status")),
        })),
        quickActions: caps.canCreate
          ? [{ label: "Создать заседание", onClick: () => setPanel("hearing") }]
          : [],
        panel: (
          <>
            {hearingPanel}
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("hearing", String(row.id))}
                onEdit={() => {
                  setEditKind("hearing");
                  setEditId(String(row.id));
                  setDetail(bundle.hearings.find((h) => pick(h, "id") === String(row.id)) || row);
                }}
                onArchive={() => void archiveKind("hearing", String(row.id))}
                extra={
                  pick(bundle.hearings.find((h) => pick(h, "id") === String(row.id)) || {}, "case_id") !== "—" ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        const h = bundle.hearings.find((x) => pick(x, "id") === String(row.id));
                        if (h?.case_id) void openEntity("case", String(h.case_id));
                      }}
                    >
                      Открыть дело
                    </Button>
                  ) : null
                }
              />
            )
          : undefined,
        emptyTitle: "Заседаний пока нет",
        emptyCtaLabel: caps.canCreate ? "Создать заседание" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("hearing") : undefined,
      },
      monitoring: {
        id: "monitoring",
        title: "Мониторинг",
        description: "Судебные дела, решения, ИП, изменения и источники (честные статусы провайдеров).",
        columns: [
          { key: "external_case_number", label: "Номер" },
          { key: "provider", label: "Provider" },
          { key: "status", label: "Статус" },
          { key: "last_checked_at", label: "Проверка" },
        ],
        rows: [],
        panel: monitoringPanel,
        emptyTitle: "Мониторинг",
      },
      calendar: {
        id: "calendar",
        title: "Календарь",
        description: `Физический календарь · Google: ${gcalStatus} (без фиктивной синхронизации)`,
        columns: [
          { key: "title", label: "Событие" },
          { key: "starts_at", label: "Начало" },
          { key: "event_type", label: "Тип" },
          { key: "sync_status", label: "Синхронизация" },
        ],
        rows: bundle.calendar.map((r, i) => ({
          id: pick(r, "id") || String(i),
          title: pick(r, "title"),
          starts_at: pick(r, "starts_at"),
          event_type: ruStatus(pick(r, "event_type")),
          sync_status: ruStatus(pick(r, "sync_status")),
        })),
        quickActions: caps.canCreate
          ? [{ label: "Создать событие", onClick: () => setPanel("calendar") }]
          : [],
        panel: (
          <>
            {calendarPanel}
            {extraPanels}
            <LawyerCalendarBoard
              events={bundle.calendar}
              clients={bundle.clients}
              cases={bundle.cases}
              canCreate={caps.canCreate}
              onCreate={(iso) => {
                setCalForm((f) => ({ ...f, starts_at: iso, ends_at: iso }));
                setPanel("calendar");
              }}
              onOpen={(ev) => void openEntity("calendar", pick(ev, "id"))}
              onEdit={(ev) => {
                setEditKind("calendar");
                setEditId(pick(ev, "id"));
                setDetail(ev);
                setEditForm({ title: pick(ev, "title"), status: pick(ev, "sync_status") });
              }}
              onArchive={(ev) => void archiveKind("calendar", pick(ev, "id"))}
              onSyncGoogle={(ev) => void post(`/calendar/${pick(ev, "id")}/sync-google`, {})}
              onOpenRelated={(kind, id) => void openEntity(kind, id)}
            />
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <LawyerRowMenu
                row={row}
                onOpen={() => void openEntity("calendar", String(row.id))}
                onEdit={() => {
                  setEditKind("calendar");
                  setEditId(String(row.id));
                  setDetail(bundle.calendar.find((c) => pick(c, "id") === String(row.id)) || row);
                }}
                onArchive={() => void archiveKind("calendar", String(row.id))}
              />
            )
          : undefined,
        integrationNote:
          gcalStatus === "needs_config" || gcalStatus === "needs_oauth"
            ? "Google Calendar: требуется настройка Google OAuth (честный статус)."
            : `Google Calendar: ${ruStatus(gcalStatus)}`,
        emptyTitle: "Пока нет событий",
        emptyCtaLabel: caps.canCreate ? "Создать событие" : undefined,
        emptyCtaOnClick: caps.canCreate ? () => setPanel("calendar") : undefined,
      },
      inbox: {
        id: "inbox",
        title: "Входящие",
        description: "Файлы без привязки к клиенту / делу / договору.",
        columns: [
          { key: "filename", label: "Файл" },
          { key: "mime_type", label: "Тип" },
          { key: "uploaded_by", label: "Автор" },
          { key: "created_at", label: "Дата" },
        ],
        rows: bundle.inbox.map((r, i) => ({
          id: pick(r, "id") || String(i),
          filename: pick(r, "filename"),
          mime_type: pick(r, "mime_type"),
          uploaded_by: pick(r, "uploaded_by"),
          created_at: pick(r, "created_at"),
        })),
        panel: extraPanels,
        rowActions: caps.canOperate
          ? (row) => (
              <div className="flex flex-wrap gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    const cid = bundle.clients[0] ? pick(bundle.clients[0], "id") : "";
                    if (cid) void post(`/files/${row.id}/link`, { entity_type: "client", entity_id: cid });
                  }}
                >
                  Привязать к клиенту
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    const cid = bundle.cases[0] ? pick(bundle.cases[0], "id") : "";
                    if (cid) void post(`/files/${row.id}/link`, { entity_type: "case", entity_id: cid });
                  }}
                >
                  Привязать к делу
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    const cid = bundle.contracts[0] ? pick(bundle.contracts[0], "id") : "";
                    if (cid) void post(`/files/${row.id}/link`, { entity_type: "contract", entity_id: cid });
                  }}
                >
                  Привязать к договору
                </Button>
                <Button size="sm" variant="ghost" onClick={() => void archiveKind("file", String(row.id))}>
                  Архивировать
                </Button>
              </div>
            )
          : undefined,
        emptyTitle: "Входящих нет",
      },
      archive: {
        id: "archive",
        title: "Архив",
        description: "Мягко удалённые дела, договоры, документы и события.",
        columns: [
          { key: "entity_kind", label: "Тип" },
          { key: "title", label: "Название" },
          { key: "archived_at", label: "В архиве" },
        ],
        rows: bundle.archive
          .filter((r) => archiveFilter === "all" || pick(r, "entity_kind") === archiveFilter)
          .map((r, i) => ({
          id: pick(r, "id") || String(i),
          entity_kind: pick(r, "entity_kind"),
          title: pick(r, "title", "name", "filename"),
          archived_at: pick(r, "archived_at"),
        })),
        panel: (
          <>
            <div className="mb-2 flex flex-wrap gap-2" data-testid="lawyer-archive-filters">
              {[
                ["all", "Все"],
                ["case", "Дела"],
                ["contract", "Договоры"],
                ["document", "Документы"],
                ["calendar", "События"],
              ].map(([id, label]) => (
                <Button key={id} size="sm" variant={archiveFilter === id ? "secondary" : "ghost"} onClick={() => setArchiveFilter(id)}>
                  {label}
                </Button>
              ))}
            </div>
            {extraPanels}
          </>
        ),
        rowActions: caps.canOperate
          ? (row) => (
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => void openEntity(String(row.entity_kind), String(row.id))}>
                  Открыть
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  data-testid="lawyer-restore"
                  onClick={() => void restoreKind(String(row.entity_kind), String(row.id))}
                >
                  Восстановить
                </Button>
              </div>
            )
          : undefined,
        emptyTitle: "Архив пуст",
      },
      "ai-analysis": {
        id: "ai-analysis",
        title: "AI-анализ",
        description: "Анализ конкретного объекта или документа. Не путать с AI-юристом.",
        columns: [
          { key: "created_at", label: "Когда" },
          { key: "action", label: "Action" },
          { key: "target_type", label: "Объект" },
          { key: "question", label: "Вопрос" },
        ],
        rows: bundle.aiAnalyses
          .filter((a) => pick(a, "workspace_kind") !== "lawyer")
          .map((a) => ({
            id: pick(a, "id"),
            created_at: pick(a, "created_at"),
            action: pick(a, "action"),
            target_type: pick(a, "target_type"),
            question: pick(a, "question"),
          })),
        panel: aiAnalysisPanel,
        emptyTitle: "Пока нет AI-анализов",
      },
      ai: {
        id: "ai",
        title: "AI-юрист",
        description: "Диалоговый помощник с контекстом клиента/дела; создаёт AI Draft.",
        columns: [
          { key: "created_at", label: "Когда" },
          { key: "mode", label: "Режим" },
          { key: "question", label: "Запрос" },
        ],
        rows: bundle.aiAnalyses
          .filter((a) => pick(a, "workspace_kind") === "lawyer")
          .map((a) => ({
            id: pick(a, "id"),
            created_at: pick(a, "created_at"),
            mode: pick(a, "mode"),
            question: pick(a, "question"),
          })),
        panel: aiPanel,
        emptyTitle: "Пока нет запусков AI-юриста",
      },
      "ai-history": {
        id: "ai-history",
        title: "История AI",
        description: "Сохранённые AI-анализы и запуски AI-юриста.",
        columns: [
          { key: "kind", label: "Тип" },
          { key: "when", label: "Когда" },
          { key: "q", label: "Запрос" },
        ],
        rows: bundle.aiAnalyses.map((a) => ({
          id: pick(a, "id"),
          kind: pick(a, "workspace_kind") === "lawyer" ? "AI-юрист" : "AI-анализ",
          when: pick(a, "created_at"),
          q: pick(a, "question"),
        })),
        panel: aiHistoryPanel,
        emptyTitle: "История пуста",
      },
      activity: {
        id: "activity",
        title: "Активность",
        description: "Журнал действий кабинета.",
        columns: [
          { key: "created_at", label: "Когда" },
          { key: "actor_role", label: "Кто" },
          { key: "action", label: "Действие" },
          { key: "summary", label: "Сводка" },
          { key: "entity_type", label: "Объект" },
        ],
        rows: bundle.activity.map((a, i) => ({
          id: pick(a, "id") || String(i),
          created_at: pick(a, "created_at"),
          actor_role: pick(a, "actor_role", "actor_id") || "—",
          action: pick(a, "action"),
          summary: pick(a, "summary"),
          entity_type: pick(a, "entity_type"),
        })),
        emptyTitle: "Пока нет активности",
      },
      settings: {
        id: "settings",
        title: "Настройки",
        description: "Интеграции и роли Lawyer Desk.",
        columns: [
          { key: "item", label: "Параметр" },
          { key: "value", label: "Значение" },
        ],
        rows: [
          { item: "API Legal Ops", value: "/api/legal-ops/v1" },
          { item: "Организация", value: orgLabel },
          { item: "Роль интерфейса", value: roleLabel },
          { item: "Роль Legal Ops", value: legalRole },
          { item: "Google Calendar", value: ruStatus(gcalStatus) },
          ...bundle.integrations.map((p) => ({
            item: pick(p, "label_ru", "provider"),
            value: ruStatus(pick(p, "status")),
          })),
        ],
        panel: (
          <div data-testid="lawyer-calendar-integrations" className="grid gap-3">
            <IntegrationHealthCard
              headers={headers}
              onConnectGoogle={() => void post("/integrations/google-calendar/connect", {})}
              onDisconnectGoogle={() => void post("/integrations/google-calendar/disconnect", {})}
            />
            <Card title="Источники данных">
              <div data-testid="lawyer-settings-sources" className="grid gap-2">
                <p className="eds-type-small text-[var(--ew-muted)]">
                  Статусы внешних источников. Секреты не отображаются.
                </p>
                {(
                  [
                    {
                      name: "Google Calendar",
                      status: ruStatus(gcalStatus),
                      hint:
                        gcalStatus === "needs_config"
                          ? "Не настроен администратором"
                          : gcalStatus === "needs_oauth"
                            ? "Требуется авторизация Google"
                            : "Готов к синхронизации ADOS → Google",
                    },
                    {
                      name: "Судебные данные",
                      status: "Не подключено",
                      hint: "Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник данных.",
                    },
                    {
                      name: "Исполнительные производства",
                      status: "Не подключено",
                      hint: "Требуется настройка лицензированного провайдера.",
                    },
                    {
                      name: "Ручной импорт",
                      status: "Доступно",
                      hint: "Создание объектов мониторинга и проверка по импортированному состоянию.",
                    },
                  ] as const
                ).map((row) => (
                  <div key={row.name} className="rounded-md border border-[var(--ew-border)] p-3">
                    <div className="font-medium">
                      ● {row.name}: {row.status}
                    </div>
                    <div className="eds-type-small text-[var(--ew-muted)]">{row.hint}</div>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Интеграции → Календари">
              {bundle.integrations.map((p) => (
                <div key={pick(p, "provider")} className="mb-3 rounded-md border border-[var(--ew-border)] p-3">
                  <div className="font-medium">{pick(p, "label_ru", "provider")}</div>
                  <div className="eds-type-small">{pick(p, "message_ru")}</div>
                  <div className="eds-type-small">Статус: {ruStatus(pick(p, "status"))}</div>
                  {pick(p, "provider") === "google" ? (
                    <Button
                      size="sm"
                      className="mt-2"
                      onClick={() => void post("/integrations/google-calendar/connect", {})}
                    >
                      Подключить
                    </Button>
                  ) : null}
                </div>
              ))}
            </Card>
          </div>
        ),
      },
    };
  }, [
    bundle,
    caps,
    cards,
    clientPanel,
    casePanel,
    contractPanel,
    documentPanel,
    taskPanel,
    hearingPanel,
    extraPanels,
    calendarPanel,
    aiPanel,
    aiAnalysisPanel,
    aiHistoryPanel,
    monitoringPanel,
    contextBadges,
    orgLabel,
    roleLabel,
    legalRole,
    archiveFilter,
    clientQuery,
    taskView,
    headers,
  ]);

  return (
    <>
      {extraPanels}
      <BusinessCabinetShell
      verticalId="legal"
      title="Юридический отдел"
      subtitle={`${orgLabel} · ${roleLabel} · CRM · дела · договоры`}
      nav={nav}
      sections={sections}
      defaultSection="home"
      loading={loading}
      error={error}
      onRefresh={() => void load()}
      testId="lawyer-business-cabinet"
      roleHint={caps.roleLabel}
    />
    </>
  );
}
