/**
 * AGRO 1.1 — operational logistics: carriers, fleet, trips.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";
import { ruStatus } from "./agroLabels";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор" },
  { id: "carrier", label: "Перевозчики" },
  { id: "vehicle", label: "Автомобили" },
  { id: "trailer", label: "Прицепы" },
  { id: "driver", label: "Водители" },
  { id: "trip", label: "Рейсы" },
  { id: "routes", label: "Маршруты" },
  { id: "documents", label: "Документы" },
  { id: "expenses", label: "Расходы" },
  { id: "history", label: "История" },
] as const;

export function AgroLogisticsPanel(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  counterparties: Row[];
  vehicles: Row[];
  carriers: Row[];
  trailers: Row[];
  drivers: Row[];
  trips: Row[];
  shipments: Row[];
  deals: Row[];
  warehouses: Row[];
  onChanged: () => void;
  onOpen: (kind: string, id: string) => void;
  onAttach: (kind: string, id: string) => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("overview");
  const [dash, setDash] = useState<Row>({});
  const [form, setForm] = useState<Row>({});
  const [msg, setMsg] = useState("");

  useEffect(() => {
    void agroOpsGet("/logistics/dashboard", props.headers).then((r) => {
      setDash((r.json as { cards?: Row }) || {});
    });
  }, [props.headers, props.trips.length, props.vehicles.length]);

  const cards = (dash.cards || {}) as Record<string, number>;

  async function save(kind: string, body: Row) {
    const res = await agroOpsPost(`/entities/${kind}`, body, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Сохранено" : j.message_ru || "Ошибка");
    if (j.ok) {
      setForm({});
      props.onChanged();
    }
  }

  const rows: Record<string, Row[]> = {
    carrier: props.carriers,
    vehicle: props.vehicles,
    trailer: props.trailers,
    driver: props.drivers,
    trip: props.trips,
  };

  return (
    <div className="grid gap-3" data-testid="agro-logistics-panel">
      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {tab === "overview" && !props.carriers.length && !props.vehicles.length && !props.trips.length ? (
        <Card title="Транспорт ещё не добавлен.">
          <p className="eds-type-small mb-2">Добавьте перевозчика, автомобиль и рейс — записи не выдумываются.</p>
          {props.canCreate ? (
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => setTab("carrier")}>
                Добавить перевозчика
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setTab("vehicle")}>
                Добавить автомобиль
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setTab("trip")}>
                Создать рейс
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}
      {tab === "overview" ? (
        <div className="grid gap-2 sm:grid-cols-4" data-testid="agro-logistics-cards">
          {[
            ["Активные рейсы", cards.active_trips],
            ["Машины в рейсе", cards.vehicles_in_trip],
            ["Свободные машины", cards.free_vehicles],
            ["Сегодня погрузок", cards.loadings_today],
            ["Сегодня выгрузок", cards.unloadings_today],
            ["Просроченные доставки", cards.overdue_deliveries],
            ["Стоимость логистики сегодня", cards.logistics_cost_today],
            ["Стоимость логистики за месяц", cards.logistics_cost_month],
            ["Коммерческие ставки (ручные)", cards.freight_quotes],
          ].map(([label, value]) => (
            <Card key={String(label)} title={String(label)}>
              <div className="text-lg">{value ?? 0}</div>
            </Card>
          ))}
        </div>
      ) : null}
      {tab === "overview" && Array.isArray(dash.commercial_quotes) && (dash.commercial_quotes as Row[]).length ? (
        <Card title="Ручные ставки фрахта">
          <ul className="eds-type-small" data-testid="agro-logistics-quotes">
            {(dash.commercial_quotes as Row[]).map((q) => (
              <li key={pick(q, "id")}>
                {pick(q, "title", "name")} · {String(q.rate ?? q.tariff ?? "—")} {String(q.currency || "")} · {String(q.manual_status || "CONFIRMED")}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
      {tab !== "overview" && ["carrier", "vehicle", "trailer", "driver", "trip"].includes(tab) && !rows[tab]?.length ? (
        <Card title="Транспорт ещё не добавлен.">
          <p className="eds-type-small mb-2">Добавьте перевозчика, автомобиль и рейс — записи не выдумываются.</p>
          {props.canCreate ? (
            <div className="flex flex-wrap gap-2">
              <Button size="sm" onClick={() => setTab("carrier")}>
                Добавить перевозчика
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setTab("vehicle")}>
                Добавить автомобиль
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setTab("trip")}>
                Создать рейс
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}
      {tab === "routes" ? (
        <Card title="Маршруты">
          {props.trips.length ? (
            <ul className="eds-type-small">
              {props.trips.map((t) => (
                <li key={pick(t, "id")} className="border-b border-[var(--ew-border)] py-1">
                  <button type="button" className="underline" onClick={() => props.onOpen("trip", pick(t, "id"))}>
                    {pick(t, "title")} · {String(t.origin || "—")} → {String(t.destination || "—")}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">Маршруты появятся после создания рейсов. Точки не выдумываются.</p>
          )}
        </Card>
      ) : null}
      {tab === "documents" ? (
        <Card title="Документы транспорта">
          <p className="eds-type-small mb-2">📎 техпаспорт, страховка, ТТН, CMR — в карточке объекта. Чувствительные документы водителя видит только директор.</p>
          {([
            ["vehicle", props.vehicles],
            ["trailer", props.trailers],
            ["driver", props.drivers],
            ["trip", props.trips],
          ] as const).flatMap(([kind, list]) =>
            list.map((r) => (
              <div key={`${kind}-${pick(r, "id")}`} className="flex justify-between border-b border-[var(--ew-border)] py-1 eds-type-small">
                <span>{pick(r, "name", "title", "full_name", "plate")}</span>
                <Button size="sm" variant="ghost" onClick={() => props.onAttach(kind, pick(r, "id"))}>
                  📎
                </Button>
              </div>
            )),
          )}
        </Card>
      ) : null}
      {tab === "expenses" ? (
        <Card title="Расходы">
          {props.trips.length ? (
            <ul className="eds-type-small">
              {props.trips.map((t) => (
                <li key={pick(t, "id")}>
                  {pick(t, "title")}: ставка {String(t.rate ?? "—")} · топливо {String(t.fuel_cost ?? "—")} · всего {String(t.total_logistics_cost ?? "—")}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">Расходы считаются из рейсов. Суммы не выдумываются.</p>
          )}
        </Card>
      ) : null}
      {tab === "history" ? (
        <Card title="История рейсов">
          {props.trips.length ? (
            <ul className="eds-type-small">
              {props.trips.map((t) => (
                <li key={pick(t, "id")}>
                  {pick(t, "title")} · {ruStatus(pick(t, "status"))} · {String(t.updated_at || t.created_at || "").slice(0, 16)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">История появится после рейсов.</p>
          )}
        </Card>
      ) : null}
      {tab !== "overview" && rows[tab]?.length ? (
        <ul className="eds-type-small" data-testid={`agro-logistics-${tab}`}>
          {rows[tab].map((r) => (
            <li key={pick(r, "id")} className="flex items-center justify-between gap-2 border-b border-[var(--ew-border)] py-1">
              <button type="button" className="text-left underline" onClick={() => props.onOpen(tab, pick(r, "id"))}>
                {pick(r, "name", "title", "full_name", "plate")} · {ruStatus(pick(r, "status"))}
              </button>
              <Button size="sm" variant="ghost" onClick={() => props.onAttach(tab, pick(r, "id"))}>
                📎
              </Button>
            </li>
          ))}
        </ul>
      ) : null}
      {props.canCreate && tab === "carrier" ? (
        <Card title="Новый перевозчик">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Название" value={String(form.name || "")} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            <Input placeholder="ЕДРПОУ" value={String(form.edrpou || "")} onChange={(e) => setForm((f) => ({ ...f, edrpou: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.carrier_type || "carrier")} onChange={(e) => setForm((f) => ({ ...f, carrier_type: e.target.value }))}>
              <option value="own">Собственный транспорт</option>
              <option value="contractor">Подрядчик</option>
              <option value="carrier">Перевозчик</option>
              <option value="forwarder">Экспедитор</option>
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.counterparty_id || "")} onChange={(e) => setForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
              <option value="">Связать с контрагентом</option>
              {props.counterparties.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <Button className="mt-2" size="sm" onClick={() => void save("carrier", form)}>
            Сохранить
          </Button>
        </Card>
      ) : null}
      {props.canCreate && tab === "vehicle" ? (
        <Card title="Новый автомобиль">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Госномер" value={String(form.plate || "")} onChange={(e) => setForm((f) => ({ ...f, plate: e.target.value, name: e.target.value }))} />
            <Input placeholder="Марка" value={String(form.brand || "")} onChange={(e) => setForm((f) => ({ ...f, brand: e.target.value }))} />
            <Input placeholder="Модель" value={String(form.model || "")} onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))} />
            <Input placeholder="Грузоподъёмность, т" value={String(form.capacity || "")} onChange={(e) => setForm((f) => ({ ...f, capacity: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.carrier_id || "")} onChange={(e) => setForm((f) => ({ ...f, carrier_id: e.target.value }))}>
              <option value="">Перевозчик</option>
              {props.carriers.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <Button className="mt-2" size="sm" onClick={() => void save("vehicle", form)}>
            Сохранить
          </Button>
        </Card>
      ) : null}
      {props.canCreate && tab === "trailer" ? (
        <Card title="Новый прицеп">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Номер прицепа" value={String(form.plate || "")} onChange={(e) => setForm((f) => ({ ...f, plate: e.target.value, name: e.target.value }))} />
            <Input placeholder="Тип / вместимость" value={String(form.capacity || "")} onChange={(e) => setForm((f) => ({ ...f, capacity: e.target.value }))} />
          </div>
          <Button className="mt-2" size="sm" onClick={() => void save("trailer", form)}>
            Сохранить
          </Button>
        </Card>
      ) : null}
      {props.canCreate && tab === "driver" ? (
        <Card title="Новый водитель">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="ФИО" value={String(form.full_name || "")} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
            <Input placeholder="Телефон" value={String(form.phone || "")} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
            <Input placeholder="Водительское удостоверение" value={String(form.license_number || "")} onChange={(e) => setForm((f) => ({ ...f, license_number: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.carrier_id || "")} onChange={(e) => setForm((f) => ({ ...f, carrier_id: e.target.value }))}>
              <option value="">Перевозчик</option>
              {props.carriers.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <Button className="mt-2" size="sm" onClick={() => void save("driver", form)}>
            Сохранить
          </Button>
        </Card>
      ) : null}
      {props.canCreate && tab === "trip" ? (
        <Card title="Новый рейс">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Номер рейса" value={String(form.title || "")} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value, trip_number: e.target.value }))} />
            <Input placeholder="Культура" value={String(form.crop || "Пшеница")} onChange={(e) => setForm((f) => ({ ...f, crop: e.target.value, cargo: e.target.value }))} />
            <Input placeholder="Вес план, т" value={String(form.weight_planned || "")} onChange={(e) => setForm((f) => ({ ...f, weight_planned: e.target.value }))} />
            <Input placeholder="Ставка" value={String(form.rate || "")} onChange={(e) => setForm((f) => ({ ...f, rate: e.target.value }))} />
            <Input placeholder="Откуда" value={String(form.origin || "")} onChange={(e) => setForm((f) => ({ ...f, origin: e.target.value }))} />
            <Input placeholder="Куда" value={String(form.destination || "")} onChange={(e) => setForm((f) => ({ ...f, destination: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.vehicle_id || "")} onChange={(e) => setForm((f) => ({ ...f, vehicle_id: e.target.value }))}>
              <option value="">Автомобиль</option>
              {props.vehicles.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name", "plate")}
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
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.shipment_id || "")} onChange={(e) => setForm((f) => ({ ...f, shipment_id: e.target.value }))}>
              <option value="">Поставка</option>
              {props.shipments.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.warehouse_id || "")} onChange={(e) => setForm((f) => ({ ...f, warehouse_id: e.target.value }))}>
              <option value="">Склад</option>
              {props.warehouses.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <Button className="mt-2" size="sm" onClick={() => void save("trip", form)}>
            Сохранить
          </Button>
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
