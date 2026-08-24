/**
 * AGRO Production 1.0 — counterparty / deal dossier drawer.
 */

import { useEffect, useState } from "react";
import { Button } from "@/ui";
import { agroOpsFileUrl, agroOpsGet, pick } from "../business-ops/opsApi";
import { CP_STATUSES, ru, ruStatus, typesRu } from "./agroLabels";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "contacts", label: "Контакты" },
  { id: "deals", label: "Сделки" },
  { id: "contracts", label: "Договоры" },
  { id: "documents", label: "Документы" },
  { id: "payments", label: "Платежи" },
  { id: "calculations", label: "Расчёты" },
  { id: "shipments", label: "Поставки" },
  { id: "tasks", label: "Задачи" },
  { id: "notes", label: "Заметки" },
  { id: "activity", label: "История" },
] as const;

function titleOf(r: Row): string {
  return String(pick(r, "title", "name", "full_name", "filename", "summary") || pick(r, "id"));
}

export function AgroDossierDrawer({
  kind,
  itemId,
  headers,
  canOperate,
  onClose,
  onHandoff,
}: {
  kind: "counterparty" | "deal";
  itemId: string;
  headers: Record<string, string>;
  canOperate: boolean;
  onClose: () => void;
  onHandoff?: (view: string, prefill?: Record<string, string>) => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("overview");
  const [item, setItem] = useState<Row | null>(null);
  const [related, setRelated] = useState<Record<string, Row[]>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await agroOpsGet(`/entities/${kind}/${itemId}/related`, headers);
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

  function list(rows: Row[] | undefined, empty: string) {
    if (!rows?.length) return <p className="eds-type-small text-[var(--ew-muted)]">{empty}</p>;
    return (
      <ul className="eds-type-small">
        {rows.slice(0, 20).map((r) => (
          <li key={pick(r, "id")} className="border-b border-[var(--ew-border)] py-1">
            {titleOf(r)} · {ruStatus(pick(r, "status"))}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 w-full max-w-xl overflow-y-auto border-l border-[var(--ew-border)] bg-[var(--eds-surface,var(--ew-surface,#0f1420))] p-4 shadow-xl"
      data-testid="agro-dossier-drawer"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="eds-type-small text-[var(--ew-muted)]">{kind === "counterparty" ? "Контрагент" : "Сделка"}</p>
          <h3 className="font-semibold">{item ? titleOf(item) : "Загрузка…"}</h3>
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}>
          Закрыть
        </Button>
      </div>
      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
      <div className="mb-3 flex flex-wrap gap-1" data-testid="agro-dossier-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {tab === "overview" && item ? (
        <dl className="grid gap-1 eds-type-small" data-testid="agro-dossier-overview">
          {kind === "counterparty" ? (
            <>
              <div>Роли: {typesRu(item.types)}</div>
              <div>Статус: {ru(CP_STATUSES, String(item.status || ""))}</div>
              <div>Страна: {String(item.country || "—")}</div>
              <div>Регион: {String(item.region || "—")}</div>
              <div>Город: {String(item.city || "—")}</div>
              <div>Телефон: {String(item.phone || "—")}</div>
              <div>Эл. почта: {String(item.email || "—")}</div>
              <div>Ответственный: {String(item.responsible || "—")}</div>
              <div>Валюта: {String(item.preferred_currency || "—")}</div>
              <div>Заметки: {String(item.notes || "—")}</div>
            </>
          ) : (
            <>
              <div>Культура: {String(item.crop || item.product || "—")}</div>
              <div>Сторона: {item.side === "sell" ? "Продажа" : "Закупка"}</div>
              <div>
                Количество: {String(item.quantity || "—")} {String(item.unit || "")}
              </div>
              <div>
                Цена: {String(item.price || "—")} {String(item.currency || "")}
              </div>
              <div>Статус: {ru(DEAL_STATUSES, String(item.status || ""))}</div>
              <div>Условия поставки: {String(item.incoterms || "—")}</div>
              <div>
                Маржа:{" "}
                {related.margin && typeof related.margin === "object" && !Array.isArray(related.margin)
                  ? `${String((related.margin as Row).gross_profit ?? "—")} (${String((related.margin as Row).margin_pct ?? "—")}%)`
                  : "Нет данных"}
              </div>
              <div>Заметки: {String(item.notes || "—")}</div>
            </>
          )}
        </dl>
      ) : null}
      {tab === "contacts" ? list(related.contacts, "Контактов пока нет") : null}
      {tab === "deals" ? list(related.deals, "Сделок пока нет") : null}
      {tab === "contracts" ? list(related.contracts, "Договоров пока нет") : null}
      {tab === "documents" ? (
        <div>
          {list(related.documents, "Документов пока нет")}
          {(related.files || []).map((f) => (
            <a key={pick(f, "id")} className="block eds-type-small underline" href={agroOpsFileUrl(pick(f, "id"))} target="_blank" rel="noreferrer">
              {pick(f, "filename")}
            </a>
          ))}
        </div>
      ) : null}
      {tab === "calculations" ? list(related.calculations, "Расчётов пока нет") : null}
      {tab === "payments" ? list(related.payments || related.invoices, "Платежей пока нет") : null}
      {tab === "shipments" ? list(related.shipments, "Поставок пока нет") : null}
      {tab === "tasks" ? list(related.tasks, "Задач пока нет") : null}
      {tab === "notes" ? list(related.notes, "Заметок пока нет") : null}
      {tab === "activity" ? list(related.activity, "Истории пока нет") : null}
      {canOperate && onHandoff ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <Button size="sm" variant="ghost" onClick={() => onHandoff("calculations", { counterparty_id: kind === "counterparty" ? itemId : String(item?.counterparty_id || ""), deal_id: kind === "deal" ? itemId : "" })}>
            Сделать расчёт
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onHandoff("documents", { entity_id: itemId, entity_type: kind })}>
            Прикрепить файл
          </Button>
        </div>
      ) : null}
    </div>
  );
}
