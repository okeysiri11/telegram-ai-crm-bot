/**
 * AGRO 2.2 Operation 360 — desktop sections vs compact mobile cards. Same /operations/{id} API.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet, agroOpsPost, agroOpsUpload } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

const DESKTOP_TABS = [
  { id: "overview", label: "Overview" },
  { id: "deals", label: "Purchase" },
  { id: "trucks", label: "Logistics" },
  { id: "weighings", label: "Weighing" },
  { id: "quality", label: "Quality" },
  { id: "lots", label: "Warehouse" },
  { id: "sales", label: "Sales" },
  { id: "payments", label: "Payments" },
  { id: "documents", label: "Documents" },
  { id: "expenses", label: "Expenses" },
  { id: "tasks", label: "Tasks" },
  { id: "activity", label: "Timeline" },
] as const;

const MOBILE_SECTIONS = [
  { id: "trucks", label: "Логистика" },
  { id: "weighings", label: "Вес" },
  { id: "quality", label: "Качество" },
  { id: "lots", label: "Склад" },
  { id: "sales", label: "Продажи" },
  { id: "payments", label: "Деньги" },
  { id: "documents", label: "Документы" },
  { id: "expenses", label: "Ещё" },
] as const;

const TRUCK_ACTIONS: { id: string; label: string; next: string }[] = [
  { id: "loading", label: "Загрузка", next: "loading" },
  { id: "loaded", label: "Выехал", next: "in_transit" },
  { id: "unloading", label: "Прибыл", next: "unloading" },
  { id: "unloaded", label: "Выгрузка", next: "unloaded" },
  { id: "problem", label: "Проблема", next: "problem" },
];

function n(v: unknown): string {
  if (v === null || v === undefined || v === "") return "Нет данных";
  return String(v);
}

function titleOf(r: Row): string {
  return String(r.number || r.lot_number || r.title || r.filename || r.plate || r.summary || r.id || "—");
}

export function AgroOperation360(props: {
  itemId: string;
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  canOperate: boolean;
  initialTab?: string;
  onBack: () => void;
  onQuick: (kind: string) => void;
  onChanged: () => void;
}) {
  const mobile = useIsMobile();
  const [tab, setTab] = useState(props.initialTab || "overview");
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gross, setGross] = useState("");
  const [tare, setTare] = useState("");
  const [scale, setScale] = useState("receiving");
  const [moisture, setMoisture] = useState("");
  const [protein, setProtein] = useState("");
  const [expAmt, setExpAmt] = useState("");
  const [expCat, setExpCat] = useState("transport");
  const [saleQty, setSaleQty] = useState("");
  const [salePrice, setSalePrice] = useState("");
  const [plate, setPlate] = useState("");
  const [driver, setDriver] = useState("");
  const [phone, setPhone] = useState("");

  async function reload() {
    const t = tab === "sales" ? "deals" : tab;
    const res = await agroOpsGet(`/operations/${props.itemId}?tab=${t}&limit=50`, props.headers);
    if (!res.ok) {
      setError((res.json as { message_ru?: string }).message_ru || "Не удалось загрузить операцию");
      return;
    }
    setData(res.json as Row);
    setError(null);
  }

  useEffect(() => {
    if (props.initialTab) setTab(props.initialTab);
  }, [props.initialTab]);

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.itemId, tab, props.headers]);

  const item = (data?.item || {}) as Row;
  const pnl = (data?.pnl || {}) as Row;
  const cost = (data?.cost_basis || {}) as Row;
  const plan = (data?.plan_vs_actual || {}) as Row;
  const rows = ((data?.items as Row[]) || []).filter((r) => (tab !== "sales" ? true : String(r.side) === "sell"));
  const allowed = (item.allowed_statuses as string[]) || [];

  async function post(path: string, body: Record<string, unknown>) {
    const res = await agroOpsPost(path, body, props.headers);
    const j = res.json as { message_ru?: string };
    if (!res.ok) {
      setError(j.message_ru || "Ошибка");
      return;
    }
    props.onChanged();
    await reload();
  }

  const headerCards = [
    { id: "planned", label: "Закуплено", value: item.planned_qty },
    { id: "received", label: "Принято", value: item.received_qty },
    { id: "stock", label: "На складе", value: item.remaining_qty },
    { id: "sold", label: "Продано", value: item.sold_qty },
    { id: "remain", label: "Остаток", value: item.remaining_qty },
  ];

  return (
    <div className="space-y-3 overflow-x-hidden" data-testid="agro-operation-360">
      <header>
        <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={props.onBack} aria-label="Назад">
          ←
        </Button>
        <h3 className="font-semibold" data-testid="agro-op-number">
          {n(item.number)}
        </h3>
        <p className="eds-type-small">
          {n(item.crop)} · {n(item.status_ru)} · {n(item.supplier)}
        </p>
      </header>

      <div className={mobile ? "grid grid-cols-2 gap-2" : "grid gap-2 sm:grid-cols-5"} data-testid="agro-op-kpis">
        {headerCards.map((c) => (
          <Card key={c.id} title={c.label}>
            <p className="text-lg font-semibold">{n(c.value)}</p>
          </Card>
        ))}
      </div>

      {props.canFinance ? (
        <p className="eds-type-small" data-testid="agro-op-money">
          Закупка: {n(item.purchase_value)} · Продажи: {n(item.sales_value)} · Расходы: {n(item.actual_expenses)}
          {pnl.calculable ? ` · P&L ${n(pnl.gross_profit)} (${n(pnl.margin_pct)}%)` : pnl.message_ru ? ` · ${String(pnl.message_ru)}` : ""}
        </p>
      ) : null}

      {mobile ? (
        <div className="grid grid-cols-2 gap-2" data-testid="agro-op-mobile-nav">
          {MOBILE_SECTIONS.map((s) => (
            <Button key={s.id} size="sm" className="min-h-11" variant={tab === s.id ? "primary" : "secondary"} onClick={() => setTab(s.id)}>
              {s.label}
            </Button>
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-1" data-testid="agro-op-tabs">
          {DESKTOP_TABS.map((t) => (
            <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
              {t.label}
            </Button>
          ))}
        </div>
      )}

      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}

      {props.canOperate && allowed.length ? (
        <div className="flex flex-wrap gap-1">
          {allowed.map((st) => (
            <Button key={st} size="sm" variant="ghost" className="min-h-11" onClick={() => void post(`/operations/${props.itemId}/status`, { status: st, source: "USER" })}>
              {st}
            </Button>
          ))}
        </div>
      ) : null}

      {tab === "overview" && !mobile ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <Card title="PLAN | ACTUAL">
            {(["quantity", "purchase_price", "logistics", "profit"] as const).map((k) => {
              const row = (plan[k] || {}) as Row;
              return (
                <p key={k} className="eds-type-small">
                  {k}: план {n(row.plan)} · факт {n(row.actual)}
                </p>
              );
            })}
          </Card>
          <Card title="Себестоимость">
            {cost.masked ? <p className="eds-type-small">Нет доступа</p> : null}
            {cost.cost_missing ? <p className="eds-type-small">Нет данных</p> : <p className="eds-type-small">Итого: {n(cost.total_cost)}</p>}
            {pnl.message_ru && !pnl.calculable ? <p className="eds-type-small">{String(pnl.message_ru)}</p> : null}
          </Card>
        </div>
      ) : null}

      {tab === "trucks" || tab === "logistics" ? (
        <section data-testid="agro-op-trucks">
          {props.canCreate ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-3">
              <Input placeholder="Госномер" value={plate} onChange={(e) => setPlate(e.target.value)} className="min-h-11" />
              <Input placeholder="Водитель" value={driver} onChange={(e) => setDriver(e.target.value)} className="min-h-11" />
              <Input placeholder="Телефон" value={phone} onChange={(e) => setPhone(e.target.value)} className="min-h-11" />
              <Button size="sm" className="min-h-11" onClick={() => void post(`/operations/${props.itemId}/truck`, { plate, driver_name: driver, driver_phone: phone })}>
                Добавить машину
              </Button>
            </div>
          ) : null}
          {(tab === "trucks" ? rows : ((data as Row | null)?.items as Row[]) || []).map((t) => (
            <Card key={String(t.id)} title={`Машина: ${n(t.plate)}`}>
              <p className="eds-type-small">Прицеп: {n(t.trailer_plate)}</p>
              <p className="eds-type-small">Водитель: {n(t.driver_name)}</p>
              <p className="eds-type-small">
                Маршрут: {n(t.load_place)} → {n(t.dest_place)}
              </p>
              <p className="eds-type-small">Cargo: {n(t.crop || item.crop)}</p>
              <p className="eds-type-small">Planned: {n(t.planned_weight)} t</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {t.driver_phone ? (
                  <a className="min-h-11 inline-flex items-center rounded-md border border-[var(--ew-border)] px-3" href={`tel:${String(t.driver_phone)}`}>
                    Позвонить
                  </a>
                ) : null}
                {t.load_place || t.dest_place ? (
                  <a
                    className="min-h-11 inline-flex items-center rounded-md border border-[var(--ew-border)] px-3"
                    href={`https://maps.google.com/?q=${encodeURIComponent(String(t.dest_place || t.load_place))}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Открыть маршрут
                  </a>
                ) : null}
                {props.canOperate
                  ? TRUCK_ACTIONS.map((a) => (
                      <Button key={a.id} size="sm" className="min-h-11" variant="secondary" onClick={() => void post(`/operations/truck/${t.id}/status`, { status: a.next })}>
                        {a.label}
                      </Button>
                    ))
                  : null}
                <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onQuick("documents")}>
                  Добавить документ
                </Button>
              </div>
            </Card>
          ))}
          {!rows.length && tab === "trucks" ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}

      {tab === "weighings" ? (
        <section data-testid="agro-op-weighing">
          {props.canCreate ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-4">
              <Input placeholder="Брутто" value={gross} onChange={(e) => setGross(e.target.value)} className="min-h-11" />
              <Input placeholder="Тара" value={tare} onChange={(e) => setTare(e.target.value)} className="min-h-11" />
              <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2" value={scale} onChange={(e) => setScale(e.target.value)}>
                <option value="loading">Погрузка</option>
                <option value="receiving">Приёмка</option>
              </select>
              <Button size="sm" className="min-h-11" onClick={() => void post(`/operations/${props.itemId}/weighing`, { gross, tare, scale, unit: "кг" })}>
                Добавить взвешивание
              </Button>
            </div>
          ) : null}
          {rows.map((w) => (
            <p key={String(w.id)} className="eds-type-small border-b border-[var(--ew-border)] py-2">
              {n(w.scale)} · брутто {n(w.gross)} · тара {n(w.tare)} · нетто {n(w.net)}
            </p>
          ))}
          {!rows.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}

      {tab === "quality" ? (
        <section data-testid="agro-op-quality">
          {props.canCreate ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-3">
              <Input placeholder="Влажность %" value={moisture} onChange={(e) => setMoisture(e.target.value)} className="min-h-11" />
              <Input placeholder="Белок %" value={protein} onChange={(e) => setProtein(e.target.value)} className="min-h-11" />
              <Button size="sm" className="min-h-11" onClick={() => void post(`/operations/${props.itemId}/quality`, { moisture, protein })}>
                Добавить анализ
              </Button>
            </div>
          ) : null}
          {rows.map((q) => (
            <p key={String(q.id)} className="eds-type-small border-b border-[var(--ew-border)] py-2">
              {titleOf(q)} · {n(q.result)} · {n(q.decision)}
            </p>
          ))}
          {!rows.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}

      {tab === "lots" ? (
        <section data-testid="agro-op-warehouse">
          {props.canCreate ? (
            <Button size="sm" className="mb-2 min-h-11" onClick={() => void post(`/operations/${props.itemId}/receive`, {})}>
              Приход на склад (факт)
            </Button>
          ) : null}
          {rows.map((l) => (
            <p key={String(l.id)} className="eds-type-small border-b border-[var(--ew-border)] py-2">
              {n(l.lot_number)} · {n(l.commodity || l.crop)} · {n(l.quantity)}
            </p>
          ))}
          {!rows.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}

      {tab === "sales" || tab === "deals" ? (
        <section data-testid="agro-op-sales">
          {tab === "sales" && props.canCreate ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-3">
              <Input placeholder="Количество, т" value={saleQty} onChange={(e) => setSaleQty(e.target.value)} className="min-h-11" />
              <Input placeholder="Цена" value={salePrice} onChange={(e) => setSalePrice(e.target.value)} className="min-h-11" />
              <Button
                size="sm"
                className="min-h-11"
                onClick={() => {
                  const lots = ((data as Row).counts_lots != null ? [] : []) as Row[];
                  void (async () => {
                    const full = await agroOpsGet(`/operations/${props.itemId}?tab=lots`, props.headers);
                    const lotRows = ((full.json as Row).items as Row[]) || [];
                    const lot = lotRows[0];
                    if (!lot) {
                      setError("Нет партии для отгрузки");
                      return;
                    }
                    await post(`/operations/${props.itemId}/sale`, {
                      price: salePrice,
                      ship: true,
                      allocations: [{ lot_id: lot.id, quantity: Number(saleQty) }],
                    });
                  })();
                }}
              >
                Создать продажу
              </Button>
            </div>
          ) : null}
          {rows.map((d) => (
            <p key={String(d.id)} className="eds-type-small border-b border-[var(--ew-border)] py-2">
              {titleOf(d)} · {n(d.side)} · {n(d.quantity)} · {n(d.price)} · {n(d.operation_number || item.number)}
            </p>
          ))}
          {!rows.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}

      {tab === "payments" || tab === "expenses" || tab === "documents" || tab === "tasks" || tab === "activity" ? (
        <section>
          {tab === "expenses" && props.canFinance ? (
            <div className="mb-2 grid gap-2 sm:grid-cols-3">
              <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2" value={expCat} onChange={(e) => setExpCat(e.target.value)}>
                {["transport", "loading", "unloading", "storage", "drying", "cleaning", "lab", "broker", "commission", "customs", "documents", "insurance", "other"].map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <Input placeholder="Сумма" value={expAmt} onChange={(e) => setExpAmt(e.target.value)} className="min-h-11" />
              <Button size="sm" className="min-h-11" onClick={() => void post(`/operations/${props.itemId}/expense`, { amount: expAmt, category: expCat })}>
                Добавить расход
              </Button>
            </div>
          ) : null}
          {tab === "documents" ? (
            <label className="eds-type-small mb-2 block">
              Камера / галерея / файл
              <input
                type="file"
                accept="image/*,.pdf,.heic,.heif,.jpg,.jpeg,.png"
                capture="environment"
                className="mt-1 block min-h-11"
                data-testid="agro-op-camera"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const res = await agroOpsUpload("/files", file, { entity_type: "agro_operation", entity_id: props.itemId, doc_type: "photo" }, props.headers);
                  setError(res.ok ? null : "Не удалось прикрепить файл");
                  if (res.ok) await reload();
                }}
              />
            </label>
          ) : null}
          {rows.map((r) => (
            <p key={String(r.id)} className="eds-type-small border-b border-[var(--ew-border)] py-2">
              {titleOf(r)}
            </p>
          ))}
          {!rows.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        </section>
      ) : null}
    </div>
  );
}

export const OPERATION_QUICK_ACTIONS = [
  { id: "weighing", label: "Добавить взвешивание" },
  { id: "quality", label: "Добавить анализ качества" },
  { id: "expense", label: "Добавить расход" },
  { id: "documents", label: "Добавить документ" },
  { id: "truck", label: "Добавить машину" },
  { id: "task", label: "Создать задачу" },
  { id: "sale", label: "Создать продажу" },
];
