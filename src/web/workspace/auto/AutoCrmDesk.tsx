/**
 * AUTO 1.3 — CRM / deals operating desk.
 * Ten-second answers. No employee scoring. No technical admin chrome.
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Button, Card, Input } from "@/ui";
import { asList, autoOpsGet, autoOpsPost, pick } from "../business-ops/opsApi";
import { money } from "./autoLabels";

type Rec = Record<string, unknown>;

const TABS = [
  { id: "all", label: "Все сделки" },
  { id: "leads", label: "Лиды" },
  { id: "active", label: "В работе" },
  { id: "reserved", label: "Резерв" },
  { id: "paying", label: "Оплата" },
  { id: "done", label: "Закрытые" },
  { id: "problems", label: "Проблемные" },
];

const STAGES = [
  "LEAD",
  "CONTACT",
  "VEHICLE_SELECTED",
  "RESERVED",
  "DEPOSIT",
  "CONTRACT",
  "PARTIAL_PAYMENT",
  "FINAL_PAYMENT",
  "HANDOVER",
  "COMPLETED",
];

export function AutoCrmDesk({
  headers,
  canCreate,
  canFinance,
  vehicles,
  clients,
  initialTab = "leads",
  onOpenVehicle,
}: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  vehicles: Rec[];
  clients: Rec[];
  initialTab?: string;
  onOpenVehicle: (id: string) => void;
}) {
  const [tab, setTab] = useState(initialTab);
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Rec[]>([]);
  const [counts, setCounts] = useState<Rec>({});
  const [selected, setSelected] = useState<Rec | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [searchHits, setSearchHits] = useState<Rec[]>([]);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ tab, q });
    const res = await autoOpsGet(`/crm/deals?${params.toString()}`, headers);
    const json = res.json as Rec;
    setItems(asList(json) as Rec[]);
    setCounts((json.counts || {}) as Rec);
  }, [headers, tab, q]);

  useEffect(() => {
    void load();
  }, [load]);

  async function post(path: string, body: Rec): Promise<boolean> {
    const res = await autoOpsPost(path, body, headers);
    const j = res.json as Rec;
    if (!res.ok || j.ok === false) {
      setMsg(String(j.message_ru || j.error || "Операция не выполнена"));
      return false;
    }
    setMsg("Сохранено");
    await load();
    if (selected && path.includes(String(selected.id || ""))) {
      const det = await autoOpsGet(`/crm/deals/${String(selected.id)}`, headers);
      if (det.ok) setSelected({ ...(det.json as Rec), ...((det.json as Rec).item as Rec) });
    }
    return true;
  }

  async function openDeal(id: string) {
    const det = await autoOpsGet(`/crm/deals/${id}`, headers);
    if (det.ok) setSelected({ ...(det.json as Rec), ...((det.json as Rec).item as Rec) });
  }

  async function runSearch(value: string) {
    if (!value.trim()) {
      setSearchHits([]);
      return;
    }
    const res = await autoOpsGet(`/search?q=${encodeURIComponent(value)}`, headers);
    setSearchHits(asList(res.json) as Rec[]);
  }

  return (
    <div className="space-y-4" data-testid="auto-crm-desk">
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
      <Input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          void runSearch(e.target.value);
        }}
        placeholder="VIN, клиент, перевозка, контейнер, BOL"
      />
      {searchHits.length ? (
        <ul className="eds-type-helper" data-testid="auto-search-hits">
          {searchHits.slice(0, 8).map((h) => (
            <li key={`${h.kind}-${h.id}`}>
              {pick(h, "kind")}: {pick(h, "title")} {pick(h, "extra")}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="flex flex-wrap gap-1" data-testid="auto-crm-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? undefined : "secondary"} onClick={() => setTab(t.id)}>
            {t.label}
            {counts[t.id] != null ? ` (${String(counts[t.id])})` : ""}
          </Button>
        ))}
      </div>
      {canCreate ? <CreateDealForm clients={clients} vehicles={vehicles} onSubmit={(body) => post("/crm/deals", body)} /> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        <ul className="space-y-2">
          {items.length ? (
            items.map((d) => (
              <li key={String(d.id)}>
                <button className="w-full rounded border p-3 text-left" onClick={() => void openDeal(String(d.id))}>
                  <strong>{pick(d, "client_name")}</strong>
                  <p className="eds-type-helper">
                    {pick(d, "stage_ru")} · {pick(d, "vehicle_title")}
                  </p>
                </button>
              </li>
            ))
          ) : (
            <p className="eds-type-helper">Сделок пока нет. Пустой список — нет записей, не ошибка.</p>
          )}
        </ul>
        {selected ? (
          <DealPanel selected={selected} canCreate={canCreate} canFinance={canFinance} post={post} onOpenVehicle={onOpenVehicle} />
        ) : (
          <p className="eds-type-helper">Откройте сделку: кто клиент, какая машина, какой этап, сколько должны.</p>
        )}
      </div>
    </div>
  );
}

function CreateDealForm({
  clients,
  vehicles,
  onSubmit,
}: {
  clients: Rec[];
  vehicles: Rec[];
  onSubmit: (body: Rec) => Promise<boolean>;
}) {
  const [clientId, setClientId] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!clientId) return;
    await onSubmit({ client_id: clientId, vehicle_id: vehicleId || undefined, stage: "LEAD", assigned_manager_id: "demo-manager" });
  }
  return (
    <form onSubmit={(e) => void submit(e)} className="flex flex-wrap gap-2">
      <select value={clientId} onChange={(e) => setClientId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Клиент</option>
        {clients.map((c) => (
          <option key={String(c.id)} value={String(c.id)}>
            {pick(c, "name")}
          </option>
        ))}
      </select>
      <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Автомобиль (необязательно)</option>
        {vehicles.map((v) => (
          <option key={String(v.id)} value={String(v.id)}>
            {pick(v, "title") || pick(v, "vin")}
          </option>
        ))}
      </select>
      <Button type="submit" size="sm">
        Новый лид
      </Button>
    </form>
  );
}

function DealPanel({
  selected,
  canCreate,
  canFinance,
  post,
  onOpenVehicle,
}: {
  selected: Rec;
  canCreate: boolean;
  canFinance: boolean;
  post: (path: string, body: Rec) => Promise<boolean>;
  onOpenVehicle: (id: string) => void;
}) {
  const answers = (selected.answers || {}) as Rec;
  const payments = (selected.payments || {}) as Rec;
  const profit = (selected.profit || {}) as Rec;
  const pipeline = asList(selected.pipeline, ["pipeline"]) as Rec[];
  const did = String(selected.id || "");
  const [stage, setStage] = useState(String(selected.stage || "LEAD"));
  const [amount, setAmount] = useState("");
  const showMoney = canFinance || !payments.restricted;

  return (
    <div className="space-y-3" data-testid="auto-deal-panel">
      {selected.is_demo ? <p className="eds-type-caption">DEMO — не продакшен</p> : null}
      <Card title="Сделка за 10 секунд">
        <dl className="grid gap-2" data-testid="auto-deal-answers">
          <QA q="Кто клиент?" a={String(answers.client || "—")} />
          <QA q="Какая машина?" a={String(answers.vehicle || "—")} />
          <QA q="Какой этап?" a={String(answers.stage || "—")} />
          <QA q="Сколько стоит?" a={showMoney ? money(answers.how_much, String(payments.currency || "USD")) : "Суммы видит менеджер / бухгалтер"} />
          <QA q="Сколько оплачено?" a={showMoney ? money(answers.paid, String(payments.currency || "USD")) : "—"} />
          <QA q="Сколько должны?" a={showMoney ? money(answers.owed, String(payments.currency || "USD")) : "—"} />
          <QA q="Какие документы?" a={String(answers.documents || "—")} />
          <QA q="Что дальше?" a={String(answers.next || "—")} />
          <QA q="Кто отвечает?" a={String(answers.responsible || "—")} />
        </dl>
      </Card>
      <ol className="flex flex-wrap gap-2">
        {pipeline.map((s) => (
          <li key={String(s.id)} className={s.state === "current" ? "rounded bg-[var(--eds-primary)] px-2 py-1 text-white" : "rounded border px-2 py-1"}>
            {String(s.label_ru)}
          </li>
        ))}
      </ol>
      {canCreate ? (
        <div className="flex flex-wrap gap-2">
          <select value={stage} onChange={(e) => setStage(e.target.value)} className="rounded border px-2 py-1">
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <Button size="sm" onClick={() => void post(`/crm/deals/${did}`, { stage })}>
            Сменить этап
          </Button>
          {selected.vehicle_id && selected.client_id ? (
            <Button
              size="sm"
              variant="secondary"
              onClick={() =>
                void post("/crm/reservations", {
                  vehicle_id: selected.vehicle_id,
                  client_id: selected.client_id,
                  deal_id: did,
                  expires_at: "2026-12-31",
                })
              }
            >
              Резерв
            </Button>
          ) : null}
        </div>
      ) : null}
      {selected.vehicle_id ? (
        <Button size="sm" variant="secondary" onClick={() => onOpenVehicle(String(selected.vehicle_id))}>
          Карточка автомобиля
        </Button>
      ) : null}
      {showMoney ? (
        <Card title="Поступления">
          <p>
            Оплачено {money(payments.paid, String(payments.currency || "USD"))} · Остаток {money(payments.outstanding, String(payments.currency || "USD"))}
          </p>
          {canCreate ? (
            <div className="mt-2 flex gap-2">
              <Input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Сумма" />
              <Button
                size="sm"
                onClick={() =>
                  void post("/crm/receipts", {
                    deal_id: did,
                    kind: "PARTIAL",
                    amount,
                    currency: payments.currency || "USD",
                    status: "pending",
                  })
                }
              >
                Записать платёж
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}
      {canFinance && !profit.restricted ? (
        <p className="eds-type-helper">
          Прибыль {money(profit.profit)} · ROI {profit.roi_pct == null ? "—" : `${profit.roi_pct}%`} · маржа {profit.margin_pct == null ? "—" : `${profit.margin_pct}%`}
        </p>
      ) : null}
    </div>
  );
}

function QA({ q, a }: { q: string; a: string }) {
  return (
    <div>
      <dt className="eds-type-caption">{q}</dt>
      <dd>{a}</dd>
    </div>
  );
}

export function VehicleCrmBlock({ crm }: { crm: Rec }) {
  const deal = (crm.deal || null) as Rec | null;
  if (!deal) return <p className="eds-type-helper">{String(crm.message_ru || "Сделка ещё не создана.")}</p>;
  const answers = (deal.answers || {}) as Rec;
  return (
    <div data-testid="auto-vehicle-crm">
      <dl className="grid gap-2 md:grid-cols-2">
        <div>
          <dt className="eds-type-caption">Клиент</dt>
          <dd>{String(answers.client || "—")}</dd>
        </div>
        <div>
          <dt className="eds-type-caption">Этап</dt>
          <dd>{String(answers.stage || "—")}</dd>
        </div>
        <div>
          <dt className="eds-type-caption">Оплачено / должны</dt>
          <dd>
            {money(answers.paid)} / {money(answers.owed)}
          </dd>
        </div>
        <div>
          <dt className="eds-type-caption">Дальше</dt>
          <dd>{String(answers.next || "—")}</dd>
        </div>
      </dl>
    </div>
  );
}

export function AutoReportsDesk({ headers, canFinance }: { headers: Record<string, string>; canFinance: boolean }) {
  const [report, setReport] = useState("funnel");
  const [vin, setVin] = useState("");
  const [data, setData] = useState<Rec>({});

  const load = useCallback(async () => {
    const params = new URLSearchParams({ report, vin });
    const res = await autoOpsGet(`/reports?${params.toString()}`, headers);
    setData((res.json || {}) as Rec);
  }, [headers, report, vin]);

  useEffect(() => {
    void load();
  }, [load]);

  const types = asList(data.types, ["types"]) as Rec[];
  const items = asList(data.items) as Rec[];

  return (
    <div className="space-y-3" data-testid="auto-reports">
      <div className="flex flex-wrap gap-1" data-testid="auto-report-types">
        {(types.length
          ? types
          : [
              { id: "sales", label_ru: "Продажи" },
              { id: "funnel", label_ru: "Воронка продаж" },
              { id: "managers", label_ru: "Работа менеджеров" },
              { id: "in_stock", label_ru: "Автомобили в наличии" },
              { id: "in_transit", label_ru: "Автомобили в пути" },
            ]
        ).map((t) => (
          <Button key={String(t.id)} size="sm" variant={report === t.id ? undefined : "secondary"} onClick={() => setReport(String(t.id))}>
            {String(t.label_ru)}
          </Button>
        ))}
      </div>
      <Input value={vin} onChange={(e) => setVin(e.target.value)} placeholder="Фильтр VIN" />
      <p className="eds-type-helper">{String(data.note_ru || "Отчёт по фактическим записям.")}</p>
      {data.employee_scoring === false || report === "managers" ? (
        <p className="eds-type-caption">Балльной оценки сотрудников нет — только счётчики.</p>
      ) : null}
      {!canFinance && ["sales", "vehicle_profit", "expenses", "receipts", "client_debt"].includes(report) ? (
        <p className="eds-type-helper">Финансовые отчёты видят директор и бухгалтер.</p>
      ) : (
        <ul className="space-y-1">
          {items.length ? (
            items.map((row, i) => (
              <li key={String(row.id || row.vehicle_id || row.manager_id || row.stage || i)}>
                {pick(row, "title", "client_name", "manager_id", "label_ru", "vin", "name") !== "—"
                  ? `${pick(row, "title", "client_name", "manager_id", "label_ru", "vin", "name")}`
                  : pick(row, "stage")}
                {row.count != null ? ` · ${String(row.count)}` : ""}
                {row.outstanding != null ? ` · долг ${money(row.outstanding, String(row.currency || "USD"))}` : ""}
                {row.profit != null ? ` · прибыль ${money(row.profit)}` : ""}
                {row.leads_assigned != null ? ` · лиды ${String(row.leads_assigned)} · продажи ${String(row.completed_sales)} · задачи ${String(row.outstanding_tasks)}` : ""}
              </li>
            ))
          ) : (
            <p className="eds-type-helper">Нет записей для этого отчёта.</p>
          )}
        </ul>
      )}
    </div>
  );
}

export function CrmSettingsPanel({ headers, canCreate }: { headers: Record<string, string>; canCreate: boolean }) {
  return (
    <Card title="Клиенты и продажи">
      <p className="eds-type-helper">Воронка, резерв, поступления. Паспорт и адрес на бэкенде закрыты без роли с PII. Балльной оценки менеджеров нет.</p>
      {canCreate ? (
        <Button size="sm" variant="secondary" onClick={() => void autoOpsPost("/crm/demo", { confirm_demo: true }, headers)}>
          Создать демо-сделку
        </Button>
      ) : null}
    </Card>
  );
}
