/**
 * Sprint Lawyer 3.6 — common entity detail drawer.
 * Open details for client/case/contract/document/task/hearing without
 * losing the current list context. Tabs: Обзор / Файлы / Связи / Активность.
 */

import { useEffect, useState } from "react";
import { Button } from "@/ui";
import { legalOpsGet, pick } from "../business-ops/opsApi";
import { ruStatus } from "./lawyerLabels";

type Row = Record<string, unknown>;

export type DrawerKind = "client" | "case" | "contract" | "document" | "task" | "hearing";

export type AiHandoffContext = {
  clientId?: string;
  caseId?: string;
  contractId?: string;
  hearingId?: string;
  changeId?: string;
  documentIds?: string[];
  contextLabels?: string[];
};

const KIND_TITLES: Record<DrawerKind, string> = {
  client: "Клиент",
  case: "Дело",
  contract: "Договор",
  document: "Документ",
  task: "Задача",
  hearing: "Заседание",
};

const OVERVIEW_FIELDS: Record<DrawerKind, [string, string][]> = {
  client: [
    ["name", "Имя / название"],
    ["client_type", "Тип"],
    ["phone", "Телефон"],
    ["email", "Email"],
    ["responsible", "Ответственный юрист"],
    ["status", "Статус"],
    ["notes", "Заметки"],
  ],
  case: [
    ["title", "Название"],
    ["case_number", "Номер"],
    ["court_case_number", "Номер судебного дела"],
    ["status", "Статус"],
    ["practice_area", "Практика"],
    ["responsible", "Ответственный юрист"],
    ["court", "Суд"],
    ["judge", "Судья"],
    ["deadline_at", "Контрольный срок"],
    ["notes", "Заметки"],
  ],
  contract: [
    ["title", "Название"],
    ["contract_number", "Номер"],
    ["status", "Статус"],
    ["counterparty", "Контрагент"],
    ["amount", "Сумма"],
    ["deadline_at", "Срок"],
    ["responsible", "Ответственный"],
    ["notes", "Заметки"],
  ],
  document: [
    ["title", "Название"],
    ["doc_type", "Тип"],
    ["status", "Статус"],
    ["description", "Описание"],
  ],
  task: [
    ["title", "Название"],
    ["kind", "Вид"],
    ["status", "Статус"],
    ["priority", "Приоритет"],
    ["due_at", "Срок"],
    ["assignee", "Исполнитель"],
    ["description", "Описание"],
  ],
  hearing: [
    ["title", "Название"],
    ["court_name", "Суд"],
    ["court_case_number", "Номер судебного дела"],
    ["judge", "Судья"],
    ["scheduled_at", "Дата и время"],
    ["room", "Зал"],
    ["location", "Адрес"],
    ["description", "Описание"],
  ],
};

const RELATION_SECTIONS: { key: string; label: string; kind?: DrawerKind }[] = [
  { key: "clients", label: "Клиент", kind: "client" },
  { key: "cases", label: "Дела", kind: "case" },
  { key: "contracts", label: "Договоры", kind: "contract" },
  { key: "documents", label: "Документы", kind: "document" },
  { key: "tasks", label: "Задачи / сроки", kind: "task" },
  { key: "hearings", label: "Заседания", kind: "hearing" },
  { key: "calendar", label: "Календарь" },
  { key: "monitoring", label: "Мониторинг" },
  { key: "changes", label: "Изменения мониторинга" },
  { key: "ai", label: "AI-анализы" },
];

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "files", label: "Файлы" },
  { id: "links", label: "Связи" },
  { id: "activity", label: "Активность" },
] as const;

function rowTitle(r: Row): string {
  return String(
    pick(r, "title", "name", "filename", "summary", "question", "action") || pick(r, "id"),
  );
}

export function LawyerDetailDrawer({
  kind,
  itemId,
  headers,
  canOperate,
  onClose,
  onNavigate,
  onEdit,
  onArchive,
  onHandoffAi,
  onPreviewFile,
}: {
  kind: DrawerKind;
  itemId: string;
  headers: Record<string, string>;
  canOperate: boolean;
  onClose: () => void;
  onNavigate: (kind: DrawerKind, id: string) => void;
  onEdit?: (kind: DrawerKind, id: string) => void;
  onArchive?: (kind: DrawerKind, id: string) => void;
  onHandoffAi?: (ctx: AiHandoffContext) => void;
  onPreviewFile?: (fileId: string, mime?: string) => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("overview");
  const [item, setItem] = useState<Row | null>(null);
  const [related, setRelated] = useState<Record<string, Row[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setItem(null);
    setError(null);
    (async () => {
      const res = await legalOpsGet(`/entities/${kind}/${itemId}/related`, headers);
      if (cancelled) return;
      if (!res.ok) {
        setError("Не удалось загрузить карточку объекта");
        return;
      }
      const body = res.json as { item?: Row; related?: Record<string, Row[]> };
      setItem(body.item || null);
      setRelated(body.related || {});
    })();
    return () => {
      cancelled = true;
    };
  }, [kind, itemId, headers]);

  function buildHandoff(): AiHandoffContext {
    const caseId =
      kind === "case" ? itemId : String(item?.case_id || (related.cases?.[0] ? pick(related.cases[0], "id") : "") || "");
    const clientId =
      kind === "client" ? itemId : String(item?.client_id || (related.clients?.[0] ? pick(related.clients[0], "id") : "") || "");
    const documentIds =
      kind === "document" ? [itemId] : (related.documents || []).slice(0, 10).map((d) => pick(d, "id"));
    const labels: string[] = [];
    if (kind !== "client" && kind !== "case") labels.push(`${KIND_TITLES[kind]} ${rowTitle(item || {})}`);
    if (caseId) {
      const c = kind === "case" ? item : related.cases?.find((x) => pick(x, "id") === caseId);
      labels.push(`Дело ${c ? rowTitle(c) : caseId}`);
    }
    if (clientId) {
      const c = kind === "client" ? item : related.clients?.find((x) => pick(x, "id") === clientId);
      labels.push(`Клиент ${c ? rowTitle(c) : clientId}`);
    }
    if (documentIds.length) labels.push(`${documentIds.length} документ(ов)`);
    if (related.changes?.length) labels.push(`${related.changes.length} изменение(й) мониторинга`);
    return {
      caseId: caseId || undefined,
      clientId: clientId || undefined,
      contractId: kind === "contract" ? itemId : undefined,
      hearingId: kind === "hearing" ? itemId : undefined,
      documentIds,
      contextLabels: labels,
    };
  }

  const files = related.files || [];
  const activity = related.activity || [];

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 w-full max-w-xl overflow-y-auto border-l border-[var(--ew-border)] bg-[var(--eds-surface,var(--ew-surface,#0f1420))] p-4 shadow-xl"
      data-testid="lawyer-detail-drawer"
      role="dialog"
      aria-label={`${KIND_TITLES[kind]}: детали`}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="eds-type-small text-[var(--ew-muted)]">{KIND_TITLES[kind]}</p>
          <h3 className="eds-type-heading-sm font-semibold" data-testid="lawyer-drawer-title">
            {item ? rowTitle(item) : "Загрузка…"}
          </h3>
        </div>
        <Button size="sm" variant="ghost" data-testid="lawyer-drawer-close" onClick={onClose}>
          Закрыть
        </Button>
      </div>
      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}

      <div className="mb-3 flex flex-wrap gap-1" data-testid="lawyer-drawer-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "overview" && item ? (
        <dl className="grid gap-1 eds-type-small" data-testid="lawyer-drawer-overview">
          {OVERVIEW_FIELDS[kind].map(([key, label]) => {
            const raw = item[key];
            if (raw === undefined || raw === null || raw === "") return null;
            return (
              <div key={key} className="flex justify-between gap-3 border-b border-[var(--ew-border)] py-1">
                <dt className="text-[var(--ew-muted)]">{label}</dt>
                <dd className="text-right">{key === "status" || key === "client_type" ? ruStatus(String(raw)) : String(raw)}</dd>
              </div>
            );
          })}
        </dl>
      ) : null}

      {tab === "files" ? (
        <div data-testid="lawyer-drawer-files">
          {files.length ? (
            <ul className="space-y-1 eds-type-small">
              {files.map((f) => (
                <li key={pick(f, "id")} className="flex items-center justify-between gap-2 border-b border-[var(--ew-border)] py-1">
                  <span>
                    {pick(f, "filename")} · {ruStatus(pick(f, "mime_type"))}
                  </span>
                  <Button size="sm" variant="ghost" onClick={() => onPreviewFile?.(pick(f, "id"), pick(f, "mime_type"))}>
                    Открыть
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small text-[var(--ew-muted)]">Файлов пока нет</p>
          )}
        </div>
      ) : null}

      {tab === "links" ? (
        <div className="space-y-3" data-testid="lawyer-drawer-links">
          {RELATION_SECTIONS.map((sec) => {
            const rows = related[sec.key] || [];
            if (!rows.length) return null;
            return (
              <div key={sec.key}>
                <p className="eds-type-small font-medium">{sec.label}</p>
                <ul className="eds-type-small">
                  {rows.slice(0, 15).map((r) => (
                    <li key={pick(r, "id")} className="flex items-center justify-between gap-2 border-b border-[var(--ew-border)] py-1">
                      <span>
                        {rowTitle(r)} · {ruStatus(pick(r, "status", "event_type", "change_type", "action"))}
                      </span>
                      {sec.kind ? (
                        <Button size="sm" variant="ghost" onClick={() => onNavigate(sec.kind as DrawerKind, pick(r, "id"))}>
                          Открыть
                        </Button>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
          {!RELATION_SECTIONS.some((sec) => (related[sec.key] || []).length) ? (
            <p className="eds-type-small text-[var(--ew-muted)]">Связанных объектов пока нет</p>
          ) : null}
        </div>
      ) : null}

      {tab === "activity" ? (
        <div data-testid="lawyer-drawer-activity">
          {activity.length ? (
            <ul className="space-y-1 eds-type-small">
              {activity.slice(0, 30).map((a) => (
                <li key={pick(a, "id")} className="border-b border-[var(--ew-border)] py-1">
                  {String(pick(a, "created_at")).slice(0, 16)} · {pick(a, "summary") || ruStatus(pick(a, "action"))}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small text-[var(--ew-muted)]">Активности пока нет</p>
          )}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {onEdit ? (
          <Button size="sm" disabled={!canOperate} onClick={() => onEdit(kind, itemId)}>
            Изменить
          </Button>
        ) : null}
        {onHandoffAi && kind !== "client" && kind !== "task" ? (
          <Button size="sm" variant="ghost" disabled={!canOperate} data-testid="lawyer-drawer-ai-handoff" onClick={() => onHandoffAi(buildHandoff())}>
            Передать AI-юристу
          </Button>
        ) : null}
        {onArchive ? (
          <Button size="sm" variant="ghost" disabled={!canOperate} onClick={() => onArchive(kind, itemId)}>
            Удалить
          </Button>
        ) : null}
      </div>
    </div>
  );
}
