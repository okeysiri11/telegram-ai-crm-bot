/**
 * AGRO 1.1 — warehouses, lots, receipt / issue / transfer.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "warehouses", label: "Склады" },
  { id: "balances", label: "Остатки" },
  { id: "receipt", label: "Приход" },
  { id: "issue", label: "Расход" },
  { id: "transfer", label: "Перемещения" },
  { id: "lots", label: "Партии" },
  { id: "inventory", label: "Инвентаризация" },
  { id: "ops", label: "Операции" },
  { id: "documents", label: "Документы" },
  { id: "history", label: "История" },
] as const;

export function AgroWarehousePanel(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  warehouses: Row[];
  lots: Row[];
  operations: Row[];
  counterparties: Row[];
  deals: Row[];
  trips: Row[];
  vehicles: Row[];
  drivers: Row[];
  onChanged: () => void;
  onOpen: (kind: string, id: string) => void;
  onAttach: (kind: string, id: string) => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("overview");
  const [dash, setDash] = useState<{ cards?: Record<string, number>; by_crop?: Row[] }>({});
  const [form, setForm] = useState<Row>({ commodity: "Пшеница", quantity: "100", unit: "т" });
  const [msg, setMsg] = useState("");

  useEffect(() => {
    void agroOpsGet("/warehouses/dashboard", props.headers).then((r) => setDash((r.json || {}) as { cards?: Record<string, number>; by_crop?: Row[] }));
  }, [props.headers, props.warehouses.length, props.lots.length]);

  const cards = dash.cards || {};

  async function saveWarehouse() {
    const res = await agroOpsPost("/entities/warehouse", { name: form.name, warehouse_type: form.warehouse_type || "warehouse", capacity_total: form.capacity_total, city: form.city }, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Склад сохранён" : j.message_ru || "Ошибка");
    if (j.ok) props.onChanged();
  }

  async function operate(type: string) {
    const res = await agroOpsPost("/warehouses/operations", { ...form, type }, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Операция проведена" : j.message_ru || "Ошибка");
    if (j.ok) props.onChanged();
  }

  return (
    <div className="grid gap-3" data-testid="agro-warehouse-panel">
      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {tab === "overview" ? (
        <>
          <div className="grid gap-2 sm:grid-cols-4">
            {[
              ["Общая вместимость", cards.capacity_total],
              ["Занято", cards.occupied],
              ["Свободно", cards.free],
              ["Заполненность %", cards.fill_pct],
            ].map(([label, value]) => (
              <Card key={String(label)} title={String(label)}>
                <div className="text-lg">{value ?? "—"}</div>
              </Card>
            ))}
          </div>
          <ul className="eds-type-small">
            {(dash.by_crop || []).map((c) => (
              <li key={String(c.commodity)}>
                {String(c.commodity)}: {String(c.quantity)} т · закупка {String(c.purchase_value)} · оценка {String(c.market_value ?? "—")}
              </li>
            ))}
          </ul>
        </>
      ) : null}
      {!props.warehouses.length ? (
        <Card title="Склады ещё не добавлены.">
          <div className="flex flex-wrap gap-2">
            {props.canCreate ? <Button size="sm" onClick={() => setTab("warehouses")}>Добавить склад</Button> : null}
            {props.canCreate ? <Button size="sm" variant="ghost" onClick={() => setTab("receipt")}>Оформить приход</Button> : null}
          </div>
        </Card>
      ) : null}
      {tab === "warehouses" ? (
        <>
          <ul className="eds-type-small">
            {props.warehouses.map((w) => (
              <li key={pick(w, "id")} className="flex justify-between border-b border-[var(--ew-border)] py-1">
                <button type="button" className="underline" onClick={() => props.onOpen("warehouse", pick(w, "id"))}>
                  {pick(w, "name")} · {String(w.capacity_total || "—")} т
                </button>
                <Button size="sm" variant="ghost" onClick={() => props.onAttach("warehouse", pick(w, "id"))}>
                  📎
                </Button>
              </li>
            ))}
          </ul>
          {props.canCreate ? (
            <Card title="Добавить склад">
              <div className="grid gap-2 sm:grid-cols-2">
                <Input placeholder="Название" value={String(form.name || "")} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
                <Input placeholder="Вместимость, т" value={String(form.capacity_total || "")} onChange={(e) => setForm((f) => ({ ...f, capacity_total: e.target.value }))} />
                <Input placeholder="Город" value={String(form.city || "")} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} />
                <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.warehouse_type || "warehouse")} onChange={(e) => setForm((f) => ({ ...f, warehouse_type: e.target.value }))}>
                  <option value="warehouse">Склад</option>
                  <option value="elevator">Элеватор</option>
                  <option value="silo">Силос</option>
                  <option value="terminal">Терминал</option>
                </select>
              </div>
              <Button className="mt-2" size="sm" onClick={() => void saveWarehouse()}>
                Сохранить склад
              </Button>
            </Card>
          ) : null}
        </>
      ) : null}
      {tab === "balances" || tab === "inventory" ? (
        <Card title={tab === "balances" ? "Остатки" : "Инвентаризация"}>
          {props.lots.length ? (
            <ul className="eds-type-small">
              {props.lots.map((l) => (
                <li key={pick(l, "id")}>
                  {String(l.commodity)} · {String(l.quantity)} {String(l.unit || "т")} · закупка {String(l.purchase_price ?? "—")}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">Остатки появятся после прихода. Оценка по рынку не меняет учётную цену.</p>
          )}
        </Card>
      ) : null}
      {tab === "documents" ? (
        <Card title="Документы склада">
          {props.warehouses.map((w) => (
            <div key={pick(w, "id")} className="flex justify-between eds-type-small">
              <span>{pick(w, "name")}</span>
              <Button size="sm" variant="ghost" onClick={() => props.onAttach("warehouse", pick(w, "id"))}>📎</Button>
            </div>
          ))}
          {props.lots.map((l) => (
            <div key={pick(l, "id")} className="flex justify-between eds-type-small">
              <span>{pick(l, "name", "lot_number")}</span>
              <Button size="sm" variant="ghost" onClick={() => props.onAttach("inventory_lot", pick(l, "id"))}>📎</Button>
            </div>
          ))}
        </Card>
      ) : null}
      {tab === "history" ? (
        <Card title="История операций">
          {props.operations.length ? (
            <ul className="eds-type-small">
              {props.operations.map((o) => (
                <li key={pick(o, "id")}>{pick(o, "title")} · {String(o.type)} · {String(o.quantity)} · {String(o.date || o.created_at || "").slice(0, 16)}</li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">История появится после прихода или расхода.</p>
          )}
        </Card>
      ) : null}
      {tab === "lots" ? (
        <ul className="eds-type-small" data-testid="agro-lots">
          {props.lots.map((l) => (
            <li key={pick(l, "id")} className="flex justify-between border-b border-[var(--ew-border)] py-1">
              <button type="button" className="underline" onClick={() => props.onOpen("inventory_lot", pick(l, "id"))}>
                {pick(l, "name", "lot_number")} · {String(l.commodity)} · {String(l.quantity)} {String(l.unit || "т")}
              </button>
              <Button size="sm" variant="ghost" onClick={() => props.onAttach("inventory_lot", pick(l, "id"))}>
                📎
              </Button>
            </li>
          ))}
        </ul>
      ) : null}
      {(tab === "ops" || tab === "receipt" || tab === "issue" || tab === "transfer") && props.canCreate ? (
        <Card title={tab === "receipt" ? "Приход" : tab === "issue" ? "Расход" : tab === "transfer" ? "Перемещение" : "Складская операция"}>
          <div className="grid gap-2 sm:grid-cols-2">
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.warehouse_id || "")} onChange={(e) => setForm((f) => ({ ...f, warehouse_id: e.target.value }))}>
              <option value="">Склад</option>
              {props.warehouses.map((w) => (
                <option key={pick(w, "id")} value={pick(w, "id")}>
                  {pick(w, "name")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.lot_id || "")} onChange={(e) => setForm((f) => ({ ...f, lot_id: e.target.value }))}>
              <option value="">Партия (для расхода)</option>
              {props.lots.map((l) => (
                <option key={pick(l, "id")} value={pick(l, "id")}>
                  {pick(l, "name", "lot_number")} ({String(l.quantity)})
                </option>
              ))}
            </select>
            <Input placeholder="Культура" value={String(form.commodity || "")} onChange={(e) => setForm((f) => ({ ...f, commodity: e.target.value }))} />
            <Input placeholder="Количество" value={String(form.quantity || "")} onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.counterparty_id || "")} onChange={(e) => setForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
              <option value="">Контрагент</option>
              {props.counterparties.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.deal_id || "")} onChange={(e) => setForm((f) => ({ ...f, deal_id: e.target.value }))}>
              <option value="">Сделка</option>
              {props.deals.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.trip_id || "")} onChange={(e) => setForm((f) => ({ ...f, trip_id: e.target.value }))}>
              <option value="">Рейс</option>
              {props.trips.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
            <Input placeholder="Цена закупки" value={String(form.purchase_price || "")} onChange={(e) => setForm((f) => ({ ...f, purchase_price: e.target.value }))} />
            {tab === "transfer" ? (
              <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.to_warehouse_id || "")} onChange={(e) => setForm((f) => ({ ...f, to_warehouse_id: e.target.value }))}>
                <option value="">Склад назначения</option>
                {props.warehouses.map((w) => (
                  <option key={pick(w, "id")} value={pick(w, "id")}>
                    {pick(w, "name")}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {tab === "issue" ? (
              <Button size="sm" onClick={() => void operate("ISSUE")}>Расход</Button>
            ) : tab === "transfer" ? (
              <Button size="sm" onClick={() => void operate("TRANSFER")}>Переместить</Button>
            ) : (
              <Button size="sm" onClick={() => void operate("RECEIPT")}>Приход</Button>
            )}
            {tab === "ops" ? (
              <>
                <Button size="sm" variant="ghost" onClick={() => void operate("ISSUE")}>Расход</Button>
                <Button size="sm" variant="ghost" onClick={() => void operate("TRANSFER")}>Перемещение</Button>
              </>
            ) : null}
          </div>
        </Card>
      ) : null}
      {tab === "ops" ? (
        <ul className="eds-type-small">
          {props.operations.map((o) => (
            <li key={pick(o, "id")}>
              {pick(o, "title")} · {String(o.type)} · {String(o.quantity)}
            </li>
          ))}
        </ul>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
