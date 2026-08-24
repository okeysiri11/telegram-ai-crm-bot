/**
 * AGRO 2.1 CRM list — desktop table + mobile cards. Same /crm/list backend.
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet, agroOpsPost } from "../business-ops/opsApi";
import { CP_STATUSES, CP_TYPES, ru, typesRu } from "./agroLabels";

type Row = Record<string, unknown>;

function money(buckets: unknown): string {
  if (!buckets || typeof buckets !== "object") return "Нет данных";
  const entries = Object.entries(buckets as Record<string, number>).filter(([, v]) => v != null && Number(v) !== 0);
  if (!entries.length) return "Нет данных";
  return entries.map(([ccy, v]) => `${ccy} ${Number(v).toLocaleString("ru-RU")}`).join(" · ");
}

const COLS = [
  { id: "name", label: "Контрагент" },
  { id: "types", label: "Тип" },
  { id: "region", label: "Регион" },
  { id: "responsible", label: "Ответственный" },
  { id: "active_deals", label: "Активные сделки" },
  { id: "turnover", label: "Оборот" },
  { id: "receivable", label: "Нам должны" },
  { id: "payable", label: "Мы должны" },
  { id: "last_contact", label: "Последний контакт" },
  { id: "next_task", label: "Следующая задача" },
  { id: "risk", label: "Риск" },
] as const;

export function AgroCrmList(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  canExport: boolean;
  onOpen: (id: string) => void;
  onCreate: () => void;
  onCall?: (phone: string) => void;
}) {
  const mobile = useIsMobile();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [tag, setTag] = useState("");
  const [crop, setCrop] = useState("");
  const [risk, setRisk] = useState("");
  const [debt, setDebt] = useState(false);
  const [overdue, setOverdue] = useState(false);
  const [items, setItems] = useState<Row[]>([]);
  const [analytics, setAnalytics] = useState<Row | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [importText, setImportText] = useState("");
  const [cols, setCols] = useState<string[]>(COLS.map((c) => c.id));

  const query = useMemo(() => {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (status) p.set("status", status);
    if (type) p.set("type", type);
    if (tag) p.set("tag", tag);
    if (crop) p.set("crop", crop);
    if (risk) p.set("risk", risk);
    if (debt) p.set("debt", "1");
    if (overdue) p.set("overdue", "1");
    p.set("limit", "50");
    return p.toString();
  }, [q, status, type, tag, crop, risk, debt, overdue]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await agroOpsGet(`/crm/list?${query}`, props.headers);
      if (cancelled) return;
      const body = res.json as { items?: Row[] };
      setItems(Array.isArray(body.items) ? body.items : []);
    })();
    return () => {
      cancelled = true;
    };
  }, [query, props.headers]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await agroOpsGet("/crm/analytics", props.headers);
      if (cancelled || !res.ok) return;
      setAnalytics((res.json || {}) as Row);
    })();
    return () => {
      cancelled = true;
    };
  }, [props.headers]);

  async function doExport() {
    const res = await agroOpsGet(`/crm/export?${query}`, props.headers);
    const body = res.json as { csv?: string; message_ru?: string };
    if (!res.ok || !body.csv) {
      setMsg(body.message_ru || "Экспорт недоступен");
      return;
    }
    const blob = new Blob([body.csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "agro_crm.csv";
    a.click();
  }

  async function doImport(commit: boolean) {
    const res = await agroOpsPost("/crm/import", { csv: importText, preview: !commit, commit }, props.headers);
    const body = res.json as { message_ru?: string; created?: number; skipped?: number; preview?: boolean; errors?: { message_ru?: string }[] };
    if (!res.ok) {
      setMsg(body.message_ru || "Импорт не выполнен");
      return;
    }
    setMsg(
      body.preview
        ? `Предпросмотр: ${body.errors?.length || 0} замечаний. Подтвердите запись.`
        : `Создано: ${body.created || 0}, пропущено: ${body.skipped || 0}`,
    );
  }

  const visibleCols = COLS.filter((c) => cols.includes(c.id) && (props.canFinance || !["turnover", "receivable", "payable"].includes(c.id)));

  return (
    <div className="space-y-3" data-testid="agro-crm-list">
      {analytics && props.canFinance ? (
        <div className="grid gap-2 sm:grid-cols-4" data-testid="agro-crm-analytics">
          <Card title="Активные контрагенты">
            <p className="eds-type-title">{String(analytics.active_counterparties ?? "Нет данных")}</p>
          </Card>
          <Card title="Новые за 30 дней">
            <p className="eds-type-title">{String(analytics.new_30d ?? "Нет данных")}</p>
          </Card>
          <Card title="Активные сделки">
            <p className="eds-type-title">{String(analytics.active_deals ?? "Нет данных")}</p>
          </Card>
          <Card title="Просрочка">
            <p className="eds-type-title">{String((analytics.aging as Row | undefined)?.overdue_count ?? "Нет данных")}</p>
          </Card>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Поиск: имя, ЕДРПОУ, телефон, email" value={q} onChange={(e) => setQ(e.target.value)} className="min-w-[12rem] flex-1" />
        <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Статус</option>
          {Object.entries(CP_STATUSES).map(([id, l]) => (
            <option key={id} value={id}>
              {l}
            </option>
          ))}
        </select>
        <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">Тип</option>
          {Object.entries(CP_TYPES).map(([id, l]) => (
            <option key={id} value={id}>
              {l}
            </option>
          ))}
        </select>
        <Input placeholder="Тег" value={tag} onChange={(e) => setTag(e.target.value)} className="w-28" />
        <Input placeholder="Культура" value={crop} onChange={(e) => setCrop(e.target.value)} className="w-28" />
        <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={risk} onChange={(e) => setRisk(e.target.value)}>
          <option value="">Risk</option>
          {["LOW", "MEDIUM", "HIGH", "BLOCKED"].map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <label className="eds-type-small flex items-center gap-1">
          <input type="checkbox" checked={debt} onChange={(e) => setDebt(e.target.checked)} /> Есть долг
        </label>
        <label className="eds-type-small flex items-center gap-1">
          <input type="checkbox" checked={overdue} onChange={(e) => setOverdue(e.target.checked)} /> Просрочка
        </label>
        {props.canCreate ? (
          <Button size="sm" onClick={props.onCreate}>
            Создать
          </Button>
        ) : null}
        {props.canExport ? (
          <Button size="sm" variant="secondary" onClick={() => void doExport()}>
            Экспорт
          </Button>
        ) : null}
      </div>
      {!mobile ? (
        <div className="flex flex-wrap gap-2 eds-type-small">
          {COLS.map((c) => (
            <label key={c.id} className="flex items-center gap-1">
              <input type="checkbox" checked={cols.includes(c.id)} onChange={() => setCols((cur) => (cur.includes(c.id) ? cur.filter((x) => x !== c.id) : [...cur, c.id]))} />
              {c.label}
            </label>
          ))}
        </div>
      ) : null}
      {msg ? <p className="eds-type-small text-[var(--ew-danger)]">{msg}</p> : null}
      {props.canCreate ? (
        <details className="eds-type-small">
          <summary>Импорт CSV</summary>
          <textarea className="mt-2 w-full rounded-md border border-[var(--ew-border)] bg-transparent p-2" rows={4} placeholder="name,edrpou,phone,email" value={importText} onChange={(e) => setImportText(e.target.value)} />
          <div className="mt-2 flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => void doImport(false)}>
              Предпросмотр
            </Button>
            <Button size="sm" onClick={() => void doImport(true)}>
              Записать
            </Button>
          </div>
        </details>
      ) : null}
      {mobile ? (
        <ul className="space-y-2" data-testid="agro-crm-cards">
          {items.length === 0 ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
          {items.map((r) => (
            <li key={String(r.id)} className="rounded-lg border border-[var(--ew-border)] p-3">
              <p className="font-semibold">{String(r.name || "—")}</p>
              <p className="eds-type-small text-[var(--ew-muted)]">
                {typesRu(r.types)} · {String(r.region || r.city || "—")}
              </p>
              <p className="eds-type-small">Активных сделок: {String(r.active_deals ?? 0)}</p>
              {props.canFinance ? <p className="eds-type-small">Нам должны: {money(r.receivable)}</p> : null}
              <p className="eds-type-small">Следующий контакт: {String(r.next_task || "Нет данных")}</p>
              <p className="eds-type-small">Менеджер: {String(r.responsible || "—")}</p>
              <div className="mt-2 flex gap-2">
                <Button size="sm" onClick={() => props.onOpen(String(r.id))}>
                  Открыть
                </Button>
                {r.phone ? (
                  <a className="eds-type-small self-center text-[var(--eds-primary)]" href={`tel:${String(r.phone)}`}>
                    Позвонить
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="overflow-x-auto" data-testid="agro-crm-table">
          <table className="w-full text-left eds-type-small">
            <thead>
              <tr>
                {visibleCols.map((c) => (
                  <th key={c.id} className="border-b border-[var(--ew-border)] p-2">
                    {c.label}
                  </th>
                ))}
                <th className="border-b border-[var(--ew-border)] p-2" />
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td className="p-2 text-[var(--ew-muted)]" colSpan={visibleCols.length + 1}>
                    Нет данных
                  </td>
                </tr>
              ) : (
                items.map((r) => (
                  <tr key={String(r.id)} className="cursor-pointer hover:bg-[var(--eds-primary-soft)]/30" onClick={() => props.onOpen(String(r.id))}>
                    {visibleCols.map((c) => (
                      <td key={c.id} className="border-b border-[var(--ew-border)] p-2">
                        {c.id === "types"
                          ? typesRu(r.types)
                          : c.id === "receivable" || c.id === "payable"
                            ? money(r[c.id])
                            : c.id === "turnover"
                              ? r.turnover && typeof r.turnover === "object"
                                ? (r.turnover as { mixed?: boolean; amount?: number; currency?: string }).mixed
                                  ? "Смешанные валюты"
                                  : `${(r.turnover as { currency?: string }).currency || ""} ${Number((r.turnover as { amount?: number }).amount || 0).toLocaleString("ru-RU")}`
                                : "Нет данных"
                              : c.id === "risk"
                                ? String(r.risk || "—")
                                : String(r[c.id] ?? "—")}
                      </td>
                    ))}
                    <td className="border-b border-[var(--ew-border)] p-2">{ru(CP_STATUSES, String(r.status || ""))}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
