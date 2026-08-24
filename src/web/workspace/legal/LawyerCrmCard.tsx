/**
 * Lawyer 3.1 — tabbed client/case CRM card with related entities.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { legalOpsFileUrl, legalOpsGet, pick } from "../business-ops/opsApi";
import { ruStatus } from "./lawyerLabels";

type Row = Record<string, unknown>;

const CLIENT_TABS = [
  { id: "overview", label: "Обзор" },
  { id: "cases", label: "Дела" },
  { id: "contracts", label: "Договоры" },
  { id: "documents", label: "Документы" },
  { id: "tasks", label: "Задачи" },
  { id: "hearings", label: "Заседания" },
  { id: "calendar", label: "Календарь" },
  { id: "activity", label: "Активность" },
] as const;

const CASE_TABS = [
  { id: "overview", label: "Обзор" },
  { id: "documents", label: "Документы" },
  { id: "contracts", label: "Договоры" },
  { id: "tasks", label: "Задачи" },
  { id: "hearings", label: "Заседания" },
  { id: "calendar", label: "Календарь" },
  { id: "ai", label: "AI-анализы" },
  { id: "activity", label: "Активность" },
] as const;

export function LawyerCrmCard({
  kind,
  itemId,
  headers,
  editForm,
  onEditChange,
  onSave,
  onClose,
  onArchive,
  onQuick,
  onPreviewFile,
}: {
  kind: "client" | "case";
  itemId: string;
  headers: Record<string, string>;
  editForm: Record<string, string>;
  onEditChange: (key: string, value: string) => void;
  onSave: () => void;
  onClose: () => void;
  onArchive: () => void;
  onQuick: (action: string) => void;
  onPreviewFile?: (fileId: string, mime?: string) => void;
}) {
  const [tab, setTab] = useState("overview");
  const [item, setItem] = useState<Row | null>(null);
  const [related, setRelated] = useState<Record<string, Row[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await legalOpsGet(`/entities/${kind}/${itemId}/related`, headers);
      if (cancelled) return;
      if (!res.ok) {
        setError("Не удалось загрузить карточку");
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

  const tabs = kind === "client" ? CLIENT_TABS : CASE_TABS;
  const fields =
    kind === "client"
      ? [
          ["name", "Имя / название"],
          ["client_type", "Тип (person/company)"],
          ["phone", "Телефон"],
          ["email", "Email"],
          ["address", "Адрес"],
          ["city", "Город"],
          ["country", "Страна"],
          ["company", "Компания"],
          ["position", "Должность"],
          ["responsible", "Ответственный юрист"],
          ["status", "Статус"],
          ["source", "Источник"],
          ["identity_data", "Идентификационные данные"],
          ["tags", "Теги (через запятую)"],
          ["contacts", "Доп. контакты"],
          ["notes", "Заметки"],
        ]
      : [
          ["title", "Название"],
          ["case_number", "Внутренний номер"],
          ["court_case_number", "Номер судебного дела"],
          ["client_id", "Клиент (id)"],
          ["case_type", "Тип дела"],
          ["practice_area", "Практика"],
          ["status", "Статус"],
          ["responsible", "Ответственный"],
          ["participants", "Участники"],
          ["description", "Описание"],
          ["notes", "Заметки"],
          ["opened_at", "Дата открытия"],
          ["deadline_at", "Контрольный срок"],
          ["priority", "Приоритет"],
          ["court", "Суд"],
          ["judge", "Судья"],
        ];

  function listBlock(rows: Row[] | undefined, empty: string) {
    if (!rows?.length) return <p className="eds-type-small text-[var(--eds-text-muted)]">{empty}</p>;
    return (
      <ul className="space-y-1">
        {rows.map((r) => (
          <li key={pick(r, "id")} className="eds-type-small border-b border-[var(--ew-border)] py-1">
            {pick(r, "title", "name", "filename", "summary", "action")} · {ruStatus(pick(r, "status", "event_type", "action"))}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <Card title={kind === "client" ? "Карточка клиента" : "Карточка дела"}>
      <div data-testid="lawyer-crm-card">
        {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
        {item?.avatar_file_id ? (
          <img
            src={legalOpsFileUrl(String(item.avatar_file_id))}
            alt=""
            className="mb-3 h-16 w-16 rounded-md object-cover"
            data-testid="lawyer-client-avatar"
          />
        ) : null}
        <div className="mb-3 flex flex-wrap gap-1" data-testid="lawyer-crm-tabs">
          {tabs.map((t) => (
            <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
              {t.label}
            </Button>
          ))}
        </div>
        {tab === "overview" ? (
          <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-crm-overview">
            {fields.map(([key, label]) => (
              <label key={key} className="eds-type-small">
                {label}
                <Input
                  className="mt-1"
                  value={editForm[key] ?? String(item?.[key] ?? "")}
                  onChange={(e) => onEditChange(key, e.target.value)}
                />
              </label>
            ))}
          </div>
        ) : null}
        {tab === "cases" ? listBlock(related.cases, "Дел пока нет") : null}
        {tab === "contracts" ? listBlock(related.contracts, "Договоров пока нет") : null}
        {tab === "documents" ? listBlock(related.documents, "Документов пока нет") : null}
        {tab === "tasks" ? listBlock(related.tasks, "Задач пока нет") : null}
        {tab === "hearings" ? listBlock(related.hearings, "Заседаний пока нет") : null}
        {tab === "calendar" ? listBlock(related.calendar, "Событий пока нет") : null}
        {tab === "activity" ? listBlock(related.activity, "Активности пока нет") : null}
        {tab === "ai" ? listBlock(related.ai, "AI-анализов пока нет") : null}
        {tab === "overview" && related.files?.length ? (
          <div className="mt-3">
            <p className="eds-type-small font-medium">Вложения</p>
            {related.files.map((f) => (
              <button
                key={pick(f, "id")}
                type="button"
                className="block eds-type-small underline"
                onClick={() => onPreviewFile?.(pick(f, "id"), pick(f, "mime_type"))}
              >
                {pick(f, "filename")}
              </button>
            ))}
          </div>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <Button size="sm" data-testid="lawyer-crm-save" onClick={onSave}>
            Редактировать
          </Button>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Закрыть
          </Button>
          <Button size="sm" variant="ghost" onClick={onArchive}>
            Архивировать
          </Button>
          {kind === "case" ? (
            <>
              <Button size="sm" variant="ghost" onClick={() => onQuick("document")}>
                Добавить документ
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onQuick("task")}>
                Создать задачу
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onQuick("hearing")}>
                Создать заседание
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onQuick("calendar")}>
                Создать событие
              </Button>
            </>
          ) : (
            <Button size="sm" variant="ghost" onClick={() => onQuick("case")}>
              Создать дело
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
